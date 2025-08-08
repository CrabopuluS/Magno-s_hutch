from datetime import datetime
from sqlalchemy import String, Integer, DateTime, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class SessionModel(Base):
    __tablename__ = "mh_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # UUID as string
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_mh_sessions_started", "started_at"),
    )

class EventModel(Base):
    __tablename__ = "mh_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(64), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime, index=True)
    props_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_mh_events_ts", "ts"),
        Index("ix_mh_events_name_ts", "name", "ts"),
    )
