from decimal import Decimal

from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from backend.connect import get_db_connection
from backend.schemas import TransactionCreate

transactions_bp = Blueprint(
    "transactions", __name__, url_prefix="/api/Transactions"
)

DAILY_LIMIT = Decimal("1000000")


def tx_to_dict(row):
    return {
        "id": row[0],
        "date": row[1].isoformat(),
        "amount": float(row[2]),
        "expenseItemId": row[3],
        "comment": row[4],
        "expenseItem": {
            "id": row[5],
            "name": row[6]
        } if row[5] is not None else None
    }


@transactions_bp.get("/byMonth/<int:year>/<int:month>")
def list_by_month(year: int, month: int):
    if month < 1 or month > 12:
        return jsonify({"detail": "Некорректный номер месяца"}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT t.id, t.date, t.amount, t.expense_item_id,
                   t.comment, ei.id, ei.name
            FROM transactions t
            LEFT JOIN expense_items ei ON t.expense_item_id = ei.id
            WHERE EXTRACT(YEAR FROM t.date) = %s
              AND EXTRACT(MONTH FROM t.date) = %s
            ORDER BY t.date DESC, t.id DESC
            """,
            (year, month)
        )
        rows = cursor.fetchall()

        return jsonify([tx_to_dict(row) for row in rows])
    finally:
        conn.close()


@transactions_bp.post("")
def create_transaction():
    try:
        body = TransactionCreate.model_validate(request.get_json() or {})
    except ValidationError as e:
        return jsonify({"detail": e.errors()}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, is_active
            FROM expense_items
            WHERE id = %s
            """,
            (body.expenseItemId,)
        )
        item = cursor.fetchone()

        if not item:
            return jsonify({"detail": "Статья расхода не найдена"}), 400

        if not item[1]:
            return jsonify({"detail": "Статья расхода неактивна"}), 400

        cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0)
            FROM transactions
            WHERE date = %s
            """,
            (body.date,)
        )
        day_sum = Decimal(str(cursor.fetchone()[0] or 0))

        if day_sum + body.amount > DAILY_LIMIT:
            return jsonify({
                "detail": "Превышен дневной лимит в 1 000 000 ₽"
            }), 400

        cursor.execute(
            """
            INSERT INTO transactions (date, amount, expense_item_id, comment)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (body.date, body.amount, body.expenseItemId, body.comment)
        )
        tx_id = cursor.fetchone()[0]
        conn.commit()

        cursor.execute(
            """
            SELECT t.id, t.date, t.amount, t.expense_item_id,
                   t.comment, ei.id, ei.name
            FROM transactions t
            LEFT JOIN expense_items ei ON t.expense_item_id = ei.id
            WHERE t.id = %s
            """,
            (tx_id,)
        )
        row = cursor.fetchone()

        return jsonify(tx_to_dict(row)), 201
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@transactions_bp.delete("/<int:tx_id>")
def delete_transaction(tx_id: int):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM transactions WHERE id = %s",
            (tx_id,)
        )
        if not cursor.fetchone():
            return jsonify({"detail": "Транзакция не найдена"}), 404

        cursor.execute(
            "DELETE FROM transactions WHERE id = %s",
            (tx_id,)
        )
        conn.commit()

        return "", 204
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()