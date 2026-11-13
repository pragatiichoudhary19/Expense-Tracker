"""Seed a demo account with ~90 days of realistic expenses.

Usage (from the backend folder):  python -m scripts.seed_demo
Login afterwards with demo@example.com / demo12345
"""
import asyncio
import random
from datetime import datetime, timedelta, timezone

from app.database import ensure_indexes, get_db
from app.security import hash_password
from app.services.categorizer import categorize

SAMPLES = [
    ("Swiggy", "Dinner order", 180, 450),
    ("Zomato", "Lunch", 150, 380),
    ("Starbucks", "Coffee", 220, 420),
    ("BigBasket", "Weekly groceries", 600, 1800),
    ("Blinkit", "Milk and fruit", 120, 450),
    ("Uber", "Cab to college", 90, 320),
    ("Rapido", "Bike taxi", 40, 120),
    ("Amazon", "Electronics accessory", 300, 2500),
    ("Myntra", "Clothes", 500, 2800),
    ("Jio", "Mobile recharge", 299, 299),
    ("Netflix", "Subscription", 199, 199),
    ("Apollo Pharmacy", "Medicines", 80, 600),
    ("Udemy", "Online course", 450, 650),
    ("IRCTC", "Train ticket", 350, 1400),
]


async def main() -> None:
    db = get_db()
    await ensure_indexes(db)
    await db.users.delete_many({"email": "demo@example.com"})
    result = await db.users.insert_one(
        {
            "name": "Demo User",
            "email": "demo@example.com",
            "password_hash": hash_password("demo12345"),
            "created_at": datetime.now(timezone.utc),
        }
    )
    user_id = result.inserted_id
    await db.expenses.delete_many({"user_id": user_id})
    await db.budgets.delete_many({"user_id": user_id})

    random.seed(7)
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    docs = []
    for offset in range(90):
        day = today - timedelta(days=offset)
        for _ in range(random.choice([0, 1, 1, 2, 3])):
            merchant, desc, low, high = random.choice(SAMPLES)
            category, _ = categorize(f"{merchant} {desc}")
            docs.append(
                {
                    "user_id": user_id,
                    "amount": float(random.randint(low, high)),
                    "description": desc,
                    "merchant": merchant,
                    "category": category,
                    "date": day,
                    "note": None,
                    "auto_categorized": True,
                    "created_at": datetime.now(timezone.utc),
                }
            )
    # A deliberate outlier so the anomaly detector has something to show.
    docs.append(
        {
            "user_id": user_id, "amount": 9800.0, "description": "Dinner party", "merchant": "Zomato",
            "category": "Food & Dining", "date": today - timedelta(days=2), "note": None,
            "auto_categorized": True, "created_at": datetime.now(timezone.utc),
        }
    )
    await db.expenses.insert_many(docs)
    await db.budgets.insert_many(
        [
            {"user_id": user_id, "category": "Food & Dining", "limit": 6000.0},
            {"user_id": user_id, "category": "Groceries", "limit": 5000.0},
            {"user_id": user_id, "category": "Shopping", "limit": 4000.0},
            {"user_id": user_id, "category": "Transport", "limit": 2500.0},
        ]
    )
    print(f"Seeded {len(docs)} expenses. Login: demo@example.com / demo12345")


if __name__ == "__main__":
    asyncio.run(main())
