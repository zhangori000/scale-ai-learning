# Codex Comments Exercise 31: Idempotent Temporal Fanout with Durable Intent

This is a stricter design than basic "check then insert".

## Goal

Implement an event fanout that safely handles retries and mid-flight crashes by:

1. generating deterministic keys per child task,
2. storing durable "intent" records before workflow start,
3. starting Temporal with duplicate-safe workflow ID policy,
4. making retries converge instead of duplicating work.

## Starter Code

```python
from dataclasses import dataclass


@dataclass
class Event:
    id: str
    create_tasks: list[str]


@dataclass
class TaskIntent:
    idempotency_key: str
    task_name: str
    workflow_id: str
    started: bool = False


class DuplicateKeyError(Exception):
    pass


class MockIntentStore:
    def __init__(self):
        self.by_key: dict[str, TaskIntent] = {}

    def get(self, key: str) -> TaskIntent | None:
        return self.by_key.get(key)

    def create_intent(self, intent: TaskIntent):
        if intent.idempotency_key in self.by_key:
            raise DuplicateKeyError(intent.idempotency_key)
        self.by_key[intent.idempotency_key] = intent

    def mark_started(self, key: str):
        self.by_key[key].started = True


class WorkflowAlreadyStarted(Exception):
    pass


class MockTemporal:
    def __init__(self):
        self.started_workflow_ids: set[str] = set()

    def start_workflow(self, workflow_id: str, duplicate_policy: str = "REJECT_DUPLICATE"):
        if duplicate_policy == "REJECT_DUPLICATE" and workflow_id in self.started_workflow_ids:
            raise WorkflowAlreadyStarted(workflow_id)
        self.started_workflow_ids.add(workflow_id)


class EventsUseCase:
    def __init__(self, intents: MockIntentStore, temporal: MockTemporal):
        self.intents = intents
        self.temporal = temporal

    def _idempotency_key(self, event_id: str, task_name: str) -> str:
        """
        TODO:
        Return deterministic key, e.g. f"{event_id}::{task_name}".
        """
        pass

    def _workflow_id(self, idempotency_key: str) -> str:
        """
        TODO:
        Return deterministic workflow id from key.
        """
        pass

    def process_event(self, event: Event, fail_after_creates: int | None = None):
        """
        TODO:
        For each task_name in event.create_tasks:
        1. Build deterministic idempotency key and workflow_id.
        2. If intent exists and started=True: skip.
        3. If intent does not exist: create intent (durable write).
        4. Optionally simulate crash after N intent creates (before starts).
        5. Start Temporal workflow with duplicate_policy='REJECT_DUPLICATE'.
        6. Mark intent started=True.
        7. If duplicate start exception occurs, treat as idempotent success and mark started.
        """
        pass


def demo():
    intents = MockIntentStore()
    temporal = MockTemporal()
    use_case = EventsUseCase(intents, temporal)

    event = Event(id="evt_2026_01", create_tasks=["transcribe_audio", "summarize"])

    print("Attempt 1 (crash after creating one intent)")
    try:
        use_case.process_event(event, fail_after_creates=1)
    except RuntimeError as e:
        print("  simulated crash:", e)

    print("Attempt 2 (retry)")
    use_case.process_event(event)

    print("Attempt 3 (duplicate retry)")
    use_case.process_event(event)

    print("Started workflow ids:", sorted(temporal.started_workflow_ids))
    print("Intent states:", {k: v.started for k, v in intents.by_key.items()})


if __name__ == "__main__":
    demo()
```

## Expected Behavior

1. No duplicate workflow starts across retries.
2. Crash between "intent create" and "workflow start" is recoverable on retry.
3. Final state has one started intent per fanout child.

