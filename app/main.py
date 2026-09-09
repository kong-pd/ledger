"""
FastAPI 入口
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import admin, auth, categories, orders, stats, transactions, wallet, webhook

app = FastAPI(title="Personal Ledger", version="1.2.0")

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {"status": "ok"}
