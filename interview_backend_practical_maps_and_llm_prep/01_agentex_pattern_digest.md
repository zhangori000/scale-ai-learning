# Agentex Pattern Digest

These are the backend patterns that show up repeatedly in `scale-agentex` and `scale-agentex-python`, and are worth copying into interview answers.

| Pattern | Where it shows up | What to copy in interview |
|---|---|---|
| Thin entrypoint, real orchestration in a service | `scale-agentex/agentex/src/domain/use_cases/tasks_use_case.py` and `scale-agentex/agentex/src/domain/services/task_service.py` | Keep the API/controller layer thin. Put retries, state changes, side effects, and sequencing in a service class. |
| Ports around side effects | `scale-agentex/agentex/src/adapters/http/port.py`, `scale-agentex/agentex/src/adapters/crud_store/port.py`, `scale-agentex/agentex/src/adapters/temporal/port.py` | Define interfaces for Google Maps, LLM provider, Mongo, email, and CSV storage. This makes testing and failure handling much cleaner. |
| Typed boundary models | `scale-agentex/agentex/src/domain/entities/tasks.py` and many files under `scale-agentex-python/src/agentex/types/` | Use explicit request/response models. Avoid passing loose dicts through your whole system. |
| Shared dependency setup and pooled clients | `scale-agentex/agentex/src/config/dependencies.py` and `scale-agentex/agentex/src/adapters/http/adapter_httpx.py` | Reuse HTTP clients, DB pools, and rate limiters. Do not create a fresh client per request. |
| Explicit retryability classification | `scale-agentex-python/examples/demos/procurement_agent/project/workflow.py` and `.../activities/activities.py` | Separate retryable provider failures from bad input/data problems. Retry 429 and transient 5xx. Do not retry invalid tasks forever. |
| Pagination as an explicit contract | `scale-agentex/agentex/src/utils/pagination.py` and `scale-agentex-python/src/agentex/resources/tasks.py` | Make pagination first-class. Return cursor or page token metadata, not just raw arrays. |
| Tests mock external boundaries, not core logic | `scale-agentex/agentex/tests/unit/services/test_task_service.py` and `scale-agentex-python/tests/test_client.py` | Unit test orchestration with fake adapters. Assert retries, ordering, dedupe, and fallback behavior. |
| Generated or structured client shape | `scale-agentex-python/src/agentex/_client.py`, `resources/`, and `types/` | For external APIs, think in terms of a client plus typed resource methods, not raw `requests.get()` calls sprinkled everywhere. |

## Practical translation

For these interview problems, a strong Agentex-style answer usually looks like this:

1. A request model or domain entity
2. A service class that owns orchestration
3. A small set of ports for external dependencies
4. One adapter per external system
5. Retry, rate limit, and pagination logic at the adapter or service boundary
6. Tests against fake adapters

## What not to copy

- Do not overbuild Temporal into every answer. Use it only when the workflow is long-running, resumable, or failure-prone enough to justify it.
- Do not make repositories talk directly to third-party APIs. Keep storage and external providers separate.
- Do not hide key assumptions. State them up front, especially when the prompt is underspecified.
