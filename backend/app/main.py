from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import ensure_indexes, get_db
from .routers import analytics, auth, budgets, expenses, receipts


@asynccontextmanager
async def lifespan(_: FastAPI):
    await ensure_indexes(get_db())
    yield


app = FastAPI(
    title="AI Expense & Budget Tracker API",
    version="1.0.0",
    description="Expense tracking with auto-categorization, receipt OCR, budgets, forecasting and insights.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth.router, expenses.router, budgets.router, analytics.router, receipts.router):
    app.include_router(r, prefix="/api")


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok"}
