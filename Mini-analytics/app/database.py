from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///sales.db", echo=True)