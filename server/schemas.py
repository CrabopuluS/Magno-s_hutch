# server/schemas.py
from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator

# Одно событие от клиента
class EventIn(BaseModel):
    type: str = Field(..., max_length=50)                # TODO: при желании ввести перечисление типов
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None                # TODO: пока можно игнорировать и ставить серверное время

# Батч событий
class EventBatchIn(BaseModel):
    session_id: Optional[int] = None
    user_id: Optional[str] = Field(default=None, max_length=64)
    events: List[EventIn]

    @validator("events")
    def non_empty_and_reasonable(cls, v):
        if not v:
            raise ValueError("events must not be empty")
        if len(v) > 1000:
            raise ValueError("too many events in batch (max 1000)")
        return v

# Ответ сервера
class EventBatchOut(BaseModel):
    session_id: int
    saved: int
