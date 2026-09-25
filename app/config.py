"""App configuration. In production, read all secrets from env vars."""

import os
from dotenv import load_dotenv

# Load .env file so env vars are available without manual `export`
load_dotenv()

# ── JWT ──
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# ── Stripe (test mode) ──
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")          # sk_test_...
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")  # whsec_...
STRIPE_SUCCESS_URL = os.environ.get(
    "STRIPE_SUCCESS_URL", "http://localhost:5173/wallet?payment=success"
)
STRIPE_CANCEL_URL = os.environ.get(
    "STRIPE_CANCEL_URL", "http://localhost:5173/wallet?payment=cancelled"
)

# ── Rate limiting ──
RATE_LIMIT_DEFAULT = os.environ.get("RATE_LIMIT_DEFAULT", "60/minute")
RATE_LIMIT_AUTH = os.environ.get("RATE_LIMIT_AUTH", "10/minute")
RATE_LIMIT_PAYMENT = os.environ.get("RATE_LIMIT_PAYMENT", "5/minute")
