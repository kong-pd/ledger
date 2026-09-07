"""Orders routes — create payment orders, query status."""

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Order, OrderStatus, ORDER_TRANSITIONS, User
from ..schemas import OrderCreate, OrderRead
from ..auth import get_current_user

router = APIRouter(prefix="/orders", tags=["orders"])

GATEWAY_URL = "http://localhost:9000/pay"
CALLBACK_URL = "http://localhost:8000/webhook/payment"


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

    # 1. Create order as pending
    order = Order(user_id=user.id, amount=payload.amount)
    db.add(order)
    db.commit()
    db.refresh(order)

    # 2. Call the payment gateway
    try:
        resp = httpx.post(GATEWAY_URL, json={
            "order_id": order.id,
            "amount": float(order.amount),
            "callback_url": CALLBACK_URL,
        }, timeout=10)
        resp.raise_for_status()
        gw_data = resp.json()

        # 3. Gateway accepted → move to processing
        transition_order(order, OrderStatus.processing)
        order.gateway_ref = gw_data["gateway_ref"]
        db.commit()
        db.refresh(order)

    except httpx.HTTPError:
        # Gateway unreachable → mark as failed
        transition_order(order, OrderStatus.failed)
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
