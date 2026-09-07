"""Webhook route — receives payment results from the gateway."""

import hashlib
import hmac
import json

from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import Order, OrderStatus, Wallet, LedgerEntry, EntryDirection
from ..routers.orders import transition_order

router = APIRouter(tags=["webhook"])

GATEWAY_SECRET = "shared-gateway-secret-2026"


def verify_signature(body: bytes, signature: str) -> bool:
    expected = hmac.new(GATEWAY_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/webhook/payment")
async def payment_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Gateway-Signature", "")

    if not verify_signature(body, signature):
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
        transition_order(order, new_status)
        order.gateway_ref = gateway_ref

        # On success: credit the user's wallet + write ledger entry
        if new_status == OrderStatus.completed:
            wallet = db.query(Wallet).filter(Wallet.user_id == order.user_id).first()
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
