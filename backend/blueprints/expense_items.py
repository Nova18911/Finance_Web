from flask import Blueprint, jsonify, request
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from pydantic import ValidationError

from backend.database import get_session
from backend.models import Category, ExpenseItem, Transaction
from backend.schemas import ExpenseItemCreate, ExpenseItemUpdate

expense_items_bp = Blueprint(
    "expense_items", __name__, url_prefix="/api/ExpenseItems"
)


def item_to_dict(it: ExpenseItem) -> dict:
    return {
        "id": it.id,
        "name": it.name,
        "categoryId": it.category_id,
        "isActive": it.is_active,
        "category": (
            {"id": it.category.id, "name": it.category.name}
            if it.category
            else None
        ),
    }


@expense_items_bp.get("")
def list_items():
    db = get_session()
    try:
        rows = db.scalars(
            select(ExpenseItem)
            .options(joinedload(ExpenseItem.category))
            .order_by(ExpenseItem.id)
        ).unique().all()
        return jsonify([item_to_dict(i) for i in rows])
    finally:
        db.close()


@expense_items_bp.post("")
def create_item():
    db = get_session()
    try:
        try:
            body = ExpenseItemCreate.model_validate(request.get_json() or {})
        except ValidationError as e:
            return jsonify({"detail": e.errors()}), 400

        cat = db.get(Category, body.categoryId)
        if not cat:
            return jsonify({"detail": "Категория не найдена"}), 400

        item = ExpenseItem(
            name=body.name.strip(),
            category_id=body.categoryId,
            is_active=body.isActive,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        # подгрузить category
        item = db.scalars(
            select(ExpenseItem)
            .options(joinedload(ExpenseItem.category))
            .where(ExpenseItem.id == item.id)
        ).unique().one()
        return jsonify(item_to_dict(item)), 201
    finally:
        db.close()


@expense_items_bp.put("/<int:item_id>")
def update_item(item_id: int):
    db = get_session()
    try:
        try:
            body = ExpenseItemUpdate.model_validate(request.get_json() or {})
        except ValidationError as e:
            return jsonify({"detail": e.errors()}), 400

        item = db.get(ExpenseItem, item_id)
        if not item:
            return jsonify({"detail": "Статья не найдена"}), 404

        cat = db.get(Category, body.categoryId)
        if not cat:
            return jsonify({"detail": "Категория не найдена"}), 400

        item.name = body.name.strip()
        item.category_id = body.categoryId
        item.is_active = body.isActive
        db.commit()

        item = db.scalars(
            select(ExpenseItem)
            .options(joinedload(ExpenseItem.category))
            .where(ExpenseItem.id == item_id)
        ).unique().one()
        return jsonify(item_to_dict(item))
    finally:
        db.close()


@expense_items_bp.delete("/<int:item_id>")
def delete_item(item_id: int):
    db = get_session()
    try:
        item = db.get(ExpenseItem, item_id)
        if not item:
            return jsonify({"detail": "Статья не найдена"}), 404

        tx_count = db.scalar(
            select(func.count(Transaction.id)).where(
                Transaction.expense_item_id == item_id
            )
        )
        if tx_count and tx_count > 0:
            return jsonify(
                {"detail": "Нельзя удалить статью: есть связанные транзакции"}
            ), 400

        db.delete(item)
        db.commit()
        return "", 204
    finally:
        db.close()