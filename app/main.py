"""
FastAPI 入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, categories, stats, transactions

app = FastAPI(title="Personal Ledger", version="1.0.0")

# React dev server runs on :5173, allow it to call our API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(stats.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
