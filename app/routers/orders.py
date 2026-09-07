"""Orders routes — create payment orders, query status."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Order, OrderStatus, ORDER_TRANSITIONS, User
from ..schemas import OrderCreate, OrderRead
from ..auth import get_current_user

router = APIRouter(prefix="/orders", tags=["orders"])


def transition_order(order: Order, new_status: OrderStatus):
    """Enforce state machine: only allowed transitions pass."""
    allowed = ORDER_TRANSITIONS.get(order.status, set())
    if new_status not in allowed:
        raise HTTPException(
            409,
            f"Cannot transition from {order.status.value} to {new_status.value}",
        )
    order.status = new_status


@router.post("/", response_model=OrderRead, status_code=201)
def create_order(
    payload: OrderCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.amount <= 0:
        raise HTTPException(400, "Amount must be positive")

    order = Order(user_id=user.id, amount=payload.amount)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.get("/", response_model=list[OrderRead])
def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Order)
        .filter(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{order_id}", response_model=OrderRead)
def get_order(
    order_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == user.id)
        .first()
    )
    if not order:
        raise HTTPException(404, "Order not found")
    return order
