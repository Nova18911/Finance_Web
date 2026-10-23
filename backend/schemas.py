from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class CategoryUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class ExpenseItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    categoryId: int
    isActive: bool = True


class ExpenseItemUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    categoryId: int
    isActive: bool


class TransactionCreate(BaseModel):
    date: date
    amount: Decimal = Field(gt=0)
    expenseItemId: int
    comment: str | None = None