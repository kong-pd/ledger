"""
ORM 模型 — 对应 ER 图里的三张表
================================

关系建模核心知识点（全在这个文件里）：

1. 主键 (PK)：每张表唯一标识一行的字段，autoincrement 自动递增。
2. 外键 (FK)：指向另一张表的主键，用来表达 "属于" 关系。
   - transactions.user_id → users.id   意味着 "这笔交易属于某个用户"
   - transactions.category_id → categories.id  意味着 "这笔交易归到某个分类"
3. 一对多 (One-to-Many)：一个 user 拥有多条 transaction。
   在 "一" 的那侧用 relationship()，在 "多" 的那侧放 ForeignKey。
4. nullable FK：category_id 允许为空，新记账时可以不选分类。
5. ondelete="CASCADE"：删用户时，他的所有交易一起删（级联删除）。
   ondelete="SET NULL"：删分类时，相关交易的 category_id 置空而不是报错。
"""

import enum
from datetime import date, datetime

from sqlalchemy import (
    Column, Integer, String, Numeric, Date, DateTime,
    Enum, ForeignKey, Text,
)
from sqlalchemy.orm import relationship

from .database import Base


# ---------- 枚举 ----------

class TransactionType(str, enum.Enum):
    """收入 / 支出"""
    income = "income"
    expense = "expense"


# ---------- users ----------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # relationship: 方便通过 user.categories / user.transactions 直接拿到关联数据
    # back_populates 让双向都能走：user.categories ↔ category.owner
    categories = relationship("Category", back_populates="owner", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="owner", cascade="all, delete-orphan")


# ---------- categories ----------

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")


# ---------- transactions ----------

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Numeric(10, 2), nullable=False)          # 最大 99999999.99
    type = Column(Enum(TransactionType), nullable=False)
    note = Column(Text, nullable=True)                        # 备注，可不填
    date = Column(Date, nullable=False, default=date.today)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="SET NULL"),     # 删分类 → 置空
        nullable=True,
    )
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
