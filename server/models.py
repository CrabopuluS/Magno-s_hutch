# server/models.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

# --- Сессия пользователя ---
class Session(Base):
    __tablename__ = "mh_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),  # UTC
        nullable=False,
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Связь с событиями
    events: Mapped[list["Event"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_mh_sessions_user_started", "user_id", "started_at"),
    )

# --- Событие телеметрии ---
class Event(Base):
    __tablename__ = "mh_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("mh_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    type: Mapped[str] = mapped_column(String(50), index=True)  # например: 'open', 'jump', 'hit'
    payload: Mapped[dict] = mapped_column(JSON, default=dict)  # гибкое поле с деталями

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),  # UTC
        nullable=False,
    )

    session: Mapped["Session"] = relationship(back_populates="events")

    __table_args__ = (
        Index("ix_mh_events_session_created", "session_id", "created_at"),
        Index("ix_mh_events_type_created", "type", "created_at"),
    )
