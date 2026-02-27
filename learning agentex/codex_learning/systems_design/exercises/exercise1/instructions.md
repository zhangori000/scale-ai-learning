# Exercise 1: The Core Agentex System Design You Must Internalize

Before you dive deep into SDK calls or backend internals, understand this architecture:

1. `TaskMessages` are the durable source of truth (conversation ledger).
2. `Events` are delivery triggers (notification mechanism).
3. `AgentTaskTracker` cursor (`last_processed_event_id`) controls resumable processing.
4. `State` is isolated per `(task_id, agent_id)`.

If this model is unclear, the rest of the codebase feels random.

## Why this matters

Across `agentex` docs and use cases, the same pattern appears:
- Tasks hold a flat message ledger.
- Events notify async handlers.
- Cursors prevent replay confusion.
- State is task+agent scoped for isolation and parallelism.

Your job is to implement this pattern in a small in-memory simulator.

## What system design means in this exercise

You are expected to do both:
1. Design: define requirements, failure modes, NFRs, and scaling plan.
2. Implementation: code a minimal but correct simulator.

Treat this like a real design review, not only a coding task.

## Required design deliverables

Before coding, write your own answers to these prompts:
1. Functional requirements:
   - What must always happen when a user message arrives?
   - What can happen asynchronously?
2. Non-functional requirements:
   - Delivery semantics target (at least once vs exactly once)
   - Latency SLO for event processing
   - Durability expectations for messages, events, and cursor
3. Failure analysis:
   - Crash after side effects but before cursor commit
   - Duplicate delivery of same event
   - Out-of-order or delayed deliveries
4. Scalability:
   - Partition key strategy
   - Hotspot risk (single task with very high write rate)
   - Backpressure strategy
5. Observability:
   - Metrics and logs needed to detect duplicate processing, lag, and stuck cursors

Use `architecture.md` for the design format and `readiness_playbook.md` for definitive engineering rules.

## Challenge

Implement `InMemoryAgentexCore` so it behaves like a minimal async orchestration backbone.

### Required behaviors

1. `post_user_message(task_id, text)`:
   - Append one durable USER message to the task ledger.
   - Emit one event per subscribed agent.

2. `process_with_cursor(task_id, agent_id, delivered_event_id, fail_after=None)`:
   - Ignore `delivered_event_id` as authoritative input.
   - Read tracker cursor for `(task_id, agent_id)`.
   - Fetch all events after the cursor.
   - For each unprocessed event:
     - Load corresponding durable message.
     - Update agent state:
       - `user_message_count += 1`
       - `last_user_message = <content>`
     - Emit one AGENT message as side effect.
   - Cursor must move only after successful batch completion.

3. Idempotency and retry:
   - Duplicate delivery and retries must not duplicate AGENT side effects.
   - Keep a dedupe structure in state, such as `processed_event_ids`.

4. Failure simulation:
   - If `fail_after` is provided, raise a runtime error after processing that many events but before cursor commit.
   - A retry should converge correctly without double-processing.

5. State isolation:
   - `agent-a` and `agent-b` on same task must maintain separate states.

## Starter code

```python
import asyncio
from dataclasses import dataclass
from typing import Any, Literal


Author = Literal["USER", "AGENT", "SYSTEM"]


@dataclass
class TaskMessage:
    id: str
    task_id: str
    author: Author
    content: str


@dataclass
class Event:
    id: str
    task_id: str
    agent_id: str
    message_id: str


class InMemoryAgentexCore:
    def __init__(self, agent_ids: list[str]):
        self.agent_ids = agent_ids
        self.messages_by_task: dict[str, list[TaskMessage]] = {}
        self.events_by_task_agent: dict[tuple[str, str], list[Event]] = {}
        self.tracker_by_task_agent: dict[tuple[str, str], str | None] = {}
        self.state_by_task_agent: dict[tuple[str, str], dict[str, Any]] = {}
        self._message_seq = 0
        self._event_seq = 0

    def _next_message_id(self) -> str:
        self._message_seq += 1
        return f"m-{self._message_seq:06d}"

    def _next_event_id(self) -> str:
        self._event_seq += 1
        return f"e-{self._event_seq:06d}"

    def _ensure_agent_task(self, task_id: str, agent_id: str) -> None:
        """
        TODO:
        - Initialize events list, tracker, and state for (task_id, agent_id)
        - Suggested state keys:
          user_message_count, last_user_message, processed_event_ids
        """
        pass

    async def post_user_message(self, task_id: str, text: str) -> str:
        """
        TODO:
        - Create USER TaskMessage and append to ledger
        - Create one Event per agent_id for this task message
        - Return created message id
        """
        pass

    def list_events_after(
        self, task_id: str, agent_id: str, last_event_id: str | None
    ) -> list[Event]:
        """
        TODO:
        Return events after last_event_id for this (task, agent).
        """
        pass

    def _get_message(self, task_id: str, message_id: str) -> TaskMessage:
        """
        TODO:
        Lookup message in durable ledger.
        """
        pass

    async def emit_agent_message(self, task_id: str, agent_id: str, text: str) -> str:
        """
        TODO:
        Append AGENT TaskMessage to durable ledger.
        Return message id.
        """
        pass

    async def process_with_cursor(
        self,
        task_id: str,
        agent_id: str,
        delivered_event_id: str,
        fail_after: int | None = None,
    ) -> int:
        """
        TODO:
        - Fetch pending events using tracker cursor (not delivered_event_id)
        - Process idempotently via processed_event_ids
        - Update state and emit AGENT side effects once per unique event
        - If fail_after is reached, raise RuntimeError before cursor commit
        - Commit cursor to last pending event only after successful batch
        - Return number of newly processed events
        """
        pass

    def snapshot_state(self, task_id: str, agent_id: str) -> dict[str, Any]:
        """
        Optional helper for readable output.
        """
        pass


async def demo():
    core = InMemoryAgentexCore(agent_ids=["agent-a", "agent-b"])
    task_id = "task-1"

    await core.post_user_message(task_id, "Need help with billing")

    # Simulate crash after first event side effects but before cursor commit
    try:
        await core.process_with_cursor(
            task_id=task_id,
            agent_id="agent-a",
            delivered_event_id="e-000001",
            fail_after=1,
        )
    except RuntimeError:
        pass

    # Retry same delivery
    await core.process_with_cursor(
        task_id=task_id,
        agent_id="agent-a",
        delivered_event_id="e-000001",
    )

    # Duplicate delivery should not duplicate work
    await core.process_with_cursor(
        task_id=task_id,
        agent_id="agent-a",
        delivered_event_id="e-000001",
    )

    # Process second agent independently
    await core.process_with_cursor(
        task_id=task_id,
        agent_id="agent-b",
        delivered_event_id="e-000002",
    )

    print("agent-a state:", core.snapshot_state(task_id, "agent-a"))
    print("agent-b state:", core.snapshot_state(task_id, "agent-b"))
    print("total messages:", len(core.messages_by_task[task_id]))


if __name__ == "__main__":
    asyncio.run(demo())
```

## Success criteria

1. Exactly one AGENT side-effect message per agent for the single USER message.
2. Duplicate or retried deliveries do not inflate counts.
3. `agent-a` and `agent-b` maintain independent state.
4. Cursor only advances after successful batch completion.
5. You can explain tradeoffs between:
   - event-triggered processing vs polling
   - at-least-once + dedupe vs exactly-once complexity
   - global shared state vs per-agent scoped state

## Stretch goals (ScaleAI interview level)

1. Add a per-agent dead letter queue for poison events.
2. Add state versioning and optimistic concurrency conflict retries.
3. Add replay mode: rebuild state from message ledger only.
4. Add "max events per batch" and prove fairness across tasks.
5. Add a compact architecture decision record (ADR) for each tradeoff.
