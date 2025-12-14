from sqlalchemy import Table, Column, Integer, String
from database import metadata

sales = Table(
    "sales",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("item", String, nullable=False),
    Column("price", Integer, nullable=False),
)
