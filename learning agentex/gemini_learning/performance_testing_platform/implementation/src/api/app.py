from fastapi import FastAPI, BackgroundTasks
from ..engine.models import TestPlan
from ..engine.orchestrator import PerformanceOrchestrator
from typing import Dict

app = FastAPI(title="PerfTest Control Plane")

# Simple in-memory storage for results
# In prod, use Redis/Postgres
results_db = {}

async def execute_test_job(plan: TestPlan):
    orchestrator = PerformanceOrchestrator(plan)
    stats = await orchestrator.run_plan()
    results_db[plan.project_name] = stats

@app.post("/register-job")
async def register_job(plan: TestPlan, background_tasks: BackgroundTasks):
    """
    Submits a complex test plan to be run in the background.
    """
    background_tasks.add_task(execute_test_job, plan)
    return {"message": f"Job '{plan.project_name}' registered and started.", "project": plan.project_name}

@app.get("/results/{project_name}")
async def get_results(project_name: str):
    """
    Fetches the P99 stats for a finished job.
    """
    if project_name not in results_db:
        return {"status": "pending_or_not_found"}
    return results_db[project_name]
