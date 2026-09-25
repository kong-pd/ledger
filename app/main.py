"""
FastAPI 入口 — production-grade configuration.
"""

import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .routers import admin, auth, categories, orders, stats, transactions, wallet, webhook
from .rate_limit import limiter

app = FastAPI(title="Personal Ledger", version="2.0.0")

# ── Rate limiter ──
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Idempotency-Key"],  # allow idempotency header
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)

# ── Routers ──
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(stats.router)
app.include_router(wallet.router)
app.include_router(orders.router)
app.include_router(webhook.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "2.0.0"}
