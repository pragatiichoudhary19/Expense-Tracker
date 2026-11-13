"""Hybrid expense categorizer.

1. Per-user learned merchant rules (highest confidence) - improves as the user corrects categories.
2. Keyword scoring across a curated vocabulary (works with zero training data).
"""
import re

KEYWORDS: dict[str, list[str]] = {
    "Food & Dining": [
        "restaurant", "cafe", "coffee", "swiggy", "zomato", "dominos", "pizza", "burger", "kfc",
        "mcdonald", "starbucks", "biryani", "lunch", "dinner", "breakfast", "snack", "chai",
        "canteen", "mess", "bakery", "dhaba", "food",
    ],
    "Groceries": [
        "grocery", "supermarket", "bigbasket", "blinkit", "zepto", "dmart", "vegetable", "fruit",
        "milk", "kirana", "reliance fresh", "instamart", "provision",
    ],
    "Transport": [
        "uber", "ola", "rapido", "metro", "bus", "auto", "fuel", "petrol", "diesel", "cab",
        "taxi", "parking", "toll", "fastag",
    ],
    "Shopping": [
        "amazon", "flipkart", "myntra", "ajio", "meesho", "mall", "clothes", "shoes", "shirt",
        "electronics", "store", "fashion",
    ],
    "Bills & Utilities": [
        "electricity", "water bill", "wifi", "broadband", "jio", "airtel", "vi recharge",
        "recharge", "rent", "gas", "bill", "insurance", "emi", "subscription fee",
    ],
    "Entertainment": [
        "netflix", "prime video", "hotstar", "spotify", "movie", "cinema", "pvr", "inox",
        "game", "steam", "concert", "youtube premium", "bookmyshow",
    ],
    "Health": [
        "pharmacy", "medical", "medicine", "doctor", "hospital", "clinic", "apollo", "gym",
        "diagnostic", "lab test", "dental", "1mg", "pharmeasy",
    ],
    "Education": [
        "course", "udemy", "coursera", "tuition", "book", "stationery", "college", "fees",
        "exam", "library", "notebook", "certification",
    ],
    "Travel": [
        "flight", "hotel", "irctc", "train", "makemytrip", "goibibo", "airbnb", "booking",
        "resort", "trip", "hostel", "indigo", "visa",
    ],
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", text.lower())).strip()


def normalize_merchant(merchant: str) -> str:
    return _normalize(merchant)


def categorize(text: str, learned: dict[str, str] | None = None) -> tuple[str, float]:
    """Return (category, confidence in [0, 1])."""
    norm = _normalize(text)
    if not norm:
        return "Other", 0.0

    if learned:
        for merchant, category in learned.items():
            if merchant and merchant in norm:
                return category, 0.95

    best_cat, best_hits = "Other", 0
    for category, words in KEYWORDS.items():
        hits = sum(1 for w in words if re.search(rf"\b{re.escape(w)}\b", norm))
        if hits > best_hits:
            best_cat, best_hits = category, hits

    if best_hits == 0:
        return "Other", 0.2
    return best_cat, min(0.9, 0.55 + 0.15 * best_hits)
