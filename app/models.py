"""ORM models — users, categories, transactions, wallets, ledger entries."""

import enum
from datetime import date, datetime

from sqlalchemy import (
    Column, Integer, String, Numeric, Date, DateTime,
    Enum, ForeignKey, Text, CheckConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    categories = relationship("Category", back_populates="owner", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="owner", cascade="all, delete-orphan")
    wallet = relationship("Wallet", back_populates="owner", uselist=False, cascade="all, delete-orphan")


class Wallet(Base):
    __tablename__ = "wallets"
    __table_args__ = (
        CheckConstraint("balance >= 0", name="ck_wallet_non_negative"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    balance = Column(Numeric(12, 2), nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="wallet")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Numeric(10, 2), nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    note = Column(Text, nullable=True)
    date = Column(Date, nullable=False, default=date.today)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="SET NULL"),  # keep transactions when category is deleted
        nullable=True,
    )
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")


class EntryDirection(str, enum.Enum):
    debit = "debit"
    credit = "credit"


class LedgerEntry(Base):
    """Double-entry ledger: every money movement produces a debit + credit pair."""
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    direction = Column(Enum(EntryDirection), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    counterparty_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ref_type = Column(String(20), nullable=False)  # "topup" / "transfer"
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", foreign_keys=[user_id])
