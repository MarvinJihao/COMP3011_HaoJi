# app/db/session.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base

DATABASE_URL = "sqlite:///./app.db"

# this is for database connection:
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# FastAPI Dependency Injection Usage
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
