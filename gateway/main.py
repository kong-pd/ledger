"""Mock payment gateway — runs on :9000, simulates async payment processing."""

import hashlib
import hmac
import random
import time
import threading

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Mock Payment Gateway", version="1.0.0")

GATEWAY_SECRET = "shared-gateway-secret-2026"


class PayRequest(BaseModel):
    order_id: int
    amount: float
    callback_url: str


class PayResponse(BaseModel):
    gateway_ref: str
    status: str


def make_signature(payload: str) -> str:
    """HMAC-SHA256 signature using shared secret."""
    return hmac.new(GATEWAY_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()


def process_payment(order_id: int, amount: float, callback_url: str, gateway_ref: str):
    """Background: delay, pick outcome, call webhook."""
    time.sleep(3)

    # Random outcome: 80% success, 20% failure
    status = "completed" if random.random() < 0.8 else "failed"

    # Build callback payload and sign it
    import json
    body = json.dumps({
        "order_id": order_id,
        "gateway_ref": gateway_ref,
        "status": status,
    })
    signature = make_signature(body)

    # Call our app's webhook
    try:
        httpx.post(
            callback_url,
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Gateway-Signature": signature,
            },
            timeout=10,
        )
    except Exception as e:
        print(f"Webhook delivery failed: {e}")


@app.post("/pay", response_model=PayResponse)
def pay(req: PayRequest):
    if req.amount <= 0:
        raise HTTPException(400, "Amount must be positive")

    gateway_ref = f"GW-{req.order_id}-{random.randint(1000, 9999)}"

    # Process in background thread (simulates async)
    thread = threading.Thread(
        target=process_payment,
        args=(req.order_id, req.amount, req.callback_url, gateway_ref),
    )
    thread.start()

    return {"gateway_ref": gateway_ref, "status": "accepted"}
