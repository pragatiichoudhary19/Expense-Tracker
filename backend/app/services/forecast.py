"""Spending forecast and anomaly detection (pure Python, no heavy dependencies)."""
from statistics import mean, pstdev


def project_month_end(
    daily_totals: dict[int, float], today: int, days_in_month: int
) -> dict:
    """Project month-end spend.

    Blends the month-to-date daily average with the recent 7-day average so the
    forecast reacts to changes in spending pace.
    """
    today = max(1, min(today, days_in_month))
    spent = sum(v for d, v in daily_totals.items() if d <= today)
    month_avg = spent / today

    recent_days = range(max(1, today - 6), today + 1)
    recent_avg = sum(daily_totals.get(d, 0.0) for d in recent_days) / len(recent_days)

    blended = 0.6 * recent_avg + 0.4 * month_avg
    remaining = days_in_month - today
    projected = spent + blended * remaining
    return {
        "spent_so_far": round(spent, 2),
        "daily_average": round(month_avg, 2),
        "recent_daily_average": round(recent_avg, 2),
        "projected_total": round(projected, 2),
        "days_remaining": remaining,
    }


def detect_anomalies(
    expenses: list[dict], min_samples: int = 5, z_threshold: float = 2.0
) -> list[dict]:
    """Flag expenses far above the typical amount for their category.

    Each expense dict needs: id, category, amount.
    """
    by_cat: dict[str, list[float]] = {}
    for e in expenses:
        by_cat.setdefault(e["category"], []).append(e["amount"])

    stats = {
        cat: (mean(vals), pstdev(vals))
        for cat, vals in by_cat.items()
        if len(vals) >= min_samples
    }

    flagged = []
    for e in expenses:
        if e["category"] not in stats:
            continue
        mu, sigma = stats[e["category"]]
        if sigma == 0:
            continue
        z = (e["amount"] - mu) / sigma
        if z >= z_threshold:
            flagged.append({**e, "z_score": round(z, 2), "typical": round(mu, 2)})
    return sorted(flagged, key=lambda x: x["z_score"], reverse=True)
