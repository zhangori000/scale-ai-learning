# Agentex Deep Dive: The Repo Map

This guide maps the high-level concepts mentioned in the `scale-agentex` documentation (and these exercises) to the **actual file paths** in the Scale AI repository.

---

## 1. The Core Entities (The "What")
Where are the data models and schemas defined?

| Concept | Repository Path | Description |
| :--- | :--- | :--- |
| **Events** | `agentex/src/domain/entities/events.py` | The raw input data from external systems. |
| **Tasks** | `agentex/src/domain/entities/tasks.py` | The units of work that the platform manages. |
| **Task Messages** | `agentex/src/domain/entities/task_messages.py` | Internal communication between the platform and the Agent. |
| **States** | `agentex/src/domain/entities/states.py` | How Agentex persists the status of a long-running process. |
| **Pydantic Schemas** | `agentex/src/api/schemas/` | The JSON formats used for incoming API requests. |

---

## 2. Infrastructure & Orchestration (The "How")
How does Agentex ensure things are reliable and scalable?

| Concept | Repository Path | Description |
| :--- | :--- | :--- |
| **Temporal Workers** | `agentex/src/temporal/run_worker.py` | The entry point for the processes that actually execute tasks. |
| **Workflows** | `agentex/src/temporal/workflows/` | The "Durable" logic that survives crashes and manages retries. |
| **Activities** | `agentex/src/temporal/activities/` | The "Leaf" tasks (like calling an LLM or writing to a DB) that Workflows call. |
| **Idempotency** | `agentex/src/api/routes/events.py` | Look for `idempotency_key` logic here to prevent double-processing. |

---

## 3. Business Logic (The "Brain")
Where does the actual "Agentex magic" happen?

| Concept | Repository Path | Description |
| :--- | :--- | :--- |
| **1:1 / 1:M Mapping** | `agentex/src/domain/use_cases/events_use_case.py` | Logic that turns a single event into one or more tasks. |
| **Streaming / SSE** | `agentex/src/domain/use_cases/streams_use_case.py` | How "Deltas" (partial updates) are pushed to the UI in real-time. |
| **API Endpoints** | `agentex/src/api/routes/` | FastAPI routes that bridge the outside world to the internal logic. |
| **Tracing** | `agentex/src/api/health_interceptor.py` | Implementation of trace propagation (like Exercise 27). |

---

## 4. Key Utilities & Tooling
The "Grease" in the machine.

| Concept | Repository Path | Description |
| :--- | :--- | :--- |
| **Adapters** | `agentex/src/adapters/` | Connections to external systems (Postgres, Redis, Temporal). |
| **Context Management** | `agentex/src/api/authentication_middleware.py` | Where `ContextVars` are often set for the current request. |
| **Configuration** | `agentex/src/config/` | How the app reads `.env` files and environment variables. |

---

## Pro-Tip for Navigating the Repo
- **The "src" folder** is structured using **Clean Architecture** (Domain -> Use Cases -> Adapters).
- If you want to see how a request flows:
  1. Start at `src/api/routes/` (The entry).
  2. Follow the call to `src/domain/use_cases/` (The logic).
  3. See how it interacts with `src/temporal/` (The orchestration).
  4. Look at `src/domain/entities/` (The data it saves).
