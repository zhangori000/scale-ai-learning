# Agentex Prerequisites Roadmap

This is the minimum knowledge needed before Agentex code will feel readable.

## Zero-jargon foundation (read this first)

If terms like SDK/CLI/backend feel abstract, use these definitions:

If you are still asking "what does this codebase even do?", read this first:

- `learning agentex/06_what_this_codebase_does_and_who_uses_it.md`

## Product vs infrastructure (quick orientation)

Agentex in this repo is best understood as a **developer platform**:

- not a single end-user app
- not only low-level infra scripts
- a platform for building, running, and observing many agents consistently

Who typically uses it:

1. Engineers building agent-powered product features
2. Platform teams standardizing agent runtime patterns
3. Teams needing long-running/durable workflows (not just one-shot chat responses)

| Term | Plain English | In this repo |
|---|---|---|
| **SDK** | A code toolkit you install so your code can call/use a platform more easily | `agentex-sdk` (Python package + helper APIs) |
| **CLI** | A command-line app you run in terminal (`something command ...`) | `agentex init`, `agentex agents run ...` |
| **Backend server** | A long-running program that receives requests and does work | `scale-agentex/agentex` (API on `localhost:5003`) |
| **Frontend** | The website/UI you click/type into | `scale-agentex/agentex-ui` (usually `localhost:3000`) |
| **Agent** | Your business logic app that processes tasks/messages | Usually generated via `agentex init` and run with `agentex agents run` |
| **Terminal** | Text window used to run commands | PowerShell/WSL tabs where you launch services |
| **Process** | The actual running program started by a command | Backend API process, UI dev process, agent process |
| **API** | The request/response contract between programs | UI and SDK both call Agentex API |
| **Protocol (ACP)** | A strict set of rules for how agents are called and what they return | Agent handlers follow ACP patterns |
| **Runtime convention** | Shared rules that make all agents run/interact consistently | Standard handlers, message/task model, routing behavior |
| **Infrastructure layer** | Shared plumbing that many apps/services depend on | Agentex handles routing, persistence, streaming, observability, async workflow support |
| **Task** | One conversation/workflow session | A thread container for messages/state |
| **Message** | One unit in a task conversation | User or agent message inside a task |
| **Temporal durability** | Ability to pause/resume/recover long workflows after failures | Used by async Temporal agent type |

## What "infrastructure layer" means here

Agentex is not "the brain" of your agent.  
Your Python code is the brain. Agentex is the runtime platform around it.

Think:

- Your code = restaurant chef
- Agentex = kitchen + tickets + waitstaff + storage + monitoring

Without Agentex, you must build all plumbing yourself. With Agentex, you mainly write business logic.

## One concrete request flow (end-to-end)

1. You type in the UI (`agentex-ui`).
2. UI calls Agentex backend API (`agentex` server).
3. Backend routes request to your agent handler through ACP rules.
4. Your agent code runs and returns output.
5. Backend stores task/messages/state and streams response back to UI.

This is the core loop you should keep in mind while reading docs.

## What you code vs what Agentex handles

You mainly code:

- agent logic
- tool/API integrations
- prompting/workflow rules for your use case

Agentex mainly handles:

- standardized invocation protocol (ACP)
- task/message persistence
- streaming and tracing surfaces
- async workflow runtime support
- local dev orchestration pattern (plus deployment patterns)

## Priority 0: Core mental model (must understand first)

1. Agentex is an **infrastructure layer**, not a single agent app.
2. Your code is "the agent"; Agentex standardizes how clients call it.
3. Main product pieces:
   - SDK + CLI (`agentex-sdk`)
   - Agentex Server backend (`scale-agentex/agentex`)
   - Agentex UI frontend (`scale-agentex/agentex-ui`)
4. Agent execution styles:
   - Sync (simple request/response)
   - Async base
   - Async with Temporal durability

If this model is clear, most docs become easier.

## Priority 0.5: Learn the 6 essential terms by heart

Before deep code reading, make sure you can explain each in one sentence:

1. SDK
2. CLI
3. Backend server
4. API
5. ACP
6. Task

If you cannot explain these, pause and re-read the table above.

## Priority 1: Must-know technical skills

## 1) Python 3.12 basics + async/await

Why it matters in this repo:

- Backend and agent code are Python.
- Agent handlers are async.

Minimum topics:

- virtual envs
- package management with `uv`
- `async def`, `await`, async generators
- reading type hints

Quick self-check:

- Can you explain what an async function returns?
- Can you run `uv venv`, `uv sync`, activate env?

## 2) HTTP APIs + JSON + REST basics

Why it matters:

- Agentex Server exposes APIs used by UI and SDK.
- Tasks/messages/events flow through API contracts.

Minimum topics:

- HTTP verbs
- request/response payloads
- status codes

Self-check:

- Can you read an API endpoint and predict payload/response?

## 3) Docker + Docker Compose

Why it matters:

- Local stack depends on Docker services (DBs, Temporal, backend).

Minimum topics:

- images vs containers
- `docker compose up/down/logs`
- ports, volumes, networks

Self-check:

- Can you identify which service is failing from compose logs?

## 4) Datastore basics (Postgres, Redis, MongoDB)

Why it matters:

- Local stack includes all three.
- Agentex uses multiple stores for different runtime concerns.

Minimum topics:

- relational vs document vs cache/queue semantics
- connection strings
- basic CRUD mental model

## 5) Temporal basics (important for advanced Agentex)

Why it matters:

- Durable long-running workflows rely on Temporal.

Minimum topics:

- workflow vs activity
- durability and replay concepts
- worker process role

Self-check:

- Can you explain why Temporal is useful for "wait hours/days then resume" jobs?

## 6) TypeScript/React basics (for `agentex-ui`)

Why it matters:

- UI is Next.js + React + TypeScript.
- You will use it to test/observe tasks and traces.

Minimum topics:

- React component basics
- hooks basics
- TypeScript types/interfaces

## Priority 2: Important Agentex concepts

Read these terms until they are intuitive:

- ACP (Agent-to-Client Protocol)
- Agent
- Task
- Task message
- Event
- State
- Streaming
- Trace/span
- Sync vs async vs Temporal agent types

## 20-minute starter exercise (highly recommended)

Do this once before any heavy reading:

1. Open `scale-agentex/README.md`
2. Find where it mentions:
   - SDK/CLI
   - server
   - UI
3. Write 4 lines in your own words:
   - "SDK is ..."
   - "CLI is ..."
   - "Backend server is ..."
   - "Infrastructure layer means ..."

If your 4 lines are clear, the rest of this roadmap will feel much easier.

## Priority 3: Helpful but optional at first

- Kubernetes/Helm basics (for production deployment understanding)
- OpenTelemetry basics
- CI/CD pipelines

## Fast-start path if you are time constrained

If you only have ~6 focused hours:

1. 45 min: zero-jargon foundation in this file + 20-minute exercise
2. 90 min: Python async + `uv` basics
3. 90 min: Docker Compose basics
4. 90 min: Agentex docs sections:
   - Getting started overview
   - Choose agent type
   - Agents/tasks/messages concepts
5. 45 min: Run stack locally + create one sync agent

Then proceed to `02_repo_map_and_first_navigation.md`.
