from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..database import get_db
from ..deps import get_current_user
from ..schemas import ReceiptScanOut
from ..services.categorizer import categorize
from ..services.ocr import extract_text, parse_receipt_text
from .expenses import load_learned

router = APIRouter(prefix="/receipts", tags=["receipts"])

MAX_BYTES = 8 * 1024 * 1024
ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp"}


@router.post("/scan", response_model=ReceiptScanOut)
async def scan_receipt(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Upload a PNG, JPEG or WebP image")
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Image must be under 8 MB")

    try:
        text = extract_text(data)
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
    except Exception:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Could not read that image")

    parsed = parse_receipt_text(text)
    learned = await load_learned(db, user["_id"])
    category, confidence = categorize(f"{parsed['merchant'] or ''} {text[:300]}", learned)
    return ReceiptScanOut(
        amount=parsed["amount"],
        date=parsed["date"],
        merchant=parsed["merchant"],
        category=category,
        confidence=round(confidence, 2),
        raw_text=text[:2000],
    )
