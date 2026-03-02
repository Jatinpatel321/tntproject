import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 🔥 EXPLICITLY LOAD .env FROM PROJECT ROOT
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not found. Check your .env file location.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency to get DB session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
