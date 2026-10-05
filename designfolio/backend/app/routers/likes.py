"""REST API for work likes."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Like, Work
from app.routers.auth import get_current_user
from app.schemas.like import LikeResponse

router = APIRouter(prefix="/api/works/{work_id}/like", tags=["likes"])

def get_visible_work(work_id: int, db: Session):
    work = db.get(Work, work_id)
    if work is None or work.is_hidden:
        raise HTTPException(status_code=404, detail="Work not found")
    return work

def response_for(work_id: int, user_id: int, db: Session):
    liked = db.get(Like, {"user_id": user_id, "work_id": work_id})
    count = db.scalar(select(func.count()).select_from(Like).where(Like.work_id == work_id)) or 0
    return LikeResponse(liked=liked is not None, likes_count=count, created_at=liked.created_at if liked else None)

@router.get("", response_model=LikeResponse)
def get_like(work_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    get_visible_work(work_id, db)
    return response_for(work_id, current_user.id, db)

@router.post("", response_model=LikeResponse)
def add_like(work_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    get_visible_work(work_id, db)
    if db.get(Like, {"user_id": current_user.id, "work_id": work_id}) is None:
        db.add(Like(user_id=current_user.id, work_id=work_id, created_at=datetime.now(timezone.utc)))
        db.commit()
    return response_for(work_id, current_user.id, db)

@router.delete("", response_model=LikeResponse)
def remove_like(work_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    get_visible_work(work_id, db)
    db.execute(delete(Like).where(Like.user_id == current_user.id, Like.work_id == work_id))
    db.commit()
    return response_for(work_id, current_user.id, db)
