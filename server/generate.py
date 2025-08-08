from __future__ import annotations
import argparse, random
from datetime import datetime, timedelta, timezone
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import select

from .db import SessionLocal, init_db
from .models import SessionModel, EventModel

def rand_dt_on_day(day, start_h=9, end_h=22):
    hour = random.randint(start_h, end_h)
    minute = random.randint(0,59)
    second = random.randint(0,59)
    return datetime(day.year, day.month, day.day, hour, minute, second, tzinfo=timezone.utc)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--sessions", type=int, default=300)
    parser.add_argument("--users", type=int, default=120)
    args = parser.parse_args()

    init_db()
    random.seed(42)

    # generate users
    user_ids = [str(uuid.uuid4()) for _ in range(args.users)]

    with SessionLocal() as db:
        # Determine day range from today backwards
        today = datetime.now(tz=timezone.utc).date()
        days = [today - timedelta(days=i) for i in range(args.days)]
        for _ in range(args.sessions):
            day = random.choice(days)
            user_id = random.choice(user_ids)
            sid = str(uuid.uuid4())

            start_ts = rand_dt_on_day(day)
            duration = random.randint(10, 180)  # seconds
            score = random.randint(50, 800)
            end_ts = start_ts + timedelta(seconds=duration)

            # session
            s = SessionModel(
                id=sid,
                user_id=user_id,
                started_at=start_ts.replace(tzinfo=None),  # store naive UTC
                ended_at=end_ts.replace(tzinfo=None),
                duration_sec=duration,
                score=score,
            )
            db.add(s)
            # events: start, few jumps & score, end
            db.add(EventModel(
                session_id=sid, user_id=user_id, name="game_start",
                ts=s.started_at, props_json=None
            ))

            jumps = random.randint(1, 6)
            for i in range(jumps):
                t = s.started_at + timedelta(seconds=random.randint(1, max(1, duration-2)))
                db.add(EventModel(
                    session_id=sid, user_id=user_id, name="jump",
                    ts=t, props_json={"height": random.randint(8, 20)}
                ))
                db.add(EventModel(
                    session_id=sid, user_id=user_id, name="score",
                    ts=t, props_json={"value": random.randint(10, score)}
                ))

            db.add(EventModel(
                session_id=sid, user_id=user_id, name="game_over",
                ts=s.ended_at, props_json={"final_score": score}
            ))

        db.commit()
        print("Generated demo data.")

if __name__ == "__main__":
    main()
