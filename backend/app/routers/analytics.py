import calendar
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..database import get_db
from ..deps import get_current_user
from ..services.forecast import detect_anomalies, project_month_end
from ..services.insights import build_insights
from .budgets import budgets_with_spend
from .expenses import month_bounds

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
async def summary(
    month: str | None = None,
    user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    month = month or now.strftime("%Y-%m")
    start, end = month_bounds(month)
    prev_start, _ = month_bounds((start - timedelta(days=1)).strftime("%Y-%m"))
    days_in_month = calendar.monthrange(start.year, start.month)[1]

    history_start = min(prev_start, start - timedelta(days=90))
    docs = [
        d async for d in db.expenses.find(
            {"user_id": user["_id"], "date": {"$gte": history_start, "$lt": end}}
        )
    ]
    current = [d for d in docs if start <= d["date"] < end]
    previous = [d for d in docs if prev_start <= d["date"] < start]

    total = round(sum(d["amount"] for d in current), 2)
    prev_total = round(sum(d["amount"] for d in previous), 2)

    cat_totals: dict[str, float] = {}
    merchant_totals: dict[str, float] = {}
    daily: dict[int, float] = {}
    for d in current:
        cat_totals[d["category"]] = cat_totals.get(d["category"], 0.0) + d["amount"]
        if d.get("merchant"):
            merchant_totals[d["merchant"]] = merchant_totals.get(d["merchant"], 0.0) + d["amount"]
        daily[d["date"].day] = daily.get(d["date"].day, 0.0) + d["amount"]

    by_category = sorted(
        (
            {"category": c, "total": round(v, 2), "percent": round(v / total * 100, 1) if total else 0.0}
            for c, v in cat_totals.items()
        ),
        key=lambda x: x["total"],
        reverse=True,
    )
    top_merchants = sorted(
        ({"merchant": m, "total": round(v, 2)} for m, v in merchant_totals.items()),
        key=lambda x: x["total"],
        reverse=True,
    )[:5]

    running = 0.0
    daily_series = []
    for day in range(1, days_in_month + 1):
        running += daily.get(day, 0.0)
        daily_series.append({"day": day, "total": round(daily.get(day, 0.0), 2), "cumulative": round(running, 2)})

    is_current_month = start.year == now.year and start.month == now.month
    forecast = project_month_end(daily, now.day, days_in_month) if is_current_month else None

    budgets = [b.model_dump() for b in await budgets_with_spend(db, user["_id"], month)]

    anomalies = detect_anomalies(
        [
            {
                "id": str(d["_id"]),
                "category": d["category"],
                "amount": d["amount"],
                "description": d["description"],
                "date": d["date"].date().isoformat(),
            }
            for d in docs
        ]
    )
    anomalies = [a for a in anomalies if a["date"] >= start.date().isoformat()][:5]

    return {
        "month": month,
        "total": total,
        "previous_total": prev_total,
        "change_percent": round((total - prev_total) / prev_total * 100, 1) if prev_total else None,
        "transaction_count": len(current),
        "by_category": by_category,
        "daily": daily_series,
        "top_merchants": top_merchants,
        "budgets": budgets,
        "forecast": forecast,
        "anomalies": anomalies,
        "insights": build_insights(total, prev_total, by_category, budgets, forecast),
    }
