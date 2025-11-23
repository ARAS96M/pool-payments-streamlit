from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DB_FILE = os.getenv("DB_FILE", "sqlite:///clubs.db")
engine = create_engine(DB_FILE, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    from models import Club, Pricing, Payment
    Base.metadata.create_all(bind=engine)
