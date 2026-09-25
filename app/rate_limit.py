"""
Rate limiting via slowapi.

Provides per-endpoint rate limits to protect against abuse:
  • Auth endpoints (login/register):  10/minute  — prevent brute force
  • Payment endpoints:                 5/minute  — prevent payment spam
  • General read endpoints:           60/minute  — reasonable API usage

Key function extracts client IP from the request (supports X-Forwarded-For
behind a reverse proxy).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from .config import RATE_LIMIT_DEFAULT, RATE_LIMIT_AUTH, RATE_LIMIT_PAYMENT

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[RATE_LIMIT_DEFAULT],
    storage_uri="memory://",   # in-memory; use Redis URI in production clusters
)

# Reusable decorators for different tiers
auth_limit = limiter.limit(RATE_LIMIT_AUTH)
payment_limit = limiter.limit(RATE_LIMIT_PAYMENT)
default_limit = limiter.limit(RATE_LIMIT_DEFAULT)
