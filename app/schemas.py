"""Pydantic schemas — request/response validation."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from .models import TransactionType


# --- Auth ---

class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Category ---

class CategoryCreate(BaseModel):
    name: str
    type: TransactionType


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[TransactionType] = None


class CategoryRead(BaseModel):
    id: int
    name: str
    type: TransactionType
    user_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Wallet ---

class WalletRead(BaseModel):
    balance: Decimal
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class TopUpRequest(BaseModel):
    amount: Decimal


class TransferRequest(BaseModel):
    to_username: str
    amount: Decimal


class TransferRead(BaseModel):
    from_user: str
    to_user: str
    amount: Decimal
    sender_balance: Decimal


class LedgerEntryRead(BaseModel):
    id: int
    direction: str
    amount: Decimal
    counterparty_id: Optional[int]
    ref_type: str
    note: Optional[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Transaction ---

class TransactionCreate(BaseModel):
    amount: Decimal
    type: TransactionType
    note: Optional[str] = None
    date: date
    category_id: Optional[int] = None


class TransactionUpdate(BaseModel):
    amount: Optional[Decimal] = None
    type: Optional[TransactionType] = None
    note: Optional[str] = None
    date: Optional[date] = None
    category_id: Optional[int] = None


class TransactionRead(BaseModel):
    id: int
    amount: Decimal
    type: TransactionType
    note: Optional[str]
    date: date
    user_id: int
    category_id: Optional[int]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
