# Magno’s hutch

Мини-игра (endless runner) + FastAPI-бэкенд телеметрии + дашборд метрик.

## Быстрый старт
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn server.app:app --reload
# Открой client/index.html в браузере (или подними любой статик-сервер)
```

## Эндпоинты
- `POST /events` — батч событий.
- `GET /metrics/daily?from=YYYY-MM-DD&to=YYYY-MM-DD`
- `GET /metrics/session-hist?bins=10`
- `GET /flags` (опционально)

## Генерация демо-данных
```bash
python -m server.generate --days 14 --sessions 300 --users 120
```

## Деплой
- Клиент — GitHub Pages (папка `client/`)
- Сервер — Render / Fly.io
  - `MH_DB_URL=sqlite:///./magnos_hutch.sqlite`
  - `MH_ALLOWED_ORIGINS=https://<gh-username>.github.io,http://localhost:8000`
  - `MH_AUTH_TOKEN=<опционально>`
