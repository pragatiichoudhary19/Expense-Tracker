from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..constants import CATEGORIES
from ..database import get_db
from ..deps import get_current_user
from ..schemas import BudgetIn, BudgetOut
from .expenses import month_bounds

router = APIRouter(prefix="/budgets", tags=["budgets"])


def budget_status(percent: float) -> str:
    if percent >= 100:
        return "exceeded"
    if percent >= 80:
        return "warning"
    return "ok"


async def budgets_with_spend(db: AsyncIOMotorDatabase, user_id, month: str) -> list[BudgetOut]:
    start, end = month_bounds(month)
    spent: dict[str, float] = {}
    async for row in db.expenses.aggregate([
        {"$match": {"user_id": user_id, "date": {"$gte": start, "$lt": end}}},
        {"$group": {"_id": "$category", "total": {"$sum": "$amount"}}},
    ]):
        spent[row["_id"]] = row["total"]

    out = []
    async for b in db.budgets.find({"user_id": user_id}).sort("category", 1):
        s = round(spent.get(b["category"], 0.0), 2)
        pct = round(s / b["limit"] * 100, 1) if b["limit"] else 0.0
        out.append(BudgetOut(category=b["category"], limit=b["limit"], spent=s, percent=pct, status=budget_status(pct)))
    return out


@router.get("", response_model=list[BudgetOut])
async def list_budgets(
    month: str | None = None,
    user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    month = month or datetime.now(timezone.utc).strftime("%Y-%m")
    return await budgets_with_spend(db, user["_id"], month)


@router.put("", response_model=list[BudgetOut])
async def upsert_budget(
    body: BudgetIn,
    user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    await db.budgets.update_one(
        {"user_id": user["_id"], "category": body.category},
        {"$set": {"limit": body.limit}},
        upsert=True,
    )
    return await budgets_with_spend(db, user["_id"], datetime.now(timezone.utc).strftime("%Y-%m"))


@router.delete("/{category}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    category: str,
    user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if category not in CATEGORIES:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown category")
    await db.budgets.delete_one({"user_id": user["_id"], "category": category})
    return Response(status_code=status.HTTP_204_NO_CONTENT)
