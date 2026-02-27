# Solution: Ledger + Event Trigger + Cursor + Isolated State

## Part 0: How a seasoned engineer frames this

Before writing code, define the invariants:

1. Message durability invariant:
   - Once accepted, a USER message must exist in durable history.
2. Processing invariant:
   - Each agent processes each event at most once logically, even with retries.
3. Cursor safety invariant:
   - Cursor can move forward only after side effects complete.
4. Isolation invariant:
   - Agent A state updates can never mutate Agent B state.

Then pick explicit semantics:
1. Delivery semantics: at least once delivery from event channel.
2. Correctness strategy: idempotent processing with dedupe keys.
3. Recovery strategy: replay pending events after last committed cursor.

## Part 1: The key system design

The most important Agentex mental model is:

1. Durable ledger: `TaskMessages` are the canonical history.
2. Trigger channel: `Events` signal "new work exists."
3. Cursor checkpoint: tracker stores `last_processed_event_id`.
4. Per-agent memory: state is scoped to `(task_id, agent_id)`.

This pattern gives you resumability, at-least-once safety, and multi-agent isolation.

## Part 2: Reference implementation

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
        key = (task_id, agent_id)
        self.events_by_task_agent.setdefault(key, [])
        # Cursor is the only committed "checkpoint" for batch progress.
        self.tracker_by_task_agent.setdefault(key, None)
        self.state_by_task_agent.setdefault(
            key,
            {
                "user_message_count": 0,
                "last_user_message": None,
                # Dedupe set makes at-least-once delivery safe.
                "processed_event_ids": set(),
            },
        )

    async def post_user_message(self, task_id: str, text: str) -> str:
        # 1) Persist durable message first.
        message_id = self._next_message_id()
        self.messages_by_task.setdefault(task_id, []).append(
            TaskMessage(
                id=message_id,
                task_id=task_id,
                author="USER",
                content=text,
            )
        )

        # 2) Emit per-agent events that reference durable message id.
        for agent_id in self.agent_ids:
            self._ensure_agent_task(task_id, agent_id)
            event_id = self._next_event_id()
            self.events_by_task_agent[(task_id, agent_id)].append(
                Event(
                    id=event_id,
                    task_id=task_id,
                    agent_id=agent_id,
                    message_id=message_id,
                )
            )
        return message_id

    def list_events_after(
        self, task_id: str, agent_id: str, last_event_id: str | None
    ) -> list[Event]:
        self._ensure_agent_task(task_id, agent_id)
        events = self.events_by_task_agent[(task_id, agent_id)]
        if last_event_id is None:
            return list(events)
        # Forward-only cursor movement via monotonic id.
        return [event for event in events if event.id > last_event_id]

    def _get_message(self, task_id: str, message_id: str) -> TaskMessage:
        for message in self.messages_by_task.get(task_id, []):
            if message.id == message_id:
                return message
        raise KeyError(f"message not found: task={task_id}, message_id={message_id}")

    async def emit_agent_message(self, task_id: str, agent_id: str, text: str) -> str:
        message_id = self._next_message_id()
        self.messages_by_task.setdefault(task_id, []).append(
            TaskMessage(
                id=message_id,
                task_id=task_id,
                author="AGENT",
                content=f"[{agent_id}] {text}",
            )
        )
        return message_id

    async def process_with_cursor(
        self,
        task_id: str,
        agent_id: str,
        delivered_event_id: str,
        fail_after: int | None = None,
    ) -> int:
        # Delivery notification can be stale/duplicate, so ignore it for fetch boundaries.
        _ = delivered_event_id
        self._ensure_agent_task(task_id, agent_id)
        key = (task_id, agent_id)

        # Pull from committed cursor, not from delivery payload.
        cursor = self.tracker_by_task_agent[key]
        pending_events = self.list_events_after(task_id, agent_id, cursor)
        if not pending_events:
            return 0

        state = self.state_by_task_agent[key]
        processed_this_call = 0

        for event in pending_events:
            if event.id in state["processed_event_ids"]:
                # Logical exactly-once behavior on top of at-least-once transport.
                continue

            message = self._get_message(task_id, event.message_id)
            if message.author == "USER":
                state["user_message_count"] += 1
                state["last_user_message"] = message.content
                await self.emit_agent_message(
                    task_id=task_id,
                    agent_id=agent_id,
                    text=f"Processed user input: {message.content}",
                )

            state["processed_event_ids"].add(event.id)
            processed_this_call += 1

            if fail_after is not None and processed_this_call >= fail_after:
                raise RuntimeError("simulated crash before cursor commit")

        # Atomic checkpoint for this simplified model:
        # only commit after all side effects in batch succeed.
        self.tracker_by_task_agent[key] = pending_events[-1].id
        return processed_this_call

    def snapshot_state(self, task_id: str, agent_id: str) -> dict[str, Any]:
        self._ensure_agent_task(task_id, agent_id)
        state = self.state_by_task_agent[(task_id, agent_id)]
        return {
            "user_message_count": state["user_message_count"],
            "last_user_message": state["last_user_message"],
            "processed_event_ids": sorted(state["processed_event_ids"]),
            "cursor": self.tracker_by_task_agent[(task_id, agent_id)],
        }


async def demo():
    core = InMemoryAgentexCore(agent_ids=["agent-a", "agent-b"])
    task_id = "task-1"

    await core.post_user_message(task_id, "Need help with billing")

    # Crash before cursor commit
    try:
        await core.process_with_cursor(
            task_id=task_id,
            agent_id="agent-a",
            delivered_event_id="e-000001",
            fail_after=1,
        )
    except RuntimeError as error:
        print("simulated failure:", error)

    # Retry and duplicate delivery
    await core.process_with_cursor(task_id, "agent-a", "e-000001")
    await core.process_with_cursor(task_id, "agent-a", "e-000001")

    # Process second agent independently
    await core.process_with_cursor(task_id, "agent-b", "e-000002")

    print("agent-a state:", core.snapshot_state(task_id, "agent-a"))
    print("agent-b state:", core.snapshot_state(task_id, "agent-b"))

    print("ledger:")
    for m in core.messages_by_task[task_id]:
        print(f"  {m.id} | {m.author:5s} | {m.content}")


if __name__ == "__main__":
    asyncio.run(demo())
```

## Part 3: Why this maps to Agentex

1. Durable messages and separate events match the Task/Event split.
2. Tracker cursor mirrors `last_processed_event_id` behavior.
3. Per-agent state keying mirrors `(task_id, agent_id)` isolation.
4. Retry-safe dedupe models at-least-once delivery handling.

## Part 4: Code reading guide (definitive)

Use this exact mapping when reading the implementation.

1. `_ensure_agent_task`:
   - Pattern: lazy initialization.
   - Rule: initialize tracker and state together so they cannot drift.
2. `post_user_message`:
   - Pattern: source-of-truth first.
   - Rule: persist durable message before any event publication.
3. `list_events_after`:
   - Pattern: forward-only cursor traversal.
   - Rule: treat event IDs as monotonic checkpoints.
4. `process_with_cursor`:
   - Pattern: at-least-once transport + idempotent handler.
   - Rule: never trust delivery payload for recovery boundaries; trust committed cursor.
5. `processed_event_ids`:
   - Pattern: idempotency key registry.
   - Rule: dedupe before side effects, not after.
6. cursor commit at end of `process_with_cursor`:
   - Pattern: commit-after-effects.
   - Rule: checkpoint only after all side effects are durable.
7. `(task_id, agent_id)` state key:
   - Pattern: partitioned state ownership.
   - Rule: one agent cannot mutate another agent's state.

## Part 5: Definitive production upgrades (implement in this order)

1. Add durable dedupe storage (replace in-memory `processed_event_ids` with database-backed set/table).
2. Add optimistic concurrency on state updates (`version` field with compare-and-swap).
3. Add transactional outbox for "message append + event publish" atomicity.
4. Add dead letter queue for poison events after retry budget exhaustion.
5. Add replay command to rebuild state from durable message/event history.

## Part 6: NFR and scaling notes

1. Throughput:
   - Partition by `(task_id, agent_id)` so workers can process many tasks in parallel.
2. Latency:
   - Keep event fetch and cursor commit in one short transaction boundary where possible.
3. Reliability:
   - On crash, retry from cursor and rely on dedupe keys.
4. Operability:
   - Track metrics: `event_lag`, `duplicate_event_skips`, `cursor_commit_latency`, `poison_event_count`.
5. Hot partitions:
   - If one task is extremely hot, shard by logical stream segments or enforce rate limiting.

## Part 7: Popular engineering guides applied here

1. Idempotent Consumer Pattern:
   - Every event handler must be safe under duplicate delivery.
2. Exactly-once is a business illusion:
   - Implement logical exactly-once with dedupe keys over at-least-once delivery.
3. Single source of truth:
   - Conversation history lives in the durable message ledger.
4. Commit point clarity:
   - Cursor is the explicit boundary between "replayable" and "committed."
5. Make invalid states unrepresentable:
   - Keying state by `(task_id, agent_id)` prevents cross-agent state collisions by design.
