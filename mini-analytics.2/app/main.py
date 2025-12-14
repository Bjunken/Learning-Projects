from fastapi import FastAPI, HTTPException
from database import database
from models import sales
import pandas as pd

app = FastAPI()

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.post("/sales")
async def create_sale(item: str, price: int):
    query = sales.insert().values(item=item, price=price)
    last_record_id = await database.execute(query)
    return {"id": last_record_id, "item": item, "price": price}

@app.get("/sales")
async def list_sales():
    query = sales.select()
    rows = await database.fetch_all(query)
    return rows

@app.get("/stats")
async def get_stats():
    query = sales.select()
    rows = await database.fetch_all(query)
    df = pd.DataFrame(rows)
    
    if df.empty:
        return {"message": "No data yet"}

    return {
        "total_sales": int(df.shape[0]),
        "average_price": float(df["price"].mean()) if not df.empty else 0.0,
        "max_price": int(df["price"].max()) if not df.empty else 0
    }
