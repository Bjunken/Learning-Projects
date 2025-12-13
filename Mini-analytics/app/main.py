from fastapi import FastAPI
from database import engine
from sqlalchemy import text
import pandas as pd

app = FastAPI()

@app.on_event("startup")
def startup():
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY,
            price INTEGER
        )
        """))

@app.post("/sales")
def add_sales(price: int):
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO sales (price) VALUES (:price)"),
            {"price": price}
        )
    return {"status": "saved", "price": price}

@app.get("/sales")
def get_sales():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT price FROM sales"))
        prices = [row[0] for row in result]
    return {"sales": prices}

@app.get("/stats")
def get_stats():
    with engine.connect() as conn:
        df = pd.read_sql("SELECT price FROM sales", conn)

    if df.empty:
        return {"message": "No data yet"}

    return {
        "count": int(df["price"].count()),
        "average_price": float(df["price"].mean()),
        "max_price": int(df["price"].max())
    }