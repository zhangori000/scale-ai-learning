# Official Learning Guide: Agentex + Agentex Python (v1)

## Goal
Understand the project end to end without hidden assumptions:
- What problem it solves
- Why the team open sourced it
- How `scale-agentex` and `scale-agentex-python` fit together
- How requests move through the system
- Where to read code in the right order

## What each repo is

| Repo | Purpose | Main role in system |
|---|---|---|
| `scale-agentex` | Agentic infrastructure platform | Backend API, persistence, routing, streaming, Temporal infra, developer UI |
| `scale-agentex-python` | SDK + CLI + examples | Build agent code, scaffold projects, run ACP servers, call API from Python |

## Why this exists (project intent)
Start here to avoid guessing intent:
- `scale-agentex/README.md`
- `scale-agentex/agentex/docs/docs/index.md`
- `scale-agentex/agentex/docs/docs/getting_started/agentex_overview.md`

Core message from maintainers:
- Agents are "just code"
- Infrastructure complexity is abstracted away
- One protocol (ACP) across simple and complex agents
- Open source was created to share production lessons and give teams local/self-service development

## Dependency-safe learning order
Follow this order exactly. Do not skip ahead.

### Phase 1: Product and architecture map
Read:
- `scale-agentex/README.md`
- `scale-agentex/agentex/docs/docs/concepts/architecture.md`
- `scale-agentex/agentex/docs/docs/getting_started/choose_your_agent_type.md`
- `scale-agentex/agentex/docs/docs/getting_started/project_structure.md`

Outcome:
- You can explain Sync vs Async Base vs Async Temporal
- You can draw the high-level flow: Client -> Agentex -> Agent code -> Agentex -> Client

### Phase 2: Core domain concepts (must know before source code)
Read:
- `scale-agentex/agentex/docs/docs/concepts/agents.md`
- `scale-agentex/agentex/docs/docs/concepts/task.md`
- `scale-agentex/agentex/docs/docs/concepts/task_message.md`
- `scale-agentex/agentex/docs/docs/concepts/events.md`
- `scale-agentex/agentex/docs/docs/concepts/state.md`
- `scale-agentex/agentex/docs/docs/concepts/streaming.md`

Outcome:
- You can define task, message, event, state, stream lifecycle
- You understand that state is scoped to `(task_id, agent_id)`

### Phase 3: Local runtime stack (infrastructure reality)
Read:
- `scale-agentex/agentex/docker-compose.yml`
- `scale-agentex/agentex/src/api/app.py`

Focus on:
- Services: Postgres, Mongo, Redis, Temporal, API, worker, OTEL
- Which process owns what responsibility

Outcome:
- You can explain what must be running for local development
- You know which ports correspond to API, UI, Temporal UI

### Phase 4: Backend layering in `scale-agentex`
Read in this order:
1. `scale-agentex/agentex/src/api/routes/`
2. `scale-agentex/agentex/src/domain/use_cases/`
3. `scale-agentex/agentex/src/domain/services/`
4. `scale-agentex/agentex/src/domain/repositories/`
5. `scale-agentex/agentex/src/domain/entities/`

Suggested first chain to trace:
- `src/api/routes/tasks.py`
- `src/domain/use_cases/tasks_use_case.py`
- `src/domain/services/task_service.py`

Outcome:
- You can trace one request from HTTP route to persistence and ACP forwarding

### Phase 5: Understand the split inside `scale-agentex-python`
Read:
- `scale-agentex-python/README.md`
- `scale-agentex-python/api.md`
- `scale-agentex-python/src/agentex/__init__.py`
- `scale-agentex-python/pyproject.toml`

Key point:
- This repo has two major layers:
  - Generated REST client (`src/agentex/resources`, `src/agentex/types`)
  - Hand-written agent developer stack (`src/agentex/lib/*`, CLI, FastACP, ADK)

Outcome:
- You can explain when you are using API client APIs vs ADK/FastACP APIs

### Phase 6: ACP implementation internals
Read:
- `scale-agentex-python/src/agentex/lib/sdk/fastacp/fastacp.py`
- `scale-agentex-python/src/agentex/lib/sdk/fastacp/impl/sync_acp.py`
- `scale-agentex-python/src/agentex/lib/sdk/fastacp/impl/async_base_acp.py`
- `scale-agentex-python/src/agentex/lib/sdk/fastacp/impl/temporal_acp.py`

Outcome:
- You can explain how ACP type selection is made
- You can explain what handlers are required per agent type

### Phase 7: Learn by runnable examples (do not invent abstractions first)
Read:
- `scale-agentex-python/examples/tutorials/README.md`

Run in this order:
1. `examples/tutorials/00_sync/000_hello_acp`
2. `examples/tutorials/00_sync/010_multiturn`
3. `examples/tutorials/00_sync/020_streaming`
4. `examples/tutorials/10_async/00_base/000_hello_acp`
5. `examples/tutorials/10_async/00_base/010_multiturn`
6. `examples/tutorials/10_async/00_base/020_streaming`
7. `examples/tutorials/10_async/10_temporal/000_hello_acp`
8. Then advanced Temporal tutorials

Outcome:
- You can feel the operational difference between sync, async base, temporal

### Phase 8: Production mental model (long-running agents)
Read:
- `scale-agentex-python/examples/demos/procurement_agent/README.md`

Outcome:
- You understand why Temporal + event-driven workflows matter for real business processes

## Runtime order of operations (single interaction)

### Sync agent path
1. Client sends message to Agentex API.
2. Backend persists/loads task and message context.
3. Backend forwards request to agent ACP `on_message_send`.
4. Agent returns message or stream updates.
5. Backend streams response to client and persists final output.

### Async Base path
1. Client action creates an event.
2. Event is delivered to `on_task_event_send`.
3. Agent decides what to persist with `adk.messages.create`.
4. Backend streams task updates/events to subscribers.

### Async Temporal path
1. Task create starts workflow.
2. Incoming events are routed as workflow signals.
3. Workflow and activities execute durably.
4. Messages are emitted through ADK APIs.
5. System survives restarts using Temporal persistence.

## Minimal no-assumption workflow for every new topic
Use this checklist whenever you learn a new concept (state, streaming, events, tracker, etc.):
1. Read concept doc first.
2. Read API surface (`api.md` or route schema) second.
3. Read implementation files third.
4. Run smallest matching tutorial fourth.
5. Write a 5-line summary in your own words.
6. Only then move to advanced variants.

## Known gap to keep in mind
In current docs, first-class external storage references in state are marked as "coming soon":
- `scale-agentex/agentex/docs/docs/concepts/state.md`

So if you see exercises introducing richer external ref lifecycle, treat those as forward-looking architecture practice, not guaranteed current backend behavior.

## Definition of done for this v1 guide
You are ready for deeper work when you can answer these without looking up docs:
1. Why does Agentex separate infrastructure from agent business logic?
2. How does Sync vs Async Base vs Temporal change handler design?
3. What is the difference between events and messages?
4. How is state scoped?
5. How do the two repos collaborate during local development?

---

## Lab Modules
- `0_protocol_contract_validation_lab`
- `1_agentex_types_model_lab`

If you want, next step can be `v2`: a concrete 7-day study sprint with daily checkpoints, exact files to read each day, and small validation tasks after each section.
