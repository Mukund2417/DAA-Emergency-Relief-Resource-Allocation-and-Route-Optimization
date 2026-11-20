# FastAPI backend

Start from the project root, not this directory, so the backend's thin algorithm adapters can import the preserved root `app/algorithms` modules:

```powershell
python -m pip install -r backend\requirements.txt
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

OpenAPI docs are served at `/docs`; API routes use `/api`. SQLite is initialized safely on startup. Set `DAA_WEB_DB` to use another database path.

The endpoint implementations and schema are in `app/api/routes.py`, `app/models/`, and `app/services/`. No example rows are inserted on startup.
