# Exercise 1: Reference Solution

```python
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


@dataclass
class AutoscalingPolicy:
    min_replicas: int = 1
    max_replicas: int = 10
    target_cpu: int = 50
    scale_up_windows: int = 2
    scale_down_windows: int = 3
    cooldown_windows: int = 1


@dataclass
class ServiceState:
    replicas: int
    up_streak: int = 0
    down_streak: int = 0
    cooldown: int = 0


@dataclass
class Window:
    minute: int
    api_cpu: int
    worker_cpu: int
    incoming_events: list[str] = field(default_factory=list)
    retry_events: list[str] = field(default_factory=list)


@dataclass
class Decision:
    minute: int
    api_replicas: int
    worker_replicas: int
    api_action: str
    worker_action: str
    queue_depth: int
    accepted_events: int
    deduped_events: int
    processed_events: int


def _scale_step(
    state: ServiceState,
    policy: AutoscalingPolicy,
    *,
    cpu: int,
    pressure: float,
    pressure_up_threshold: float,
    pressure_down_threshold: float,
    allow_scale_down: bool = True,
) -> str:
    if state.cooldown > 0:
        state.cooldown -= 1

    up_signal = cpu > policy.target_cpu or pressure > pressure_up_threshold
    down_signal = (
        cpu < int(policy.target_cpu * 0.5)
        and pressure < pressure_down_threshold
        and allow_scale_down
    )

    if up_signal:
        state.up_streak += 1
        state.down_streak = 0
    elif down_signal:
        state.down_streak += 1
        state.up_streak = 0
    else:
        state.up_streak = 0
        state.down_streak = 0

    if (
        state.cooldown == 0
        and state.up_streak >= policy.scale_up_windows
        and state.replicas < policy.max_replicas
    ):
        state.replicas += 1
        state.up_streak = 0
        state.down_streak = 0
        state.cooldown = policy.cooldown_windows
        return "scale_up"

    if (
        state.cooldown == 0
        and state.down_streak >= policy.scale_down_windows
        and state.replicas > policy.min_replicas
    ):
        state.replicas -= 1
        state.up_streak = 0
        state.down_streak = 0
        state.cooldown = policy.cooldown_windows
        return "scale_down"

    return "hold"


def simulate(
    windows: list[Window],
    api_policy: AutoscalingPolicy,
    worker_policy: AutoscalingPolicy,
    max_concurrent_activities: int = 10,
) -> list[Decision]:
    api = ServiceState(replicas=api_policy.min_replicas)
    worker = ServiceState(replicas=worker_policy.min_replicas)

    queue: deque[str] = deque()
    seen_event_ids: set[str] = set()
    decisions: list[Decision] = []

    for w in windows:
        accepted = 0
        deduped = 0

        # Retries can replay IDs. Keep queue insertion idempotent.
        for event_id in [*w.incoming_events, *w.retry_events]:
            if event_id in seen_event_ids:
                deduped += 1
                continue
            seen_event_ids.add(event_id)
            queue.append(event_id)
            accepted += 1

        api_pressure = (len(w.incoming_events) + len(w.retry_events)) / max(api.replicas, 1)
        worker_pressure = len(queue) / max(worker.replicas, 1)

        api_action = _scale_step(
            api,
            api_policy,
            cpu=w.api_cpu,
            pressure=api_pressure,
            pressure_up_threshold=20.0,   # reqs/min/replica
            pressure_down_threshold=5.0,
        )

        worker_action = _scale_step(
            worker,
            worker_policy,
            cpu=w.worker_cpu,
            pressure=worker_pressure,
            pressure_up_threshold=float(max_concurrent_activities),
            pressure_down_threshold=1.0,
            allow_scale_down=(len(queue) == 0),
        )

        throughput = worker.replicas * max_concurrent_activities
        processed = min(throughput, len(queue))
        for _ in range(processed):
            queue.popleft()

        decisions.append(
            Decision(
                minute=w.minute,
                api_replicas=api.replicas,
                worker_replicas=worker.replicas,
                api_action=api_action,
                worker_action=worker_action,
                queue_depth=len(queue),
                accepted_events=accepted,
                deduped_events=deduped,
                processed_events=processed,
            )
        )

    return decisions
```

## Why this matches Agentex behavior
- Independent service scaling mirrors ACP and `temporal-worker` values in deploy handlers.
- Queue-aware worker control mirrors Temporal task queue routing and worker polling.
- `max_concurrent_activities` models per-worker throughput limits.
- Idempotent queue insertion models retry safety requirements for durable systems.

## Minimal validation example
```python
if __name__ == "__main__":
    api_policy = AutoscalingPolicy(min_replicas=1, max_replicas=4, target_cpu=50)
    worker_policy = AutoscalingPolicy(min_replicas=1, max_replicas=5, target_cpu=50)
    windows = [
        Window(minute=1, api_cpu=35, worker_cpu=35, incoming_events=[f"e{i}" for i in range(20)]),
        Window(minute=2, api_cpu=70, worker_cpu=45, incoming_events=[f"e{i}" for i in range(20, 40)]),
        Window(minute=3, api_cpu=75, worker_cpu=55, incoming_events=[f"e{i}" for i in range(40, 60)]),
        Window(minute=4, api_cpu=30, worker_cpu=30, incoming_events=[], retry_events=["e10", "e11"]),
    ]
    for row in simulate(windows, api_policy, worker_policy, max_concurrent_activities=10):
        print(row)
```
