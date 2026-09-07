# Personal Ledger

Personal finance and e-wallet app — React + FastAPI + SQLite

## Architecture

![System Architecture](./docx/architecture.png)

## Payment flow

![Payment Sequence](./docx/payment-sequence.png)

## Features

- **JWT auth** — Registration and login, passwords hashed with bcrypt
- **Transaction CRUD** — Income and expense records with pagination, optional category and notes
- **Categories** — User-defined, typed (income/expense). Deleting a category nulls its transactions (`ondelete=SET NULL`)
- **E-wallet** — Balance with `CHECK(balance >= 0)` constraint, top-up, P2P transfer with atomic transactions
- **Double-entry ledger** — Every money movement produces a debit + credit pair for full audit trail
- **Stats** — Monthly income/expense summary and per-category breakdown
- **Payment gateway** (mock) — Order state machine, async processing, webhook callback with HMAC signature verification

## Tech stack

**Backend:** Python · FastAPI · SQLAlchemy · Alembic · SQLite · PyJWT · bcrypt

**Frontend:** React · Vite · Axios · React Router · Recharts

## Setup

```bash
# Backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload        # → localhost:8000

# Frontend
cd frontend && npm install
npm run dev                           # → localhost:5173

# Mock payment gateway (Phase 2)
uvicorn gateway.main:app --port 9000  # → localhost:9000
```

API docs: http://localhost:8000/docs

## API

| Method | Endpoint | Auth | Description |
| ------ | -------- | ---- | ----------- |
| POST | `/auth/register` | — | Create account |
| POST | `/auth/login` | — | Get JWT token |
| GET | `/transactions` | JWT | List (paginated) |
| POST | `/transactions` | JWT | Create |
| PATCH | `/transactions/{id}` | JWT | Partial update |
| DELETE | `/transactions/{id}` | JWT | Delete |
| GET | `/categories` | JWT | List |
| POST | `/categories` | JWT | Create |
| PATCH | `/categories/{id}` | JWT | Update |
| DELETE | `/categories/{id}` | JWT | Delete (transactions kept, category nulled) |
| GET | `/stats/monthly?year=` | JWT | Income/expense totals by month |
| GET | `/stats/by-category?year=` | JWT | Expense totals by category |
| GET | `/wallet` | JWT | Check balance |
| POST | `/wallet/topup` | JWT | Add funds |
| POST | `/wallet/transfer` | JWT | P2P transfer (atomic) |
| GET | `/wallet/history` | JWT | Ledger entries |
| POST | `/orders` | JWT | Create payment order |
| POST | `/webhook/payment` | — | Gateway callback (HMAC verified) |

## Data model

Six tables: `users`, `wallets`, `ledger_entries`, `transactions`, `categories`, `orders`. Users own wallets (1:1) and all other records (1:many). Transfers produce paired debit/credit ledger entries. Deleting a user cascades all data; deleting a category nulls references.

## Key design decisions

- **Double-entry bookkeeping** — Balance can be reconstructed from `SUM(credits) - SUM(debits)` at any time
- **Atomic transfers** — Both wallets update in a single DB transaction; failure rolls back both
- **Layered validation** — Python checks give friendly errors, DB `CHECK` constraint prevents negative balance at all entry points
- **Mock gateway** — Simulates async payment flow (request → delay → webhook) with HMAC signature verification, same interface as production gateways

## License

MIT
