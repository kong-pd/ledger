# Personal Ledger

Personal Ledger App — React + FastAPI + SQLite

## Features

- **JWT auth** — Registration and login, passwords hashed with bcrypt
- **Transaction CRUD** — Income and expense records with pagination, optional category and notes
- **Categories** — User-defined, typed (income/expense). Deleting a category sets its transactions to uncategorized rather than deleting them (`ondelete=SET NULL`)
- **Stats** — Monthly income/expense summary and per-category expense breakdown, with optional month filter

## Tech stack

**Backend:** Python · FastAPI · SQLAlchemy · Alembic · SQLite · python-jose (JWT) · bcrypt

**Frontend:** React · Vite · Recharts

## Setup

```
# Backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload        # → localhost:8000

# Frontend
cd frontend && npm install
npm run dev                           # → localhost:5173
```

API docs: http://localhost:8000/docs

## API

| Method | Endpoint | Auth | Description |
| ------ | -------- | ---- | ----------- |
| POST | `/auth/register` | — | Create account |
| POST | `/auth/login` | — | Get JWT token |
| GET | `/transactions` | JWT | List (paginated: `skip`, `limit`) |
| POST | `/transactions` | JWT | Create |
| PATCH | `/transactions/{id}` | JWT | Partial update |
| DELETE | `/transactions/{id}` | JWT | Delete |
| GET | `/categories` | JWT | List |
| POST | `/categories` | JWT | Create |
| PATCH | `/categories/{id}` | JWT | Partial update |
| DELETE | `/categories/{id}` | JWT | Delete (transactions keep, category nulled) |
| GET | `/stats/monthly?year=` | JWT | Income/expense totals by month |
| GET | `/stats/by-category?year=` | JWT | Expense totals by category (optional `month`) |

## Data model

Three tables: `users → categories → transactions`. Users own both categories and transactions. Transactions optionally reference a category. Deleting a user cascades to all their data; deleting a category nulls the reference on its transactions.

## License

MIT
