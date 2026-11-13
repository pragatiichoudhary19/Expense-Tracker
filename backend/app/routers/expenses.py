import datetime as dt
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..constants import CATEGORIES
from ..database import get_db
from ..deps import get_current_user, to_object_id
from ..schemas import CategorizeIn, CategorizeOut, ExpenseIn, ExpenseList, ExpenseOut
from ..services.categorizer import categorize, normalize_merchant

router = APIRouter(prefix="/expenses", tags=["expenses"])


def month_bounds(month: str) -> tuple[datetime, datetime]:
    try:
        start = datetime.strptime(month, "%Y-%m")
    except ValueError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "month must be YYYY-MM")
    end = datetime(start.year + (start.month == 12), (start.month % 12) + 1, 1)
    return start, end


def to_out(doc: dict, confidence: float | None = None) -> ExpenseOut:
    return ExpenseOut(
        id=str(doc["_id"]),
        amount=doc["amount"],
        description=doc["description"],
        merchant=doc.get("merchant"),
        category=doc["category"],
        date=doc["date"].date(),
        note=doc.get("note"),
        auto_categorized=doc.get("auto_categorized", False),
        confidence=confidence,
    )


async def load_learned(db: AsyncIOMotorDatabase, user_id) -> dict[str, str]:
    rules = db.merchant_rules.find({"user_id": user_id})
    return {r["merchant"]: r["category"] async for r in rules}


async def remember_merchant(db: AsyncIOMotorDatabase, user_id, merchant: str | None, category: str) -> None:
    key = normalize_merchant(merchant or "")
    if not key:
        return
    await db.merchant_rules.update_one(
        {"user_id": user_id, "merchant": key},
        {"$set": {"category": category}},
        upsert=True,
    )


@router.post("/categorize", response_model=CategorizeOut)
async def suggest_category(
    body: CategorizeIn,
    user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    learned = await load_learned(db, user["_id"])
    category, confidence = categorize(body.text, learned)
    return CategorizeOut(category=category, confidence=round(confidence, 2))


@router.get("/categories", response_model=list[str])
async def list_categories():
    return CATEGORIES


@router.post("", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
async def create_expense(
    body: ExpenseIn,
    user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    category, confidence, auto = body.category, None, False
    if not category:
        learned = await load_learned(db, user["_id"])
        category, confidence = categorize(f"{body.merchant or ''} {body.description}", learned)
        auto = True

    doc = {
        "user_id": user["_id"],
        "amount": round(body.amount, 2),
        "description": body.description.strip(),
        "merchant": body.merchant.strip() if body.merchant else None,
        "category": category,
        "date": datetime.combine(body.date, dt.time.min),
        "note": body.note,
        "auto_categorized": auto,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.expenses.insert_one(doc)
    doc["_id"] = result.inserted_id
    if not auto:
        await remember_merchant(db, user["_id"], body.merchant, category)
    return to_out(doc, round(confidence, 2) if confidence is not None else None)


@router.get("", response_model=ExpenseList)
async def list_expenses(
    month: str | None = Query(default=None, description="YYYY-MM"),
    category: str | None = None,
    q: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    query: dict = {"user_id": user["_id"]}
    if month:
        start, end = month_bounds(month)
        query["date"] = {"$gte": start, "$lt": end}
    if category:
        query["category"] = category
    if q:
        pattern = {"$regex": re.escape(q), "$options": "i"}
        query["$or"] = [{"description": pattern}, {"merchant": pattern}]

    total = await db.expenses.count_documents(query)
    cursor = db.expenses.find(query).sort([("date", -1), ("created_at", -1)]).skip(skip).limit(limit)
    items = [to_out(d) async for d in cursor]
    return ExpenseList(items=items, total=total)


@router.put("/{expense_id}", response_model=ExpenseOut)
async def update_expense(
    expense_id: str,
    body: ExpenseIn,
    user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    oid = to_object_id(expense_id)
    existing = await db.expenses.find_one({"_id": oid, "user_id": user["_id"]})
    if not existing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Expense not found")

    category = body.category or existing["category"]
    updates = {
        "amount": round(body.amount, 2),
        "description": body.description.strip(),
        "merchant": body.merchant.strip() if body.merchant else None,
        "category": category,
        "date": datetime.combine(body.date, dt.time.min),
        "note": body.note,
        "auto_categorized": False,
    }
    await db.expenses.update_one({"_id": oid}, {"$set": updates})
    if body.category and body.category != existing["category"]:
        # The user corrected the category: learn it for this merchant.
        await remember_merchant(db, user["_id"], body.merchant, body.category)
    return to_out({**existing, **updates})


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    result = await db.expenses.delete_one({"_id": to_object_id(expense_id), "user_id": user["_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Expense not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
