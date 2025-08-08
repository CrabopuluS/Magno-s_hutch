from __future__ import annotations
from datetime import datetime, date, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from .models import SessionModel

def _daterange_days(d1: date, d2: date):
    cur = d1
    while cur <= d2:
        yield cur
        cur = cur + timedelta(days=1)

def get_daily_metrics(db: Session, from_date: date, to_date: date):
    # get sessions in range
    start_dt = datetime.combine(from_date, datetime.min.time())
    end_dt = datetime.combine(to_date, datetime.max.time())

    rows = db.execute(
        select(SessionModel).where(
            SessionModel.started_at >= start_dt,
            SessionModel.started_at <= end_dt,
        )
    ).scalars().all()

    # init buckets
    buckets: Dict[date, Dict[str, float]] = {
        d: {"plays_count": 0, "sum_score": 0.0, "cnt_score": 0, "sum_dur": 0.0, "cnt_dur": 0, "users": set()}
        for d in _daterange_days(from_date, to_date)
    }

    for s in rows:
        d = s.started_at.date()
        b = buckets.get(d)
        if b is None:
            continue
        b["plays_count"] += 1
        b["users"].add(s.user_id)
        if s.score is not None:
            b["sum_score"] += float(s.score)
            b["cnt_score"] += 1
        if s.duration_sec is not None:
            b["sum_dur"] += float(s.duration_sec)
            b["cnt_dur"] += 1

    result: List[Dict] = []
    for d in _daterange_days(from_date, to_date):
        b = buckets[d]
        avg_score = (b["sum_score"] / b["cnt_score"]) if b["cnt_score"] else 0.0
        avg_session_sec = (b["sum_dur"] / b["cnt_dur"]) if b["cnt_dur"] else 0.0
        result.append({
            "date": d.isoformat(),
            "plays_count": int(b["plays_count"]),
            "avg_score": round(avg_score, 2),
            "avg_session_sec": round(avg_session_sec, 2),
            "unique_users": len(b["users"]),
        })
    return result

def get_session_hist(db: Session, bins: int = 10):
    rows = db.execute(
        select(SessionModel.duration_sec).where(SessionModel.duration_sec.is_not(None))
    ).all()
    durations = [r[0] for r in rows if r[0] is not None and r[0] >= 0]
    if not durations:
        return [{"from": 0, "to": 0, "count": 0} for _ in range(max(1, bins))]

    mn, mx = min(durations), max(durations)
    if mn == mx:
        # single bin
        return [{"from": mn, "to": mx, "count": len(durations)}]

    width = (mx - mn) / float(bins)
    edges = [mn + i * width for i in range(bins+1)]
    counts = [0] * bins
    for v in durations:
        # place value into bin (inclusive of last edge)
        idx = min(int((v - mn) / width), bins - 1)
        counts[idx] += 1
    out = []
    for i in range(bins):
        out.append({"from": round(edges[i], 2), "to": round(edges[i+1], 2), "count": counts[i]})
    return out
