"""Receipt OCR + parsing.

Text extraction uses Tesseract (optional system dependency). Parsing is plain
Python so it can be unit-tested without Tesseract installed.
"""
import io
import re
from datetime import date

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

_AMOUNT = r"(?:rs\.?|inr|₹)?\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)"
_TOTAL_HINTS = ("grand total", "total amount", "amount due", "net amount", "total", "amount payable", "net payable")


def extract_text(image_bytes: bytes) -> str:
    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("OCR dependencies are not installed") from exc
    try:
        image = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(image)
    except pytesseract.TesseractNotFoundError as exc:  # pragma: no cover
        raise RuntimeError("Tesseract OCR engine is not installed on the server") from exc


def _to_float(raw: str) -> float | None:
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return None


def parse_amount(text: str) -> float | None:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for hint in _TOTAL_HINTS:
        for line in reversed(lines):
            low = line.lower()
            if hint in low and "sub" not in low.split(hint)[0][-4:]:
                matches = re.findall(_AMOUNT, low, flags=re.IGNORECASE)
                values = [v for v in (_to_float(m) for m in matches) if v is not None]
                if values:
                    return max(values)
    candidates = []
    for m in re.finditer(r"[0-9][0-9,]*\.[0-9]{2}", text):
        v = _to_float(m.group())
        if v is not None:
            candidates.append(v)
    return max(candidates) if candidates else None


def parse_date(text: str) -> date | None:
    m = re.search(r"\b(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})\b", text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    m = re.search(r"\b(\d{1,2})[-/.](\d{1,2})[-/.](20\d{2}|\d{2})\b", text)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        y = y + 2000 if y < 100 else y
        try:
            return date(y, mo, d)
        except ValueError:
            pass
    m = re.search(r"\b(\d{1,2})[\s-]([A-Za-z]{3})[a-z]*[\s,-]+(20\d{2})\b", text)
    if m and m.group(2).lower() in MONTHS:
        try:
            return date(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1)))
        except ValueError:
            pass
    return None


def parse_merchant(text: str) -> str | None:
    for line in text.splitlines():
        clean = line.strip()
        if len(clean) >= 3 and re.search(r"[A-Za-z]{3,}", clean):
            if re.search(r"invoice|receipt|bill|tax|gst|cash memo", clean, re.IGNORECASE) and len(clean) < 20:
                continue
            return clean[:80]
    return None


def parse_receipt_text(text: str) -> dict:
    return {
        "amount": parse_amount(text),
        "date": parse_date(text),
        "merchant": parse_merchant(text),
    }
