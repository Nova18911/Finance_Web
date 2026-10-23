from decimal import Decimal

from flask import Blueprint, jsonify, request
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from pydantic import ValidationError

from backend.database import get_session
from backend.models import ExpenseItem, Transaction
from backend.schemas import TransactionCreate

transactions_bp = Blueprint(
    "transactions", __name__, url_prefix="/api/Transactions"
)

DAILY_LIMIT = Decimal("1000000")


def tx_to_dict(tx: Transaction) -> dict:
    return {
        "id": tx.id,
        "date": tx.date.isoformat(),
        "amount": float(tx.amount),
        "expenseItemId": tx.expense_item_id,
        "comment": tx.comment,
        "expenseItem": (
            {"id": tx.expense_item.id, "name": tx.expense_item.name}
            if tx.expense_item
            else None
        ),
    }


@transactions_bp.get("/byMonth/<int:year>/<int:month>")
def list_by_month(year: int, month: int):
    db = get_session()
    try:
        rows = db.scalars(
            select(Transaction)
            .options(joinedload(Transaction.expense_item))
            .where(
                func.extract("year", Transaction.date) == year,
                func.extract("month", Transaction.date) == month,
            )
            .order_by(Transaction.date.desc(), Transaction.id.desc())
        ).unique().all()
        return jsonify([tx_to_dict(t) for t in rows])
    finally:
        db.close()


@transactions_bp.post("")
def create_transaction():
    db = get_session()
    try:
        try:
            body = TransactionCreate.model_validate(request.get_json() or {})
        except ValidationError as e:
            return jsonify({"detail": e.errors()}), 400

        item = db.get(ExpenseItem, body.expenseItemId)
        if not item:
            return jsonify({"detail": "Статья расхода не найдена"}), 400
        if not item.is_active:
            return jsonify({"detail": "Статья расхода неактивна"}), 400

        day_sum = db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.date == body.date
            )
        )
        day_sum = Decimal(str(day_sum or 0))
        if day_sum + body.amount > DAILY_LIMIT:
            return jsonify(
                {"detail": "Превышен дневной лимит в 1 000 000 ₽"}
            ), 400

        tx = Transaction(
            date=body.date,
            amount=body.amount,
            expense_item_id=body.expenseItemId,
            comment=body.comment,
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)

        tx = db.scalars(
            select(Transaction)
            .options(joinedload(Transaction.expense_item))
            .where(Transaction.id == tx.id)
        ).unique().one()
        return jsonify(tx_to_dict(tx)), 201
    finally:
        db.close()


@transactions_bp.delete("/<int:tx_id>")
def delete_transaction(tx_id: int):
    db = get_session()
    try:
        tx = db.get(Transaction, tx_id)
        if not tx:
            return jsonify({"detail": "Транзакция не найдена"}), 404
        db.delete(tx)
        db.commit()
        return "", 204
    finally:
        db.close()