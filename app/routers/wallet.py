"""
钱包路由
========
GET  /wallet        → 查看余额
POST /wallet/topup  → 模拟充值

Step 6 的新概念：
  数据库约束 CheckConstraint("balance >= 0")
  即使代码试图把余额扣成负数，数据库会直接拒绝。
  这比在 Python 里写 if 更安全——它防住了所有入口。
"""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Wallet, User
from ..schemas import WalletRead, TopUpRequest
from ..auth import get_current_user

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("/", response_model=WalletRead)
def get_balance(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()
    if not wallet:
        raise HTTPException(404, "Wallet not found")
    return wallet


@router.post("/topup", response_model=WalletRead)
def topup(
    payload: TopUpRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.amount <= 0:
        raise HTTPException(400, "Amount must be positive")

    wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()
    if not wallet:
        raise HTTPException(404, "Wallet not found")

    wallet.balance = wallet.balance + payload.amount
    db.commit()
    db.refresh(wallet)
    return wallet
