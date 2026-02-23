# FastAPI Offline Guide (Beginner-Friendly)

This guide is written so you can read it on a flight with no internet.

## 1) What FastAPI is

FastAPI is a Python web framework for building APIs quickly.

In practice:

- You write Python functions.
- You attach them to HTTP routes (`GET`, `POST`, etc.).
- FastAPI validates request bodies using Pydantic models.
- It auto-generates API docs at `/docs`.

## 2) Terms you need

| Term | Meaning |
|---|---|
| Route | URL path + method, e.g. `POST /tasks/enqueue` |
| Handler | Python function that runs when route is called |
| Request body | JSON sent by the client |
| Response | JSON returned by handler |
| Pydantic model | Python class that validates input data |
| Uvicorn | ASGI server process that runs your FastAPI app |

## 3) Project files in this folder

- `app.py` - FastAPI app and endpoints
- `lightweight_lb.py` - scheduler/load-balancer logic
- `requirements.txt` - dependencies
- `prepare_offline_wheels.ps1` - download packages for offline install

## 4) FastAPI shape in `app.py`

You will see this pattern:

1. Create app:

```python
app = FastAPI(...)
```

2. Define request schema:

```python
class EnqueueTaskRequest(BaseModel):
    payload: Any
    priority: Literal["critical", "high", "medium", "low"] = "medium"
```

3. Define route:

```python
@app.post("/tasks/enqueue")
def enqueue_task(request: EnqueueTaskRequest):
    ...
```

FastAPI will:

- parse JSON into `EnqueueTaskRequest`
- validate fields
- return `422` automatically if invalid

## 5) Install and run (online normal mode)

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
uvicorn app:app --reload --port 8010
```

Then open:

- `http://127.0.0.1:8010/docs`

## 6) Prepare for offline use before flight

Run this while you still have internet:

```powershell
.\prepare_offline_wheels.ps1
```

This creates `wheelhouse/` with dependency files.

On airplane/offline machine:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --no-index --find-links wheelhouse -r requirements.txt
uvicorn app:app --port 8010
```

## 7) Endpoint flow you should memorize

1. `POST /workers/register`  
Register worker with capacity.

2. `POST /workers/{worker_id}/heartbeat`  
Keep worker alive and update load.

3. `POST /tasks/enqueue`  
Add task with priority.

4. `POST /dispatch`  
Ask scheduler for assignments.

5. `POST /ack`  
Report task success/failure.

6. `POST /tick`  
Run failover housekeeping.

7. `GET /snapshot`  
Inspect state.

## 8) Minimal request examples (PowerShell)

Register worker:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8010/workers/register" -ContentType "application/json" -Body '{"worker_id":"w1","capacity":2}'
```

Enqueue critical task:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8010/tasks/enqueue" -ContentType "application/json" -Body '{"payload":{"job":"incident"},"priority":"critical"}'
```

Dispatch:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8010/dispatch" -ContentType "application/json" -Body '{"max_assignments":5}'
```

Ack success:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8010/ack" -ContentType "application/json" -Body '{"worker_id":"w1","task_id":"<task-id>","success":true}'
```

## 9) Common beginner mistakes

1. Wrong JSON keys -> FastAPI returns `422`.
2. Forgetting `Content-Type: application/json`.
3. Running `python app.py` instead of `uvicorn app:app`.
4. Forgetting to activate virtual environment.
5. Using stale `task_id` in `/ack` (returns conflict).

## 10) How to explain this in an interview

Say:

1. I separated transport layer (FastAPI routes) from core scheduling logic (`lightweight_lb.py`).
2. API only validates and delegates.
3. Core logic handles worker states, priority queue, leases, and failover.
4. This makes testing and future migration to another transport (gRPC, message bus) easier.
