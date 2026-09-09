"""Transaction CRUD routes — synced with wallet."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Transaction, User, Wallet, LedgerEntry, EntryDirection, TransactionType
from ..schemas import TransactionCreate, TransactionUpdate, TransactionRead
from ..auth import get_current_user

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/", response_model=TransactionRead, status_code=201)
def create_transaction(
    payload: TransactionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()

    # Expense: deduct from wallet
    if payload.type == TransactionType.expense:
        if wallet and wallet.balance < payload.amount:
            raise HTTPException(400, "Insufficient wallet balance")
        if wallet:
            wallet.balance = wallet.balance - payload.amount
            db.add(LedgerEntry(
                user_id=user.id, direction=EntryDirection.debit,
                amount=payload.amount, ref_type="expense",
                note=payload.note or "Expense",
            ))

    # Income: add to wallet
    if payload.type == TransactionType.income:
        if wallet:
            wallet.balance = wallet.balance + payload.amount
            db.add(LedgerEntry(
                user_id=user.id, direction=EntryDirection.credit,
                amount=payload.amount, ref_type="income",
                note=payload.note or "Income",
            ))

    txn = Transaction(**payload.model_dump(), user_id=user.id)
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


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

    # Reverse the wallet effect
    wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()
    if wallet:
        if txn.type == TransactionType.expense:
            wallet.balance = wallet.balance + txn.amount
        elif txn.type == TransactionType.income:
            wallet.balance = wallet.balance - txn.amount

    db.delete(txn)
    db.commit()
