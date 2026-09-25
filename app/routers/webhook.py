"""
Stripe webhook handler — receives payment events from Stripe.

Processes checkout.session.completed to:
  1. Look up the Order by stripe_session_id
  2. Transition order to completed
  3. Credit the user's wallet (with FOR UPDATE lock)
  4. Write double-entry ledger records

Idempotent: if the order is already completed, returns 200 without re-processing.
"""

import logging

import stripe
from fastapi import APIRouter, Request, HTTPException

from ..database import SessionLocal, lock_for_update
from ..models import Order, OrderStatus, Wallet, LedgerEntry, EntryDirection
from ..config import STRIPE_WEBHOOK_SECRET
from ..stripe_service import construct_webhook_event

logger = logging.getLogger(__name__)

router = APIRouter(tags=["webhook"])


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """
    Stripe sends events here. We verify the signature, then process.
    Only checkout.session.completed is acted on; others are acknowledged.
    """
    body = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")

    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(503, "Webhook secret not configured")

    # ── Verify signature ──
    try:
        event = construct_webhook_event(body, sig_header, STRIPE_WEBHOOK_SECRET)
    except stripe.SignatureVerificationError:
        logger.warning("Stripe webhook signature verification failed")
        raise HTTPException(400, "Invalid signature")
    except ValueError:
        raise HTTPException(400, "Invalid payload")

    # ── Route by event type ──
    if event["type"] == "checkout.session.completed":
        _handle_checkout_completed(event["data"]["object"])
    elif event["type"] == "checkout.session.expired":
        _handle_checkout_expired(event["data"]["object"])
    else:
        logger.info("Unhandled Stripe event type: %s", event["type"])

    return {"status": "ok"}


def _handle_checkout_completed(session_data: dict):
    """
    Process a successful checkout:
      • Find order by stripe_session_id
      • Transition pending/processing → completed
      • Credit wallet with FOR UPDATE lock
      • Write ledger entries
    """
    session_id = session_data["id"]
    payment_intent_id = session_data.get("payment_intent")

    db = SessionLocal()
    try:
        order = (
            db.query(Order)
            .filter(Order.stripe_session_id == session_id)
            .first()
        )
        if not order:
            logger.warning("No order found for Stripe session %s", session_id)
            return

        # Idempotent: already processed
        if order.status == OrderStatus.completed:
            logger.info("Order %d already completed, skipping", order.id)
            return

        # Store Payment Intent ID
        if payment_intent_id:
            order.stripe_payment_intent_id = payment_intent_id

        # Transition to completed
        try:
            if order.status == OrderStatus.pending:
                order.status = OrderStatus.processing
            order.status = OrderStatus.completed
        except Exception:
            logger.error("Invalid state transition for order %d (status=%s)", order.id, order.status)
            return

        # Credit wallet with row lock
        wallet = lock_for_update(
            db.query(Wallet).filter(Wallet.user_id == order.user_id)
        ).first()

        if wallet:
            wallet.balance = wallet.balance + order.amount
            db.add(LedgerEntry(
                user_id=order.user_id,
                direction=EntryDirection.credit,
                amount=order.amount,
                ref_type="payment",
                note=f"Stripe payment order #{order.id}",
            ))

        db.commit()
        logger.info(
            "Order %d completed via Stripe. Credited %s to user %d",
            order.id, order.amount, order.user_id,
        )
    except Exception:
        db.rollback()
        logger.exception("Error processing checkout.session.completed for %s", session_id)
        raise
    finally:
        db.close()


def _handle_checkout_expired(session_data: dict):
    """Mark the order as failed when the Stripe checkout session expires."""
    session_id = session_data["id"]

    db = SessionLocal()
    try:
        order = (
            db.query(Order)
            .filter(Order.stripe_session_id == session_id)
            .first()
        )
        if not order:
            return

        if order.status in (OrderStatus.pending, OrderStatus.processing):
            order.status = OrderStatus.failed
            db.commit()
            logger.info("Order %d marked failed (Stripe session expired)", order.id)
    except Exception:
        db.rollback()
        logger.exception("Error processing checkout.session.expired for %s", session_id)
    finally:
        db.close()


# ── Legacy mock gateway webhook (kept for backward compatibility) ──

import hashlib
import hmac
import json

LEGACY_GATEWAY_SECRET = "shared-gateway-secret-2026"


def _verify_legacy_signature(body: bytes, signature: str) -> bool:
    expected = hmac.new(LEGACY_GATEWAY_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/webhook/payment")
async def legacy_payment_webhook(request: Request):
    """Legacy mock gateway webhook — kept for backward compat during migration."""
    body = await request.body()
    signature = request.headers.get("X-Gateway-Signature", "")

    if not _verify_legacy_signature(body, signature):
        raise HTTPException(400, "Invalid signature")

    data = json.loads(body)
    order_id = data["order_id"]
    gateway_ref = data["gateway_ref"]
    status = data["status"]

    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(404, "Order not found")

        new_status = OrderStatus.completed if status == "completed" else OrderStatus.failed
        if order.status == new_status:
            return {"status": "ok"}  # idempotent

        order.status = new_status
        order.gateway_ref = gateway_ref

        if new_status == OrderStatus.completed:
            wallet = lock_for_update(
                db.query(Wallet).filter(Wallet.user_id == order.user_id)
            ).first()
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
        return {"status": "ok"}
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(500, "Webhook processing failed")
    finally:
        db.close()
