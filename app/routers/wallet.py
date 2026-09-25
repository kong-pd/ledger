"""Wallet routes — balance, top-up, transfer, ledger history.

Production hardening:
  • SELECT ... FOR UPDATE on wallet rows prevents concurrent double-spend.
  • Idempotency-Key header prevents duplicate transfers from retries.
"""

from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from sqlalchemy.orm import Session

from ..database import get_db, lock_for_update
from ..models import Wallet, User, LedgerEntry, EntryDirection, IdempotencyRecord
from ..schemas import (
    WalletRead, TopUpRequest,
    TransferRequest, TransferRead,
    LedgerEntryRead,
)
from ..auth import get_current_user

import json

router = APIRouter(prefix="/wallet", tags=["wallet"])


# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────

def _get_wallet_locked(db: Session, user_id: int) -> Wallet:
    """Fetch wallet with row-level lock (FOR UPDATE on PG, plain query on SQLite)."""
    wallet = lock_for_update(
        db.query(Wallet).filter(Wallet.user_id == user_id)
    ).first()
    if not wallet:
        raise HTTPException(404, "Wallet not found")
    return wallet


def _check_idempotency(
    db: Session, key: str | None, user_id: int, path: str
) -> IdempotencyRecord | None:
    """If key was already used, return the stored record; else None."""
    if not key:
        return None
    record = (
        db.query(IdempotencyRecord)
        .filter(
            IdempotencyRecord.key == key,
            IdempotencyRecord.user_id == user_id,
        )
        .first()
    )
    if record and record.request_path != path:
        raise HTTPException(
            422,
            "Idempotency-Key was already used on a different endpoint",
        )
    return record


def _save_idempotency(
    db: Session, key: str | None, user_id: int, path: str,
    status_code: int, body: dict,
):
    if not key:
        return
    db.add(IdempotencyRecord(
        key=key,
        user_id=user_id,
        request_path=path,
        response_code=status_code,
        response_body=json.dumps(body),
    ))


# ──────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────

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
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    if payload.amount <= 0:
        raise HTTPException(400, "Amount must be positive")

    # Idempotency check
    existing = _check_idempotency(db, idempotency_key, user.id, "/wallet/topup")
    if existing:
        return json.loads(existing.response_body)

    # Lock the wallet row to prevent concurrent modification
    wallet = _get_wallet_locked(db, user.id)

    wallet.balance = wallet.balance + payload.amount
    db.add(LedgerEntry(
        user_id=user.id,
        direction=EntryDirection.credit,
        amount=payload.amount,
        ref_type="topup",
        note="Top up",
    ))

    result = {"balance": float(wallet.balance + payload.amount), "updated_at": None}

    try:
        db.commit()
        db.refresh(wallet)
        result = {"balance": float(wallet.balance), "updated_at": str(wallet.updated_at)}
    except Exception:
        db.rollback()
        raise HTTPException(500, "Top-up failed")

    # Persist idempotency record (separate transaction — fire-and-forget is fine)
    if idempotency_key:
        try:
            _save_idempotency(
                db, idempotency_key, user.id, "/wallet/topup", 200, result
            )
            db.commit()
        except Exception:
            db.rollback()  # duplicate key = already stored; ignore

    return wallet


@router.post("/transfer", response_model=TransferRead)
def transfer(
    payload: TransferRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    if payload.amount <= 0:
        raise HTTPException(400, "Amount must be positive")
    if payload.to_username == user.username:
        raise HTTPException(400, "Cannot transfer to yourself")

    # Idempotency check
    existing = _check_idempotency(db, idempotency_key, user.id, "/wallet/transfer")
    if existing:
        return json.loads(existing.response_body)

    receiver = db.query(User).filter(User.username == payload.to_username).first()
    if not receiver:
        raise HTTPException(404, "Recipient not found")

    # Lock BOTH wallets in a consistent order (lower id first) to prevent deadlocks
    ids = sorted([user.id, receiver.id])
    wallets = {
        w.user_id: w
        for w in lock_for_update(
            db.query(Wallet).filter(Wallet.user_id.in_(ids)).order_by(Wallet.user_id)
        ).all()
    }
    sender_wallet = wallets.get(user.id)
    receiver_wallet = wallets.get(receiver.id)

    if not sender_wallet or not receiver_wallet:
        raise HTTPException(404, "Wallet not found")
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
    result = {
        "from_user": user.username,
        "to_user": receiver.username,
        "amount": float(payload.amount),
        "sender_balance": float(sender_wallet.balance),
    }

    # Persist idempotency record
    if idempotency_key:
        try:
            _save_idempotency(
                db, idempotency_key, user.id, "/wallet/transfer", 200, result
            )
            db.commit()
        except Exception:
            db.rollback()

    return result


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
