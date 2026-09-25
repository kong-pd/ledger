"""Database connection, session factory, and concurrency helpers."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Query

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./ledger.db")

# Fix Render's postgres:// → postgresql:// (legacy URL scheme)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Runtime flag: does the engine support SELECT ... FOR UPDATE?
IS_POSTGRES = DATABASE_URL.startswith("postgresql")


class Base(DeclarativeBase):
    pass


def get_db():
    """Yield a DB session per request, auto-closed on completion."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def lock_for_update(query: Query) -> Query:
    """
    Apply SELECT ... FOR UPDATE when running on PostgreSQL.
    SQLite uses database-level locking, so FOR UPDATE is unnecessary and unsupported.
    """
    if IS_POSTGRES:
        return query.with_for_update()
    return query
