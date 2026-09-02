"""
交易 CRUD 路由
==============
四个接口：Create / Read list / Update / Delete

所有路由都通过 get_current_user 获取当前登录用户，
未登录请求会被自动拦截返回 401。
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Transaction, User
from ..schemas import TransactionCreate, TransactionUpdate, TransactionRead
from ..auth import get_current_user

router = APIRouter(prefix="/transactions", tags=["transactions"])


# ---------- C: 记一笔 ----------
@router.post("/", response_model=TransactionRead, status_code=201)
def create_transaction(
    payload: TransactionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    txn = Transaction(
        **payload.model_dump(),
        user_id=user.id,          # ← 从 token 里拿到的真实用户
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


# ---------- R: 查列表（分页） ----------
@router.get("/", response_model=list[TransactionRead])
def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Transaction)
        .filter(Transaction.user_id == user.id)
        .order_by(Transaction.date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ---------- U: 改一笔 ----------
@router.patch("/{txn_id}", response_model=TransactionRead)
def update_transaction(
    txn_id: int,
    payload: TransactionUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    txn = (
        db.query(Transaction)
        .filter(Transaction.id == txn_id, Transaction.user_id == user.id)
        .first()
    )
    if not txn:
        raise HTTPException(404, "Transaction not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(txn, field, value)

    db.commit()
    db.refresh(txn)
    return txn


# ---------- D: 删一笔 ----------
@router.delete("/{txn_id}", status_code=204)
def delete_transaction(
    txn_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    txn = (
        db.query(Transaction)
        .filter(Transaction.id == txn_id, Transaction.user_id == user.id)
        .first()
    )
    if not txn:
        raise HTTPException(404, "Transaction not found")

    db.delete(txn)
    db.commit()
