from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="Личные финансы")

app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")


@app.get("/")
def index():
    return RedirectResponse(url="/Categories.html")


@app.get("/Categories.html")
def categories_page():
    return FileResponse(FRONTEND_DIR / "Categories.html")


@app.get("/ExpenseItems.html")
def expense_items_page():
    return FileResponse(FRONTEND_DIR / "ExpenseItems.html")


@app.get("/Transactions.html")
def transactions_page():
    return FileResponse(FRONTEND_DIR / "Transactions.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)