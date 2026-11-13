from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from .config import get_settings

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(get_settings().mongodb_url)
    return _client


def get_db() -> AsyncIOMotorDatabase:
    return get_client()[get_settings().db_name]


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    await db.users.create_index("email", unique=True)
    await db.expenses.create_index([("user_id", 1), ("date", -1)])
    await db.expenses.create_index([("user_id", 1), ("category", 1)])
    await db.budgets.create_index([("user_id", 1), ("category", 1)], unique=True)
    await db.merchant_rules.create_index([("user_id", 1), ("merchant", 1)], unique=True)
