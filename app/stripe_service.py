"""
Stripe integration service — wraps the Stripe SDK with retry logic.

Uses Stripe Checkout Sessions (test mode) for the payment flow:
  1. Backend creates a Checkout Session → returns URL
  2. Frontend redirects user to Stripe-hosted checkout page
  3. Stripe sends webhook on payment completion
  4. Backend processes webhook, credits wallet

All Stripe API calls are wrapped with tenacity retry for transient failures.
"""

import logging

import stripe
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception,
)

from .config import STRIPE_SECRET_KEY, STRIPE_SUCCESS_URL, STRIPE_CANCEL_URL

logger = logging.getLogger(__name__)

# Configure the Stripe SDK
stripe.api_key = STRIPE_SECRET_KEY


def _is_retryable_stripe_error(exc: BaseException) -> bool:
    """Only retry on transient Stripe errors (rate limit, API connection, 500s)."""
    if isinstance(exc, stripe.RateLimitError):
        return True
    if isinstance(exc, stripe.APIConnectionError):
        return True
    if isinstance(exc, stripe.APIError) and getattr(exc, "http_status", 0) >= 500:
        return True
    return False


_stripe_retry = retry(
    retry=retry_if_exception(_is_retryable_stripe_error),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)


@_stripe_retry
def create_checkout_session(
    order_id: int,
    amount_cents: int,
    currency: str = "myr",
    idempotency_key: str | None = None,
) -> stripe.checkout.Session:
    """
    Create a Stripe Checkout Session for a top-up / payment order.

    Args:
        order_id: internal order ID, stored in Session metadata
        amount_cents: amount in smallest currency unit (e.g. cents for MYR)
        currency: three-letter ISO currency code
        idempotency_key: optional key forwarded to Stripe for dedup

    Returns:
        stripe.checkout.Session with .id and .url
    """
    params = dict(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": currency,
                "unit_amount": amount_cents,
                "product_data": {
                    "name": f"Wallet Top-Up (Order #{order_id})",
                    "description": f"Add {currency.upper()} {amount_cents / 100:.2f} to your wallet",
                },
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=f"{STRIPE_SUCCESS_URL}&order_id={order_id}",
        cancel_url=f"{STRIPE_CANCEL_URL}&order_id={order_id}",
        metadata={"order_id": str(order_id)},
    )

    kwargs = {}
    if idempotency_key:
        kwargs["idempotency_key"] = f"checkout_{idempotency_key}"

    session = stripe.checkout.Session.create(**params, **kwargs)
    logger.info("Stripe Checkout Session created: %s for order %d", session.id, order_id)
    return session


@_stripe_retry
def retrieve_checkout_session(session_id: str) -> stripe.checkout.Session:
    """Fetch a Checkout Session by ID (with retry)."""
    return stripe.checkout.Session.retrieve(session_id)


@_stripe_retry
def retrieve_payment_intent(pi_id: str) -> stripe.PaymentIntent:
    """Fetch a Payment Intent by ID (with retry)."""
    return stripe.PaymentIntent.retrieve(pi_id)


def construct_webhook_event(payload: bytes, sig_header: str, webhook_secret: str):
    """
    Verify and parse a Stripe webhook event.
    Raises stripe.SignatureVerificationError on invalid signature.
    """
    return stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
