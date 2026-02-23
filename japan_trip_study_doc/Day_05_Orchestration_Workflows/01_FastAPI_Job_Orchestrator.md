# Day 05 - Practical: Designing a Job Orchestrator API in FastAPI

Scale AI doesn't just do "Quick API Calls." We do **"Work"** (e.g., re-evaluating 1 million LLM outputs). This is an **Orchestration** lesson.

## 1. The Async Job Pattern
The user POSTs a "Batch" request. We don't want the API to wait 1 hour for it to finish. 

```python
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
import uuid

app = FastAPI()

class BatchRequest(BaseModel):
    dataset_id: str
    model_version: str

@app.post("/v1/batches", status_code=202) # 202 = Accepted
async def start_batch_job(
    request: BatchRequest,
    background_tasks: BackgroundTasks, # FastAPI's built-in background worker
    db = Depends(get_db)
):
    # 1. CREATE: Generate a Job ID and store it as 'QUEUED'
    job_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO jobs (id, status, payload) VALUES (:id, 'QUEUED', :p)",
        {"id": job_id, "p": request.model_dump_json()}
    )
    
    # 2. OFFLOAD: Tell FastAPI to run the heavy work in the background
    background_tasks.add_task(run_batch_logic, job_id)
    
    # 3. RETURN: Give the user the ID immediately
    return {"job_id": job_id, "status": "queued"}

async def run_batch_logic(job_id: str):
    """
    This runs AFTER the API response is sent.
    """
    # 4. UPDATE: Mark the job as 'RUNNING'
    await db.execute("UPDATE jobs SET status = 'RUNNING' WHERE id = :id", {"id": job_id})
    
    try:
        # Simulate heavy work (e.g., calling 1,000 LLMs)
        await process_dataset(job_id)
        
        # 5. SUCCESS: Mark as 'SUCCEEDED'
        await db.execute("UPDATE jobs SET status = 'SUCCEEDED' WHERE id = :id", {"id": job_id})
    except Exception as e:
        # 6. FAILURE: Mark as 'FAILED' and store the error
        await db.execute(
            "UPDATE jobs SET status = 'FAILED', error = :e WHERE id = :id",
            {"id": job_id, "e": str(e)}
        )
```

---

## 2. 🧠 Key Teaching Points:
*   **`BackgroundTasks`**: This is FastAPI's "Lightweight" way to offload work. In a real Scale production system, we would use a **Dedicated Worker Cluster** (like Celery, Temporal, or Airflow).
*   **The 202 Accepted Response**: This is a "Contract" with the user. "I have accepted your request. Use this `job_id` to check the status later."
*   **Idempotent Job Creation**: What if the user clicks "Submit" twice? We should use the `dataset_id` as a **De-duplication Key** so we don't run the same expensive batch twice.
*   **State Machine Logic**: Notice the `QUEUED -> RUNNING -> SUCCEEDED/FAILED` transitions. This is a "Deterministic State Machine." You should never jump from `QUEUED` to `SUCCEEDED` without passing through `RUNNING`.
*   **Polling Endpoint**: You'll also need a `GET /v1/batches/{job_id}` endpoint for the user to "Poll" for the result. At Scale, we might use **Webhooks** or **SSE** to notify the user instead of making them poll.
