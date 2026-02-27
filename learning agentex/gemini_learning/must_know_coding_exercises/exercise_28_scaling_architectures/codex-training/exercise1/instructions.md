# Exercise 1: Queue-Aware Dual-Service Autoscaler

## Why this exercise exists
You are modeling the real Agentex pattern:
- ACP/API service scales independently.
- Temporal worker service scales independently.
- Work is routed by task queue.
- Worker concurrency limits and idempotency determine real throughput.

This maps directly to:
- `deploy_handlers.py` autoscaling setup
- `WORKFLOW_TASK_QUEUE` routing in `run_handlers.py`
- Temporal submission in `temporal_task_service.py`
- Worker concurrency in `worker.py`

## Problem
Implement a simulator in `scaling_simulator.py` that makes minute-by-minute scaling decisions for:
- `api` service
- `temporal-worker` service

## Requirements
1. Support separate autoscaling policies per service:
- `min_replicas`
- `max_replicas`
- `target_cpu`
- `scale_up_windows`
- `scale_down_windows`
- `cooldown_windows`
2. Use queue-aware logic:
- worker scale-up can trigger on CPU or queue pressure.
- worker scale-down is blocked while queue is non-empty.
3. Keep scaling independent:
- API can scale up while worker holds, and vice versa.
4. Model worker throughput:
- `processed_per_minute = worker_replicas * max_concurrent_activities`
5. Enforce idempotency:
- duplicate event IDs (retries) must not be re-enqueued.
6. Return a decision log with, per minute:
- `api_replicas`
- `worker_replicas`
- `api_action`
- `worker_action`
- `queue_depth`
- `accepted_events`
- `deduped_events`
- `processed_events`

## Suggested API
```python
simulate(
    windows: list[Window],
    api_policy: AutoscalingPolicy,
    worker_policy: AutoscalingPolicy,
    max_concurrent_activities: int = 10,
) -> list[Decision]
```

## Test Scenarios (must pass)
1. Queue growth forces worker scale-up even if worker CPU is moderate.
2. Worker does not scale down until queue depth is 0.
3. Duplicate retry IDs are deduped and not double-counted.
4. API and worker replica counts diverge under asymmetric load.

## Interview discussion prompts
1. Why can CPU-only autoscaling be insufficient for Temporal workers?
2. How do queue depth and concurrency interact?
3. Why is idempotency mandatory when retries happen during scaling events?
