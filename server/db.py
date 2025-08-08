import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DB_URL = os.getenv("MH_DB_URL", "sqlite:///./magnos_hutch.sqlite")

def _sqlite_kwargs(url: str):
    return {"check_same_thread": False} if url.startswith("sqlite") else {}

engine = create_engine(DB_URL, connect_args=_sqlite_kwargs(DB_URL))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

def init_db():
    # Late import to register models before create_all
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
