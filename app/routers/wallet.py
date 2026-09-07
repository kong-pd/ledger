"""Wallet routes — balance, top-up, transfer, ledger history."""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Wallet, User, LedgerEntry, EntryDirection
from ..schemas import (
    WalletRead, TopUpRequest,
    TransferRequest, TransferRead,
    LedgerEntryRead,
)
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
    db.add(LedgerEntry(
        user_id=user.id,
        direction=EntryDirection.credit,
        amount=payload.amount,
        ref_type="topup",
        note="Top up",
    ))

    db.commit()
    db.refresh(wallet)
    return wallet


@router.post("/transfer", response_model=TransferRead)
def transfer(
    payload: TransferRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.amount <= 0:
        raise HTTPException(400, "Amount must be positive")
    if payload.to_username == user.username:
        raise HTTPException(400, "Cannot transfer to yourself")

    receiver = db.query(User).filter(User.username == payload.to_username).first()
    if not receiver:
        raise HTTPException(404, "Recipient not found")

    sender_wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()
    receiver_wallet = db.query(Wallet).filter(Wallet.user_id == receiver.id).first()

    if sender_wallet.balance < payload.amount:
        raise HTTPException(400, "Insufficient balance")

    # Atomic: both balance updates + both ledger entries share one commit
    sender_wallet.balance = sender_wallet.balance - payload.amount
    receiver_wallet.balance = receiver_wallet.balance + payload.amount

    db.add(LedgerEntry(
        user_id=user.id, direction=EntryDirection.debit,
        amount=payload.amount, counterparty_id=receiver.id,
        ref_type="transfer", note=f"Transfer to {receiver.username}",
    ))
    db.add(LedgerEntry(
        user_id=receiver.id, direction=EntryDirection.credit,
        amount=payload.amount, counterparty_id=user.id,
        ref_type="transfer", note=f"Transfer from {user.username}",
    ))

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(500, "Transfer failed")

    db.refresh(sender_wallet)
    return {
        "from_user": user.username,
        "to_user": receiver.username,
        "amount": payload.amount,
        "sender_balance": sender_wallet.balance,
    }


@router.get("/history", response_model=list[LedgerEntryRead])
def ledger_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(LedgerEntry)
        .filter(LedgerEntry.user_id == user.id)
        .order_by(LedgerEntry.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
