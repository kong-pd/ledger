"""Statistics routes — monthly and per-category aggregations."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Transaction, Category, User, TransactionType
from ..auth import get_current_user

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/monthly")
def monthly_summary(
    year: int = Query(..., description="Year, e.g. 2026"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(
            extract("month", Transaction.date).label("month"),
            Transaction.type,
            func.sum(Transaction.amount).label("total"),
        )
        .filter(Transaction.user_id == user.id, extract("year", Transaction.date) == year)
        .group_by("month", Transaction.type)
        .all()
    )

    months = {}
    for month, txn_type, total in rows:
        m = int(month)
        if m not in months:
            months[m] = {"month": m, "income": 0, "expense": 0}
        months[m][txn_type.value] = float(total)

    return sorted(months.values(), key=lambda x: x["month"])


@router.get("/by-category")
def category_summary(
    year: int = Query(..., description="Year, e.g. 2026"),
    month: int = Query(None, ge=1, le=12),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = (
        db.query(Category.name, func.sum(Transaction.amount).label("total"))
        .join(Category, Transaction.category_id == Category.id)
        .filter(
            Transaction.user_id == user.id,
            Transaction.type == TransactionType.expense,
            extract("year", Transaction.date) == year,
        )
    )
    if month:
        q = q.filter(extract("month", Transaction.date) == month)

    return [{"category": name, "total": float(total)} for name, total in q.group_by(Category.name).all()]
