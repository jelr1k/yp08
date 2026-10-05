"""REST API for work image uploads."""
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Work, WorkImage
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/works/{work_id}/images", tags=["images"])
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
ALLOWED = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}
MAX_SIZE = 8 * 1024 * 1024

@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_image(work_id: int, file: UploadFile = File(...), current_user=Depends(get_current_user), db: Session = Depends(get_db)):
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
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{ALLOWED[file.content_type]}"
    path = UPLOAD_DIR / filename
    path.write_bytes(data)
    url = f"/uploads/{filename}"
    image = WorkImage(work_id=work_id, image_url=url, sort_order=0, created_at=datetime.now(timezone.utc))
    db.add(image)
    work.cover_url = url
    work.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(image)
    return {"id": image.id, "image_url": image.image_url, "cover_url": work.cover_url}

@router.get("")
def list_images(work_id: int, db: Session = Depends(get_db)):
    work = db.get(Work, work_id)
    if work is None or work.is_hidden:
        raise HTTPException(status_code=404, detail="Work not found")
    return db.query(WorkImage).filter(WorkImage.work_id == work_id).order_by(WorkImage.sort_order).all()
