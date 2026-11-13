import datetime as dt

from pydantic import BaseModel, EmailStr, Field, field_validator

from .constants import CATEGORIES


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ExpenseIn(BaseModel):
    amount: float = Field(gt=0, le=10_000_000)
    description: str = Field(min_length=1, max_length=200)
    merchant: str | None = Field(default=None, max_length=100)
    category: str | None = None
    date: dt.date
    note: str | None = Field(default=None, max_length=500)

    @field_validator("category")
    @classmethod
    def valid_category(cls, v: str | None) -> str | None:
        if v is not None and v not in CATEGORIES:
            raise ValueError(f"category must be one of {CATEGORIES}")
        return v


class ExpenseOut(BaseModel):
    id: str
    amount: float
    description: str
    merchant: str | None = None
    category: str
    date: dt.date
    note: str | None = None
    auto_categorized: bool = False
    confidence: float | None = None


class ExpenseList(BaseModel):
    items: list[ExpenseOut]
    total: int


class CategorizeIn(BaseModel):
    text: str = Field(min_length=1, max_length=300)


class CategorizeOut(BaseModel):
    category: str
    confidence: float


class BudgetIn(BaseModel):
    category: str
    limit: float = Field(gt=0, le=100_000_000)

    @field_validator("category")
    @classmethod
    def valid_category(cls, v: str) -> str:
        if v not in CATEGORIES:
            raise ValueError(f"category must be one of {CATEGORIES}")
        return v


class BudgetOut(BaseModel):
    category: str
    limit: float
    spent: float
    percent: float
    status: str  # ok | warning | exceeded


class ReceiptScanOut(BaseModel):
    amount: float | None
    date: dt.date | None
    merchant: str | None
    category: str
    confidence: float
    raw_text: str
