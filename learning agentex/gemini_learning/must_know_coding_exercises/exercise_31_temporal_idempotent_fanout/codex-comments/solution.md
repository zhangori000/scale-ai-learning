# Codex Comments Solution 31: Idempotent Temporal Fanout with Durable Intent

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
        return f"{event_id}::{task_name}"

    def _workflow_id(self, idempotency_key: str) -> str:
        # Deterministic workflow ID lets Temporal duplicate policy enforce uniqueness.
        return f"wf::{idempotency_key}"

    def process_event(self, event: Event, fail_after_creates: int | None = None):
        created_this_call = 0

        for task_name in event.create_tasks:
            key = self._idempotency_key(event.id, task_name)
            existing = self.intents.get(key)

            if existing and existing.started:
                print(f"[idempotent-hit] {task_name} already started")
                continue

            if not existing:
                workflow_id = self._workflow_id(key)
                try:
                    self.intents.create_intent(
                        TaskIntent(
                            idempotency_key=key,
                            task_name=task_name,
                            workflow_id=workflow_id,
                            started=False,
                        )
                    )
                    created_this_call += 1
                    print(f"[intent] created {task_name} ({key})")
                except DuplicateKeyError:
                    # Another worker won the race: load the winner's intent.
                    pass

            if fail_after_creates is not None and created_this_call >= fail_after_creates:
                raise RuntimeError("crash after intent creation, before workflow start")

            intent = self.intents.get(key)
            if intent is None:
                raise RuntimeError(f"intent unexpectedly missing for key={key}")

            if intent.started:
                continue

            try:
                self.temporal.start_workflow(
                    workflow_id=intent.workflow_id,
                    duplicate_policy="REJECT_DUPLICATE",
                )
                print(f"[temporal] started {intent.workflow_id}")
            except WorkflowAlreadyStarted:
                # Treat duplicate-start as idempotent success.
                print(f"[temporal] duplicate-start treated as success: {intent.workflow_id}")
            finally:
                self.intents.mark_started(key)


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

## Why this matches real Agentex patterns

1. Temporal retries require idempotent side effects (documented in temporal development guides).
2. Deterministic workflow IDs plus duplicate rejection mirrors SDK Temporal duplicate policy controls.
3. Durable intent-before-start avoids ghost work and enables recovery after mid-flight crash.
4. Idempotent retries converge to one started workflow per fanout child.

