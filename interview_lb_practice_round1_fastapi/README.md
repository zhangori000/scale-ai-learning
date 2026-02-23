# Separate FastAPI Version (Reference 2)

This is a separate implementation from `interview_lb_practice_round1/` so you can keep both:

- `interview_lb_practice_round1/` -> pure Python core (no web framework)
- `interview_lb_practice_round1_fastapi/` -> same core + FastAPI HTTP API

## What you get

- `lightweight_lb.py` - core scheduling and failover logic
- `app.py` - FastAPI wrapper endpoints
- `FASTAPI_OFFLINE_GUIDE.md` - beginner/offline-friendly guide
- `requirements.txt` - dependencies
- `prepare_offline_wheels.ps1` - dependency pre-download for airplane mode

## Quick start (when online)

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
uvicorn app:app --reload --port 8010
```

Open docs:

- `http://127.0.0.1:8010/docs`

## Offline prep (before flight)

1. Download packages:

```powershell
.\prepare_offline_wheels.ps1
```

2. Later install offline:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --no-index --find-links wheelhouse -r requirements.txt
uvicorn app:app --port 8010
```

## Endpoint summary

- `GET /health`
- `POST /workers/register`
- `POST /workers/{worker_id}/heartbeat`
- `POST /workers/{worker_id}/mark-lost`
- `POST /tasks/enqueue`
- `POST /dispatch`
- `POST /ack`
- `POST /tick`
- `GET /snapshot`

## Notes

- State is in-memory (good for interview demo, not production durable).
- Core algorithm is thread-safe in-process.
- For production, persist queue/leases and add distributed coordination.
