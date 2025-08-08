# server/db.py
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# --- Путь к файлу БД рядом с server/ ---
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "mh.sqlite3"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# --- Движок ---
engine = create_engine(
    DATABASE_URL,
    echo=False,                 # поставь True, если хочешь видеть сырой SQL
    future=True,
    connect_args={"check_same_thread": False},  # для многопоточных серверов
)

# --- База и фабрика сессий ---
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

def init_db() -> None:
    """
    Создаёт таблицы, если их нет.
    Важно: импортируем модели, чтобы они зарегистрировались в metadata.
    """
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)

@contextmanager
def session_scope():
    """
    Безопасная обёртка над сессией: commit/rollback/close автоматически.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except:  # noqa: E722
        session.rollback()
        raise
    finally:
        session.close()
