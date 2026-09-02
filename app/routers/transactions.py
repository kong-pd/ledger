"""
交易 CRUD 路由
==============
四个接口：Create / Read list / Update / Delete

⚠️ 暂时硬编码 CURRENT_USER_ID = 1
   第 ② 步加 JWT 后会替换成 get_current_user 依赖。
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Transaction
from ..schemas import TransactionCreate, TransactionUpdate, TransactionRead

router = APIRouter(prefix="/transactions", tags=["transactions"])

# ---------- 临时：硬编码当前用户 ----------
CURRENT_USER_ID = 1


# ---------- C: 记一笔 ----------
@router.post("/", response_model=TransactionRead, status_code=201)
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db)):
    txn = Transaction(
        **payload.model_dump(),
        user_id=CURRENT_USER_ID,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)       # 拿回数据库生成的 id / created_at
    return txn


# ---------- R: 查列表（分页） ----------
@router.get("/", response_model=list[TransactionRead])
def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return (
        db.query(Transaction)
        .filter(Transaction.user_id == CURRENT_USER_ID)
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
    db: Session = Depends(get_db),
):
    txn = (
        db.query(Transaction)
        .filter(Transaction.id == txn_id, Transaction.user_id == CURRENT_USER_ID)
        .first()
    )
    if not txn:
        raise HTTPException(404, "Transaction not found")

    # 只更新用户传了的字段
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(txn, field, value)

    db.commit()
    db.refresh(txn)
    return txn


# ---------- D: 删一笔 ----------
@router.delete("/{txn_id}", status_code=204)
def delete_transaction(txn_id: int, db: Session = Depends(get_db)):
    txn = (
        db.query(Transaction)
        .filter(Transaction.id == txn_id, Transaction.user_id == CURRENT_USER_ID)
        .first()
    )
    if not txn:
        raise HTTPException(404, "Transaction not found")

    db.delete(txn)
    db.commit()
