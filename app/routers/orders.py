"""
Orders routes — Stripe Checkout integration (test mode).

Flow:
  POST /orders/  →  creates Order + Stripe Checkout Session  →  returns checkout URL
  Frontend redirects to Stripe  →  user pays on Stripe-hosted page
  Stripe fires webhook  →  /webhook/stripe  →  credits wallet

Concurrency:
  • Idempotency-Key header prevents duplicate order creation from retries.
  • Order state machine enforces valid transitions only.
"""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Order, OrderStatus, ORDER_TRANSITIONS, User
from ..schemas import OrderCreate, OrderRead, StripeCheckoutResponse
from ..auth import get_current_user
from ..config import STRIPE_SECRET_KEY
from ..rate_limit import payment_limit
from .. import stripe_service

logger = logging.getLogger(__name__)

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


@router.post("/", response_model=StripeCheckoutResponse, status_code=201)
@payment_limit
def create_order(
    request: Request,
    payload: OrderCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    if payload.amount <= 0:
        raise HTTPException(400, "Amount must be positive")

    if not STRIPE_SECRET_KEY:
        raise HTTPException(
            503,
            "Stripe is not configured. Set STRIPE_SECRET_KEY env var.",
        )

    # ── Idempotency: return existing order if key was already used ──
    if idempotency_key:
        existing = (
            db.query(Order)
            .filter(
                Order.idempotency_key == idempotency_key,
                Order.user_id == user.id,
            )
            .first()
        )
        if existing and existing.stripe_session_id:
            # Retrieve the Stripe session to get the URL again
            try:
                session = stripe_service.retrieve_checkout_session(
                    existing.stripe_session_id
                )
                return {
                    "order_id": existing.id,
                    "checkout_url": session.url or "",
                    "stripe_session_id": existing.stripe_session_id,
                }
            except Exception:
                # Session expired; fall through to create a new one
                pass

    # ── Create order ──
    order = Order(
        user_id=user.id,
        amount=payload.amount,
        currency=payload.currency,
        idempotency_key=idempotency_key,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # ── Create Stripe Checkout Session ──
    amount_cents = int(payload.amount * 100)
    try:
        session = stripe_service.create_checkout_session(
            order_id=order.id,
            amount_cents=amount_cents,
            currency=payload.currency,
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        logger.error("Stripe session creation failed for order %d: %s", order.id, exc)
        order.status = OrderStatus.failed
        db.commit()
        raise HTTPException(502, f"Payment gateway error: {exc}")

    # ── Update order with Stripe references and move to processing ──
    order.stripe_session_id = session.id
    transition_order(order, OrderStatus.processing)
    db.commit()
    db.refresh(order)

    return {
        "order_id": order.id,
        "checkout_url": session.url,
        "stripe_session_id": session.id,
    }


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
