"""REST API for comments on works."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Comment, Work
from app.routers.auth import get_current_user
from app.schemas.comment import CommentCreate, CommentResponse

router = APIRouter(prefix="/api/works/{work_id}/comments", tags=["comments"])

def get_visible_work(work_id: int, db: Session):
    work = db.get(Work, work_id)
    if work is None or work.is_hidden:
        raise HTTPException(status_code=404, detail="Work not found")
    return work

@router.get("", response_model=list[CommentResponse])
def list_comments(work_id: int, db: Session = Depends(get_db)):
    get_visible_work(work_id, db)
    return db.scalars(
        select(Comment).where(
            Comment.work_id == work_id,
            Comment.is_hidden.is_(False),
        ).order_by(Comment.created_at.asc())
    ).all()

@router.post("", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(work_id: int, payload: CommentCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    get_visible_work(work_id, db)
    now = datetime.now(timezone.utc)
    comment = Comment(
        user_id=current_user.id,
        work_id=work_id,
        content=payload.content.strip(),
        is_hidden=False,
        created_at=now,
        updated_at=now,
    )
    if not comment.content:
        raise HTTPException(status_code=422, detail="Comment cannot be empty")
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment

@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    comment = db.get(Comment, comment_id)
    if comment is None or comment.is_hidden:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    db.delete(comment)
    db.commit()
