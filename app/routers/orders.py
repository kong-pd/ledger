"""Orders routes — embedded mock gateway as background task."""

import random
import threading
import time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db, SessionLocal
from ..models import Order, OrderStatus, ORDER_TRANSITIONS, User, Wallet, LedgerEntry, EntryDirection
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


def process_payment_background(order_id: int):
    """Background task: simulate gateway processing, then update order."""
    time.sleep(3)

    status = OrderStatus.completed if random.random() < 0.8 else OrderStatus.failed

    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order or order.status != OrderStatus.processing:
            return

        order.status = status
        order.gateway_ref = f"GW-{order_id}-{random.randint(1000, 9999)}"

        if status == OrderStatus.completed:
            wallet = db.query(Wallet).filter(Wallet.user_id == order.user_id).first()
            if wallet:
                wallet.balance = wallet.balance + order.amount
                db.add(LedgerEntry(
                    user_id=order.user_id,
                    direction=EntryDirection.credit,
                    amount=order.amount,
                    ref_type="payment",
                    note=f"Payment order #{order.id}",
                ))

        db.commit()
    finally:
        db.close()


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

    # Move to processing and start background task
    transition_order(order, OrderStatus.processing)
    db.commit()
    db.refresh(order)

    threading.Thread(target=process_payment_background, args=(order.id,)).start()

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
