"""REST API for DesignFolio works."""
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Category, Work
from app.routers.auth import get_current_user
from app.schemas.work import WorkCreate, WorkListResponse, WorkResponse, WorkUpdate

router = APIRouter(prefix="/api/works", tags=["works"])


def get_work_or_404(work_id: int, db: Session) -> Work:
    work = db.get(Work, work_id)
    if work is None or work.is_hidden:
        raise HTTPException(status_code=404, detail="Work not found")
    return work


@router.get("", response_model=WorkListResponse)
def list_works(
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
    category_id: int | None = Query(None, ge=1),
    sort: str = Query("newest", pattern="^(newest|oldest)$"),
    db: Session = Depends(get_db),
):
    query = select(Work).where(Work.is_hidden.is_(False))

    if search:
        term = f"%{search.strip()}%"
        query = query.where(or_(Work.title.ilike(term), Work.description.ilike(term)))

    if category_id is not None:
        query = query.where(Work.category_id == category_id)

    if sort == "oldest":
        query = query.order_by(Work.created_at.asc())
    else:
        query = query.order_by(Work.created_at.desc())

    total = db.scalar(
        select(func.count()).select_from(query.order_by(None).subquery())
    ) or 0
    items = db.scalars(query.offset((page - 1) * limit).limit(limit)).all()

    return WorkListResponse(
        items=items,
        page=page,
        limit=limit,
        total=total,
        pages=ceil(total / limit) if total else 0,
    )


@router.get("/{work_id}", response_model=WorkResponse)
def get_work(work_id: int, db: Session = Depends(get_db)):
    return get_work_or_404(work_id, db)


@router.post("", response_model=WorkResponse, status_code=status.HTTP_201_CREATED)
def create_work(
    payload: WorkCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    category = db.get(Category, payload.category_id)
    if category is None:
        raise HTTPException(status_code=400, detail="Category not found")

    work = Work(
        title=payload.title,
        description=payload.description,
        category_id=payload.category_id,
        author_id=current_user.id,
        is_hidden=False,
    )
    db.add(work)
    db.commit()
    db.refresh(work)
    return work


@router.put("/{work_id}", response_model=WorkResponse)
def update_work(
    work_id: int,
    payload: WorkUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    work = db.get(Work, work_id)
    if work is None or work.is_hidden:
        raise HTTPException(status_code=404, detail="Work not found")
    if work.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if payload.category_id is not None and db.get(Category, payload.category_id) is None:
        raise HTTPException(status_code=400, detail="Category not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(work, field, value)

    db.commit()
    db.refresh(work)
    return work


@router.delete("/{work_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work(
    work_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    work = db.get(Work, work_id)
    if work is None:
        raise HTTPException(status_code=404, detail="Work not found")
    if work.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")

    db.delete(work)
    db.commit()
