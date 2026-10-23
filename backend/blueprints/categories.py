from flask import Blueprint, jsonify, request
from sqlalchemy import select, func
from pydantic import ValidationError

from backend.database import get_session
from backend.models import Category, ExpenseItem, Transaction
from backend.schemas import CategoryCreate, CategoryUpdate

categories_bp = Blueprint("categories", __name__, url_prefix="/api/Categories")


def category_to_dict(c: Category) -> dict:
    return {"id": c.id, "name": c.name}


@categories_bp.get("")
def list_categories():
    db = get_session()
    try:
        rows = db.scalars(select(Category).order_by(Category.id)).all()
        return jsonify([category_to_dict(c) for c in rows])
    finally:
        db.close()


@categories_bp.post("")
def create_category():
    db = get_session()
    try:
        try:
            body = CategoryCreate.model_validate(request.get_json() or {})
        except ValidationError as e:
            return jsonify({"detail": e.errors()}), 400

        name = body.name.strip()
        exists = db.scalar(select(Category).where(Category.name == name))
        if exists:
            return jsonify({"detail": "Категория с таким именем уже есть"}), 400

        cat = Category(name=name)
        db.add(cat)
        db.commit()
        db.refresh(cat)
        return jsonify(category_to_dict(cat)), 201
    finally:
        db.close()


@categories_bp.put("/<int:category_id>")
def update_category(category_id: int):
    db = get_session()
    try:
        try:
            body = CategoryUpdate.model_validate(request.get_json() or {})
        except ValidationError as e:
            return jsonify({"detail": e.errors()}), 400

        cat = db.get(Category, category_id)
        if not cat:
            return jsonify({"detail": "Категория не найдена"}), 404

        cat.name = body.name.strip()
        db.commit()
        db.refresh(cat)
        return jsonify(category_to_dict(cat))
    finally:
        db.close()


@categories_bp.delete("/<int:category_id>")
def delete_category(category_id: int):
    db = get_session()
    try:
        cat = db.get(Category, category_id)
        if not cat:
            return jsonify({"detail": "Категория не найдена"}), 404

        tx_count = db.scalar(
            select(func.count(Transaction.id))
            .join(ExpenseItem, Transaction.expense_item_id == ExpenseItem.id)
            .where(ExpenseItem.category_id == category_id)
        )
        if tx_count and tx_count > 0:
            return jsonify(
                {"detail": "Нельзя удалить категорию: есть связанные транзакции"}
            ), 400

        db.delete(cat)
        db.commit()
        return "", 204
    finally:
        db.close()