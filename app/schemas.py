"""
Pydantic Schemas — 请求体 & 响应体
===================================
ORM Model  = 数据库长什么样
Schema     = API 进出的 JSON 长什么样

分成 Create（写入）和 Read（读出）两套：
  - Create 只包含用户需要提供的字段
  - Read  多了 id, created_at 等数据库自动生成的字段
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from .models import TransactionType


# ---------- Auth ----------

class UserCreate(BaseModel):
    """注册时用户需要传的字段"""
    username: str
    email: str
    password: str          # 明文，后端会 hash 后再存


class UserRead(BaseModel):
    """返回给前端的用户信息（不含密码）"""
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """登录成功后返回的 token"""
    access_token: str
    token_type: str = "bearer"


# ---------- Category ----------

class CategoryCreate(BaseModel):
    name: str
    type: TransactionType          # income 或 expense


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


# ---------- Transaction ----------

class TransactionCreate(BaseModel):
    """新建交易时，用户需要传的字段"""
    amount: Decimal
    type: TransactionType
    note: Optional[str] = None
    date: date
    category_id: Optional[int] = None


class TransactionUpdate(BaseModel):
    """更新交易：所有字段都可选，只传想改的"""
    amount: Optional[Decimal] = None
    type: Optional[TransactionType] = None
    note: Optional[str] = None
    date: Optional[date] = None
    category_id: Optional[int] = None


class TransactionRead(BaseModel):
    """返回给前端的交易数据"""
    id: int
    amount: Decimal
    type: TransactionType
    note: Optional[str]
    date: date
    user_id: int
    category_id: Optional[int]
    created_at: datetime

    # 让 Pydantic 直接从 ORM 对象读属性，不需要手动转 dict
    model_config = ConfigDict(from_attributes=True)
