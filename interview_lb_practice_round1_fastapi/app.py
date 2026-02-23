from __future__ import annotations

from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from lightweight_lb import LightweightLoadBalancer, TaskPriority

app = FastAPI(
    title="Lightweight Load Balancer API",
    version="1.0.0",
    description=(
        "Interview-style backend practical: worker registry, heartbeat/liveness, "
        "priority task queue, dispatch, and failover."
    ),
)

# In-memory singleton for demo/interview use.
lb = LightweightLoadBalancer(
    heartbeat_timeout_s=15.0,
    default_lease_timeout_s=10.0,
)


PRIORITY_MAP = {
    "critical": TaskPriority.CRITICAL,
    "high": TaskPriority.HIGH,
    "medium": TaskPriority.MEDIUM,
    "low": TaskPriority.LOW,
}


class RegisterWorkerRequest(BaseModel):
    worker_id: str = Field(..., min_length=1, max_length=200)
    capacity: int = Field(1, gt=0, le=100000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class HeartbeatRequest(BaseModel):
    in_flight: int | None = Field(default=None, ge=0)
    capacity: int | None = Field(default=None, gt=0, le=100000)
    metadata: dict[str, Any] | None = None


class EnqueueTaskRequest(BaseModel):
    payload: Any
    priority: Literal["critical", "high", "medium", "low"] = "medium"
    task_id: str | None = Field(default=None, min_length=1, max_length=200)
    max_retries: int = Field(2, ge=0, le=50)
    lease_timeout_s: float | None = Field(default=None, gt=0, le=3600)


class DispatchRequest(BaseModel):
    max_assignments: int = Field(1, ge=1, le=10000)


class AckRequest(BaseModel):
    worker_id: str = Field(..., min_length=1, max_length=200)
    task_id: str = Field(..., min_length=1, max_length=200)
    success: bool
    retryable: bool = True
    error: str | None = None


def _serialize_assignment(assignment: Any) -> dict[str, Any]:
    return {
        "task_id": assignment.task_id,
        "worker_id": assignment.worker_id,
        "payload": assignment.payload,
        "priority": assignment.priority.name.lower(),
        "attempt": assignment.attempt,
        "lease_expires_at": assignment.lease_expires_at,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/workers/register")
def register_worker(request: RegisterWorkerRequest) -> dict[str, Any]:
    worker = lb.register_worker(
        worker_id=request.worker_id,
        capacity=request.capacity,
        metadata=request.metadata,
    )
    return {
        "worker_id": worker.worker_id,
        "status": worker.status.value,
        "capacity": worker.capacity,
        "in_flight": worker.in_flight,
        "last_heartbeat": worker.last_heartbeat,
        "metadata": worker.metadata,
    }


@app.post("/workers/{worker_id}/heartbeat")
def heartbeat(worker_id: str, request: HeartbeatRequest) -> dict[str, Any]:
    worker = lb.heartbeat(
        worker_id=worker_id,
        in_flight=request.in_flight,
        capacity=request.capacity,
        metadata=request.metadata,
    )
    return {
        "worker_id": worker.worker_id,
        "status": worker.status.value,
        "capacity": worker.capacity,
        "in_flight": worker.in_flight,
        "last_heartbeat": worker.last_heartbeat,
        "metadata": worker.metadata,
    }


@app.post("/workers/{worker_id}/mark-lost")
def mark_lost(worker_id: str) -> dict[str, Any]:
    lb.mark_worker_lost(worker_id)
    return {"worker_id": worker_id, "marked_lost": True}


@app.post("/tasks/enqueue")
def enqueue_task(request: EnqueueTaskRequest) -> dict[str, Any]:
    priority = PRIORITY_MAP[request.priority]
    try:
        task_id = lb.enqueue_task(
            payload=request.payload,
            priority=priority,
            task_id=request.task_id,
            max_retries=request.max_retries,
            lease_timeout_s=request.lease_timeout_s,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"task_id": task_id}


@app.post("/dispatch")
def dispatch(request: DispatchRequest) -> dict[str, Any]:
    assignments = lb.dispatch(max_assignments=request.max_assignments)
    return {"assignments": [_serialize_assignment(a) for a in assignments]}


@app.post("/ack")
def ack(request: AckRequest) -> dict[str, Any]:
    accepted = lb.ack(
        worker_id=request.worker_id,
        task_id=request.task_id,
        success=request.success,
        retryable=request.retryable,
        error=request.error,
    )
    if not accepted:
        raise HTTPException(
            status_code=409,
            detail="ack rejected (task unknown, stale lease, or wrong worker)",
        )
    return {"accepted": True}


@app.post("/tick")
def tick() -> dict[str, bool]:
    lb.tick()
    return {"ok": True}


@app.get("/snapshot")
def snapshot() -> dict[str, Any]:
    return lb.snapshot()

