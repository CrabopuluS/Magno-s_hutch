from datetime import datetime
from typing import Any, Dict, List
from pydantic import BaseModel, Field

class EventIn(BaseModel):
    name: str
    ts: datetime
    props: Dict[str, Any] = Field(default_factory=dict)

class EventsBatch(BaseModel):
    session_id: str
    user_id: str
    events: List[EventIn]
