"""
统计路由
========
两个接口：
  GET /stats/monthly     → 按月汇总收入/支出
  GET /stats/by-category → 按分类汇总支出

这里用到了 SQL 聚合函数（SUM, GROUP BY），
是 CRUD 之上的第一层"业务逻辑"。
"""

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
    """
    返回某一年每个月的收入/支出合计。
    SQL 等价：
      SELECT month, type, SUM(amount)
      FROM transactions
      WHERE user_id = ? AND year = ?
      GROUP BY month, type
    """
    rows = (
        db.query(
            extract("month", Transaction.date).label("month"),
            Transaction.type,
            func.sum(Transaction.amount).label("total"),
        )
        .filter(
            Transaction.user_id == user.id,
            extract("year", Transaction.date) == year,
        )
        .group_by("month", Transaction.type)
        .all()
    )

    # 整理成前端友好的格式: [{month: 1, income: 5000, expense: 1200}, ...]
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
    month: int = Query(None, ge=1, le=12, description="Month (optional)"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    按分类汇总支出金额。
    可选按月筛选，不传 month 则统计全年。
    """
    q = (
        db.query(
            Category.name,
            func.sum(Transaction.amount).label("total"),
        )
        .join(Category, Transaction.category_id == Category.id)
        .filter(
            Transaction.user_id == user.id,
            Transaction.type == TransactionType.expense,
            extract("year", Transaction.date) == year,
        )
    )

    if month:
        q = q.filter(extract("month", Transaction.date) == month)

    rows = q.group_by(Category.name).all()

    return [{"category": name, "total": float(total)} for name, total in rows]
