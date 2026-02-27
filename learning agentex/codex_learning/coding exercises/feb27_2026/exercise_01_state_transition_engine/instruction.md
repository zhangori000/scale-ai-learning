# Exercise: Concurrent State Transition Engine (60 minutes)

## Why this exercise
If you want to understand Agentex and SDK internals, you must be fluent in deterministic state transitions under concurrency. This is the core skill behind reliable workflow logic.

## Timebox
- 60 minutes total
- 10 min: read requirements
- 35 min: implement
- 15 min: run and validate edge cases

## Context from Agentex
1. State is scoped to `(task_id, agent_id)` and is isolated per pair.
2. Temporal workflows use explicit states and explicit transitions.
3. Streaming/event-driven systems can deliver retries and concurrent updates.

Your job is to build a minimal engine that handles all three realities.

## Build this
Implement a Python module named `state_engine.py` with:

1. `WorkflowState` enum
2. `EventType` enum
3. `Event` dataclass
4. `ApplyStatus` enum
5. `ApplyResult` dataclass
6. `TransitionRecord` dataclass
7. `TaskAgentStateEngine` class with async `apply(event)` method

## Required states
- `WAITING_FOR_USER_INPUT`
- `CLARIFYING_USER_QUERY`
- `PERFORMING_DEEP_RESEARCH`
- `COMPLETED`
- `FAILED`

## Required events
- `TASK_CREATED`
- `USER_MESSAGE_RECEIVED`
- `FOLLOW_UP_ASKED`
- `START_RESEARCH`
- `RESEARCH_COMPLETED`
- `RESEARCH_FAILED`

## Transition rules (must be exact)
1. `TASK_CREATED`: `None -> WAITING_FOR_USER_INPUT`
2. `USER_MESSAGE_RECEIVED`: `WAITING_FOR_USER_INPUT -> CLARIFYING_USER_QUERY`
3. `FOLLOW_UP_ASKED`: `CLARIFYING_USER_QUERY -> WAITING_FOR_USER_INPUT`
4. `START_RESEARCH`: `CLARIFYING_USER_QUERY -> PERFORMING_DEEP_RESEARCH`
5. `RESEARCH_COMPLETED`: `PERFORMING_DEEP_RESEARCH -> COMPLETED`
6. `RESEARCH_FAILED`: `PERFORMING_DEEP_RESEARCH -> FAILED`

Any other transition must be rejected.

## Non-negotiable invariants
1. State is independent per `(task_id, agent_id)` key.
2. `event_id` deduplication is required per key.
3. `seq` must be monotonic per key:
   - If `seq < last_seq`: reject.
   - If duplicate `event_id`: return duplicate (not rejected).
4. Concurrency safety is required:
   - Two concurrent `apply()` calls for the same key must not race.
   - Use per-key `asyncio.Lock`.
5. Every applied transition must append an audit record.

## Required API
```python
class TaskAgentStateEngine:
    async def apply(self, event: Event) -> ApplyResult: ...
    def get_state(self, task_id: str, agent_id: str) -> WorkflowState | None: ...
    def get_history(self, task_id: str, agent_id: str) -> list[TransitionRecord]: ...
    def dump_snapshot(self) -> dict[str, dict[str, object]]: ...
```

## Validation cases (must pass)
1. Happy path:
   - `TASK_CREATED -> USER_MESSAGE_RECEIVED -> START_RESEARCH -> RESEARCH_COMPLETED`
   - final state is `COMPLETED`
2. Duplicate event:
   - Apply same `event_id` twice
   - first is `APPLIED`, second is `DUPLICATE`
3. Out-of-order:
   - Apply `seq=3`, then `seq=2` for same key
   - second is `REJECTED`
4. Invalid transition:
   - `START_RESEARCH` from `WAITING_FOR_USER_INPUT`
   - must be `REJECTED`
5. Isolation:
   - same `task_id`, two different `agent_id`s
   - their states and histories diverge independently

## Definition of done
You are done only when all five validation cases pass with assertions.
