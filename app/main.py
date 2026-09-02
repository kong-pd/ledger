"""
FastAPI 入口
"""

from fastapi import FastAPI

from .routers import auth, transactions

app = FastAPI(title="Personal Ledger", version="0.2.0")

app.include_router(auth.router)
app.include_router(transactions.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
