"""Admin routes — requires is_admin=1."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Wallet, Order
from ..auth import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])


def get_admin_user(user: User = Depends(get_current_user)) -> User:
    """Dependency: same as get_current_user but rejects non-admins."""
    if not user.is_admin:
        raise HTTPException(403, "Admin access required")
    return user


@router.get("/users")
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    users = db.query(User).offset(skip).limit(limit).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "is_admin": bool(u.is_admin),
            "created_at": u.created_at,
            "wallet_balance": float(u.wallet.balance) if u.wallet else None,
        }
        for u in users
    ]


@router.get("/users/{user_id}")
def get_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    orders = db.query(Order).filter(Order.user_id == user_id).count()
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_admin": bool(user.is_admin),
        "created_at": user.created_at,
        "wallet_balance": float(user.wallet.balance) if user.wallet else None,
        "order_count": orders,
    }


@router.patch("/users/{user_id}/toggle-admin")
def toggle_admin(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.id == admin.id:
        raise HTTPException(400, "Cannot change your own admin status")

    user.is_admin = 0 if user.is_admin else 1
    db.commit()
    return {"id": user.id, "username": user.username, "is_admin": bool(user.is_admin)}


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.id == admin.id:
        raise HTTPException(400, "Cannot delete yourself")

    db.delete(user)  # CASCADE deletes wallet, transactions, orders, ledger entries
    db.commit()
