from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from backend.connect import get_db_connection
from backend.schemas import CategoryCreate, CategoryUpdate

categories_bp = Blueprint("categories", __name__, url_prefix="/api/Categories")


@categories_bp.get("")
def list_categories():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM categories ORDER BY id")
        rows = cursor.fetchall()

        return jsonify([
            {"id": row[0], "name": row[1]}
            for row in rows
        ])
    finally:
        conn.close()


@categories_bp.post("")
def create_category():
    try:
        body = CategoryCreate.model_validate(request.get_json() or {})
    except ValidationError as e:
        return jsonify({"detail": e.errors()}), 400

    name = body.name.strip()

    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM categories WHERE name = %s",
            (name,)
        )
        if cursor.fetchone():
            return jsonify({"detail": "Категория с таким именем уже есть"}), 400

        cursor.execute(
            "INSERT INTO categories (name) VALUES (%s) RETURNING id",
            (name,)
        )
        category_id = cursor.fetchone()[0]
        conn.commit()

        return jsonify({"id": category_id, "name": name}), 201
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@categories_bp.put("/<int:category_id>")
def update_category(category_id: int):
    try:
        body = CategoryUpdate.model_validate(request.get_json() or {})
    except ValidationError as e:
        return jsonify({"detail": e.errors()}), 400

    name = body.name.strip()

    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM categories WHERE id = %s",
            (category_id,)
        )
        if not cursor.fetchone():
            return jsonify({"detail": "Категория не найдена"}), 404

        cursor.execute(
            """
            UPDATE categories
            SET name = %s
            WHERE id = %s
            """,
            (name, category_id)
        )
        conn.commit()

        return jsonify({"id": category_id, "name": name})
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@categories_bp.delete("/<int:category_id>")
def delete_category(category_id: int):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM categories WHERE id = %s",
            (category_id,)
        )
        if not cursor.fetchone():
            return jsonify({"detail": "Категория не найдена"}), 404

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM transactions t
            JOIN expense_items ei ON t.expense_item_id = ei.id
            WHERE ei.category_id = %s
            """,
            (category_id,)
        )
        tx_count = cursor.fetchone()[0]

        if tx_count > 0:
            return jsonify({
                "detail": "Нельзя удалить категорию: есть связанные транзакции"
            }), 400

        cursor.execute(
            "DELETE FROM categories WHERE id = %s",
            (category_id,)
        )
        conn.commit()

        return "", 204
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()