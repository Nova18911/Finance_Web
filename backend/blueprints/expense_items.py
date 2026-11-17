from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from backend.connect import get_db_connection
from backend.schemas import ExpenseItemCreate, ExpenseItemUpdate

expense_items_bp = Blueprint(
    "expense_items", __name__, url_prefix="/api/ExpenseItems"
)


def item_to_dict(row):
    return {
        "id": row[0],
        "name": row[1],
        "categoryId": row[2],
        "isActive": row[3],
        "category": {
            "id": row[4],
            "name": row[5]
        } if row[4] is not None else None
    }


@expense_items_bp.get("")
def list_items():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT ei.id, ei.name, ei.category_id, ei.is_active,
                   c.id, c.name
            FROM expense_items ei
            LEFT JOIN categories c ON ei.category_id = c.id
            ORDER BY ei.id
            """
        )
        rows = cursor.fetchall()

        return jsonify([item_to_dict(row) for row in rows])
    finally:
        conn.close()


@expense_items_bp.post("")
def create_item():
    try:
        body = ExpenseItemCreate.model_validate(request.get_json() or {})
    except ValidationError as e:
        return jsonify({"detail": e.errors()}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM categories WHERE id = %s",
            (body.categoryId,)
        )
        if not cursor.fetchone():
            return jsonify({"detail": "Категория не найдена"}), 400

        cursor.execute(
            """
            INSERT INTO expense_items (name, category_id, is_active)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (body.name.strip(), body.categoryId, body.isActive)
        )
        item_id = cursor.fetchone()[0]
        conn.commit()

        cursor.execute(
            """
            SELECT ei.id, ei.name, ei.category_id, ei.is_active,
                   c.id, c.name
            FROM expense_items ei
            LEFT JOIN categories c ON ei.category_id = c.id
            WHERE ei.id = %s
            """,
            (item_id,)
        )
        row = cursor.fetchone()

        return jsonify(item_to_dict(row)), 201
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@expense_items_bp.put("/<int:item_id>")
def update_item(item_id: int):
    try:
        body = ExpenseItemUpdate.model_validate(request.get_json() or {})
    except ValidationError as e:
        return jsonify({"detail": e.errors()}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM expense_items WHERE id = %s",
            (item_id,)
        )
        if not cursor.fetchone():
            return jsonify({"detail": "Статья не найдена"}), 404

        cursor.execute(
            "SELECT id FROM categories WHERE id = %s",
            (body.categoryId,)
        )
        if not cursor.fetchone():
            return jsonify({"detail": "Категория не найдена"}), 400

        cursor.execute(
            """
            UPDATE expense_items
            SET name = %s, category_id = %s, is_active = %s
            WHERE id = %s
            """,
            (body.name.strip(), body.categoryId, body.isActive, item_id)
        )
        conn.commit()

        cursor.execute(
            """
            SELECT ei.id, ei.name, ei.category_id, ei.is_active,
                   c.id, c.name
            FROM expense_items ei
            LEFT JOIN categories c ON ei.category_id = c.id
            WHERE ei.id = %s
            """,
            (item_id,)
        )
        row = cursor.fetchone()

        return jsonify(item_to_dict(row))
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@expense_items_bp.delete("/<int:item_id>")
def delete_item(item_id: int):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM expense_items WHERE id = %s",
            (item_id,)
        )
        if not cursor.fetchone():
            return jsonify({"detail": "Статья не найдена"}), 404

        cursor.execute(
            "SELECT COUNT(*) FROM transactions WHERE expense_item_id = %s",
            (item_id,)
        )
        tx_count = cursor.fetchone()[0]

        if tx_count > 0:
            return jsonify({
                "detail": "Нельзя удалить статью: есть связанные транзакции"
            }), 400

        cursor.execute(
            "DELETE FROM expense_items WHERE id = %s",
            (item_id,)
        )
        conn.commit()

        return "", 204
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()