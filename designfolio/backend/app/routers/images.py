"""REST API for work image uploads to Supabase Storage."""
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Work, WorkImage
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/works/{work_id}/images", tags=["images"])

BUCKET = "work-images"
ALLOWED = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
MAX_SIZE = 8 * 1024 * 1024


def upload_to_supabase(filename: str, data: bytes, content_type: str) -> str:
    if not settings.supabase_url or not settings.supabase_secret_key:
        raise HTTPException(
            status_code=503,
            detail="Supabase Storage is not configured on the server",
        )

    path = quote(filename, safe="/")
    url = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{BUCKET}/{path}"
    request = Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {settings.supabase_secret_key}",
            "apikey": settings.supabase_secret_key,
            "Content-Type": content_type,
            "Cache-Control": "3600",
            "x-upsert": "false",
        },
    )

    try:
        with urlopen(request, timeout=30) as response:
            if response.status not in (200, 201):
                raise HTTPException(
                    status_code=502,
                    detail="Supabase Storage returned an unexpected status",
                )
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise HTTPException(
            status_code=502,
            detail=f"Supabase Storage upload failed: {detail}",
        ) from exc
    except URLError as exc:
        raise HTTPException(
            status_code=502,
            detail="Supabase Storage is unreachable",
        ) from exc

    return f"{settings.supabase_url.rstrip('/')}/storage/v1/object/public/{BUCKET}/{path}"


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_image(
    work_id: int,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    work = db.get(Work, work_id)
    if work is None or work.is_hidden:
        raise HTTPException(status_code=404, detail="Work not found")
    if work.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if file.content_type not in ALLOWED:
        raise HTTPException(status_code=400, detail="Unsupported image type")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="Image is too large (max 8 MB)")

    filename = f"works/{work_id}/{uuid4().hex}{ALLOWED[file.content_type]}"
    public_url = upload_to_supabase(filename, data, file.content_type)

    image = WorkImage(
        work_id=work_id,
        image_url=public_url,
        sort_order=0,
        created_at=datetime.now(timezone.utc),
    )
    db.add(image)
    work.cover_url = public_url
    work.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(image)

    return {
        "id": image.id,
        "image_url": image.image_url,
        "cover_url": work.cover_url,
    }


@router.get("")
def list_images(work_id: int, db: Session = Depends(get_db)):
    work = db.get(Work, work_id)
    if work is None or work.is_hidden:
        raise HTTPException(status_code=404, detail="Work not found")

    return (
        db.query(WorkImage)
        .filter(WorkImage.work_id == work_id)
        .order_by(WorkImage.sort_order)
        .all()
    )
