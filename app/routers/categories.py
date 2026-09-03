"""
分类 CRUD 路由
==============
用户可以自建分类（如 "餐饮"、"工资"），记账时关联。

这一步的关系建模重点：
  删分类时，已关联的交易怎么办？
  → models.py 里设了 ondelete="SET NULL"
  → 所以删分类后，那些交易的 category_id 变成 NULL（未分类）
  → 交易本身不会丢
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Category, User
from ..schemas import CategoryCreate, CategoryUpdate, CategoryRead
from ..auth import get_current_user

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("/", response_model=CategoryRead, status_code=201)
def create_category(
    payload: CategoryCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cat = Category(**payload.model_dump(), user_id=user.id)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.get("/", response_model=list[CategoryRead])
def list_categories(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Category)
        .filter(Category.user_id == user.id)
        .order_by(Category.name)
        .all()
    )


@router.patch("/{cat_id}", response_model=CategoryRead)
def update_category(
    cat_id: int,
    payload: CategoryUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cat = (
        db.query(Category)
        .filter(Category.id == cat_id, Category.user_id == user.id)
        .first()
    )
    if not cat:
        raise HTTPException(404, "Category not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(cat, field, value)

    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/{cat_id}", status_code=204)
def delete_category(
    cat_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cat = (
        db.query(Category)
        .filter(Category.id == cat_id, Category.user_id == user.id)
        .first()
    )
    if not cat:
        raise HTTPException(404, "Category not found")

    db.delete(cat)
    db.commit()
