from datetime import date

from app.security import create_access_token, decode_access_token, hash_password, verify_password
from app.services.categorizer import categorize
from app.services.forecast import detect_anomalies, project_month_end
from app.services.insights import build_insights
from app.services.ocr import parse_amount, parse_date, parse_receipt_text


# --- categorizer -----------------------------------------------------------
def test_keyword_categorization():
    assert categorize("Swiggy dinner order")[0] == "Food & Dining"
    assert categorize("Uber ride to office")[0] == "Transport"
    assert categorize("Netflix subscription")[0] == "Entertainment"


def test_unknown_text_falls_back_to_other():
    cat, conf = categorize("xyzzy qwerty")
    assert cat == "Other"
    assert conf < 0.5


def test_learned_merchant_overrides_keywords():
    cat, conf = categorize("Swiggy Instamart", learned={"swiggy": "Groceries"})
    assert cat == "Groceries"
    assert conf == 0.95


def test_empty_text():
    assert categorize("   ") == ("Other", 0.0)


# --- forecast --------------------------------------------------------------
def test_projection_with_constant_spend():
    daily = {d: 100.0 for d in range(1, 11)}
    result = project_month_end(daily, today=10, days_in_month=30)
    assert result["spent_so_far"] == 1000.0
    assert result["projected_total"] == 3000.0
    assert result["days_remaining"] == 20


def test_projection_reacts_to_recent_spike():
    daily = {d: 50.0 for d in range(1, 8)}
    daily.update({d: 500.0 for d in range(8, 11)})
    result = project_month_end(daily, today=10, days_in_month=30)
    steady = project_month_end({d: 50.0 for d in range(1, 11)}, today=10, days_in_month=30)
    assert result["projected_total"] > steady["projected_total"]


def test_anomaly_detection_flags_outlier():
    expenses = [{"id": str(i), "category": "Food & Dining", "amount": 200.0} for i in range(10)]
    expenses.append({"id": "big", "category": "Food & Dining", "amount": 5000.0})
    flagged = detect_anomalies(expenses)
    assert [f["id"] for f in flagged] == ["big"]


def test_anomaly_needs_enough_samples():
    expenses = [{"id": "1", "category": "Travel", "amount": 100.0}, {"id": "2", "category": "Travel", "amount": 9000.0}]
    assert detect_anomalies(expenses) == []


# --- OCR parsing -----------------------------------------------------------
RECEIPT = """Big Bazaar Hypermarket
Invoice
Date: 12/03/2026
Milk            60.00
Bread           45.50
Subtotal       105.50
GST             5.28
Grand Total    1,110.78
"""


def test_parse_amount_prefers_total_line():
    assert parse_amount(RECEIPT) == 1110.78


def test_parse_date_formats():
    assert parse_date("Date: 12/03/2026") == date(2026, 3, 12)
    assert parse_date("2026-11-05") == date(2026, 11, 5)
    assert parse_date("5 Nov 2026") == date(2026, 11, 5)
    assert parse_date("no date here") is None


def test_parse_receipt_text_merchant():
    parsed = parse_receipt_text(RECEIPT)
    assert parsed["merchant"] == "Big Bazaar Hypermarket"
    assert parsed["date"] == date(2026, 3, 12)


# --- insights --------------------------------------------------------------
def test_insights_empty_month():
    assert "No expenses" in build_insights(0, 0, [], [], None)[0]


def test_insights_budget_and_forecast():
    insights = build_insights(
        total=5000,
        prev_total=4000,
        by_category=[{"category": "Shopping", "total": 3000, "percent": 60}],
        budgets=[{"category": "Shopping", "limit": 2500, "spent": 3000, "percent": 120}],
        forecast={"projected_total": 9000, "days_remaining": 10},
    )
    text = " ".join(insights)
    assert "exceeded your Shopping budget" in text
    assert "month end" in text
    assert "over your combined budgets" in text


# --- security --------------------------------------------------------------
def test_password_hash_roundtrip():
    hashed = hash_password("correct horse")
    assert verify_password("correct horse", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_roundtrip_and_expiry():
    token = create_access_token("user-123")
    assert decode_access_token(token) == "user-123"
    assert decode_access_token(create_access_token("user-123", expires_minutes=-1)) is None
    assert decode_access_token("garbage") is None
