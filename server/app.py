# server/app.py (фрагмент)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db

app = FastAPI(title="Magno's Hutch API")

# CORS и прочее — как у тебя уже настроено...
# app.add_middleware(CORSMiddleware, ...)

@app.on_event("startup")
def on_startup():
    # Создаём таблицы, если их нет
    init_db()

# Ниже — твои маршруты /events, /metrics, /flags и т.п.
