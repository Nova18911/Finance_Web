from pathlib import Path

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

from backend.blueprints.categories import categories_bp
from backend.blueprints.expense_items import expense_items_bp
from backend.blueprints.transactions import transactions_bp

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = Flask(__name__)
CORS(app)

app.register_blueprint(categories_bp)
app.register_blueprint(expense_items_bp)
app.register_blueprint(transactions_bp)


@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "Categories.html")


@app.get("/Categories.html")
def categories_page():
    return send_from_directory(FRONTEND_DIR, "Categories.html")


@app.get("/ExpenseItems.html")
def expense_items_page():
    return send_from_directory(FRONTEND_DIR, "ExpenseItems.html")


@app.get("/Transactions.html")
def transactions_page():
    return send_from_directory(FRONTEND_DIR, "Transactions.html")


@app.get("/css/<path:filename>")
def css_files(filename):
    return send_from_directory(FRONTEND_DIR / "css", filename)


@app.get("/js/<path:filename>")
def js_files(filename):
    return send_from_directory(FRONTEND_DIR / "js", filename)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8010, debug=True)