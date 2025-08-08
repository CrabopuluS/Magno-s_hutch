from __future__ import annotations
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .db import init_db, SessionLocal
from .schemas import EventsBatch
from .models import SessionModel, EventModel
from .metrics import get_daily_metrics as _get_daily_metrics, get_session_hist as _get_session_hist

def to_utc_naive(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc).replace(tzinfo=None)
    return dt.astimezone(timezone.utc).replace(tzinfo=None)

def get_db() -> Session:
    return SessionLocal()

def allowed_origins() -> list[str]:
    val = os.getenv("MH_ALLOWED_ORIGINS")
    if not val:
        return ["*"]
    return [v.strip() for v in val.split(",") if v.strip()]

app = FastAPI(title="Magno's hutch API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

@app.post("/events")
def post_events(batch: EventsBatch, x_magnoshutch_client: Optional[str] = Header(default=None)):
    # Process incoming batch of events
    db = get_db()
    try:
        # ensure session row exists (on game_start) or upsert lazily
        session_row = db.get(SessionModel, batch.session_id)
        for ev in batch.events:
            ts = to_utc_naive(ev.ts)
            if ev.name == "game_start":
                if session_row is None:
                    session_row = SessionModel(
                        id=batch.session_id,
                        user_id=batch.user_id,
                        started_at=ts,
                        ended_at=None,
                        duration_sec=None,
                        score=None,
                    )
                    db.add(session_row)
                else:
                    # idempotent: do not overwrite started_at if present
                    if session_row.started_at is None:
                        session_row.started_at = ts

            elif ev.name == "game_over":
                if session_row is None:
                    # if somehow missing, create to keep data consistent
                    session_row = SessionModel(
                        id=batch.session_id,
                        user_id=batch.user_id,
                        started_at=ts,
                    )
                    db.add(session_row)
                session_row.ended_at = ts
                # optional score
                if isinstance(ev.props, dict):
                    sc = ev.props.get("final_score")
                    if isinstance(sc, (int, float)):
                        session_row.score = int(sc)
                # duration
                if session_row.started_at is not None and session_row.ended_at is not None:
                    session_row.duration_sec = int((session_row.ended_at - session_row.started_at).total_seconds())

            # Persist each event
            db.add(EventModel(
                session_id=batch.session_id,
                user_id=batch.user_id,
                name=ev.name,
                ts=ts,
                props_json=ev.props or None,
            ))

        db.commit()
        return {"ok": True}
    except Exception as e:
        db.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        db.close()

@app.get("/metrics/daily")
def metrics_daily(
    from_: str = Query(alias="from"),
    to: str = Query(alias="to"),
):
    from datetime import date
    with SessionLocal() as db:
        from_date = date.fromisoformat(from_)
        to_date = date.fromisoformat(to)
        return _get_daily_metrics(db, from_date, to_date)

@app.get("/metrics/session-hist")
def metrics_session_hist(bins: int = 10):
    with SessionLocal() as db:
        return _get_session_hist(db, bins)

@app.get("/flags")
def flags():
    return {"difficulty": "normal"}
