# Spendwise: AI Expense & Budget Tracker

A full-stack expense tracker with smart automation: expenses categorize themselves, receipts scan into entries, and a dashboard forecasts your month-end spend.

**Stack:** React 18 + Vite + Recharts · FastAPI · MongoDB (Motor, async) · JWT auth · Tesseract OCR · Docker

## Features

| Feature | How it works |
|---|---|
| **Auto-categorization** | Keyword-scoring classifier plus per-user learned merchant rules. When you correct a category, the app remembers it for that merchant (confidence 95%). |
| **Receipt scanning** | Upload a photo, Tesseract extracts text, a parser pulls the total (prefers "Grand Total" lines), date (several formats) and merchant. |
| **Budgets** | Monthly per-category limits with ok / warning (80%) / exceeded states. |
| **Month-end forecast** | Blends month-to-date and last-7-day daily averages, so it reacts to changes in spending pace. |
| **Anomaly detection** | Flags expenses with a z-score of 2 or more within their category (needs 5+ samples). |
| **Plain-English insights** | Month-over-month change, top category, budget alerts, projected overspend. |
| **Auth & isolation** | bcrypt password hashing, JWT bearer tokens, every query scoped to the signed-in user. |

## Architecture

```
React SPA ──/api──▶ FastAPI ──▶ MongoDB
                      │
                      ├─ routers/   auth, expenses, budgets, analytics, receipts
                      └─ services/  categorizer, forecast, ocr, insights   (pure Python, unit-tested)
```

Business logic lives in `services/` with no database or HTTP dependency, so it is fast to unit test.

## Run locally

**Prerequisites:** Python 3.11+, Node 20+, MongoDB running on `localhost:27017`, and (optional, for receipt scanning) the Tesseract engine (`sudo apt install tesseract-ocr` or `brew install tesseract`).

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m scripts.seed_demo        # optional: demo data, login demo@example.com / demo12345
uvicorn app.main:app --reload      # http://localhost:8000/docs

# Frontend (new terminal)
cd frontend
npm install
npm run dev                        # http://localhost:5173
```

## Run with Docker

```bash
JWT_SECRET=$(openssl rand -hex 32) docker compose up --build
# App: http://localhost:8080   API docs: http://localhost:8000/docs
```

## Tests

```bash
cd backend && pytest
```

Covers the categorizer, forecast, anomaly detection, OCR parsing, insights and auth/JWT utilities.

## API overview

`POST /api/auth/register` · `POST /api/auth/login` · `GET /api/auth/me`
`GET|POST /api/expenses` · `PUT|DELETE /api/expenses/{id}` · `POST /api/expenses/categorize`
`GET|PUT /api/budgets` · `DELETE /api/budgets/{category}`
`GET /api/analytics/summary?month=YYYY-MM`
`POST /api/receipts/scan`

## Roadmap

- Recurring expenses and CSV import/export
- Replace the keyword classifier with a trained model (scikit-learn TF-IDF + logistic regression) once enough labelled data exists
- Multi-currency support
