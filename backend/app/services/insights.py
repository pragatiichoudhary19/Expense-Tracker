"""Rule-based natural-language insights generated from computed analytics."""


def _fmt(amount: float) -> str:
    return f"₹{amount:,.0f}"


def build_insights(
    total: float,
    prev_total: float,
    by_category: list[dict],
    budgets: list[dict],
    forecast: dict | None,
) -> list[str]:
    insights: list[str] = []

    if total == 0:
        return ["No expenses recorded for this month yet. Add one to see insights."]

    if prev_total > 0:
        change = (total - prev_total) / prev_total * 100
        direction = "more" if change > 0 else "less"
        if abs(change) >= 5:
            insights.append(
                f"You've spent {_fmt(total)} so far, {abs(change):.0f}% {direction} than the whole of last month ({_fmt(prev_total)})."
            )

    if by_category:
        top = by_category[0]
        insights.append(
            f"{top['category']} is your biggest category at {top['percent']:.0f}% of spending ({_fmt(top['total'])})."
        )

    for b in budgets:
        if b["percent"] >= 100:
            insights.append(f"You've exceeded your {b['category']} budget by {_fmt(b['spent'] - b['limit'])}.")
        elif b["percent"] >= 80:
            insights.append(
                f"{b['category']} budget is {b['percent']:.0f}% used - {_fmt(b['limit'] - b['spent'])} left."
            )

    if forecast and forecast["days_remaining"] > 0:
        insights.append(
            f"At your current pace you'll spend about {_fmt(forecast['projected_total'])} by month end."
        )
        total_limit = sum(b["limit"] for b in budgets)
        if total_limit and forecast["projected_total"] > total_limit:
            insights.append(
                f"That is {_fmt(forecast['projected_total'] - total_limit)} over your combined budgets of {_fmt(total_limit)}."
            )

    return insights
