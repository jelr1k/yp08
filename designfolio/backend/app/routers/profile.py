"""Authenticated profile and personal catalog endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Like, Work
from app.routers.auth import get_current_user
from app.schemas.work import WorkResponse

router=APIRouter(prefix="/api/me",tags=["profile"])

@router.get("/works",response_model=list[WorkResponse])
def my_works(current_user=Depends(get_current_user),db:Session=Depends(get_db)):
    return db.scalars(select(Work).where(Work.author_id==current_user.id).order_by(Work.created_at.desc())).all()

@router.get("/favorites",response_model=list[WorkResponse])
def my_favorites(current_user=Depends(get_current_user),db:Session=Depends(get_db)):
    return db.scalars(select(Work).join(Like,Like.work_id==Work.id).where(Like.user_id==current_user.id,Work.is_hidden.is_(False)).order_by(Like.created_at.desc())).all()
