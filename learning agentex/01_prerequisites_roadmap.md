# Agentex Prerequisites Roadmap

This is the minimum knowledge needed before Agentex code will feel readable.

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

## Priority 3: Helpful but optional at first

- Kubernetes/Helm basics (for production deployment understanding)
- OpenTelemetry basics
- CI/CD pipelines

## Fast-start path if you are time constrained

If you only have ~6 focused hours:

1. 90 min: Python async + `uv` basics
2. 90 min: Docker Compose basics
3. 90 min: Agentex docs sections:
   - Getting started overview
   - Choose agent type
   - Agents/tasks/messages concepts
4. 90 min: Run stack locally + create one sync agent

Then proceed to `02_repo_map_and_first_navigation.md`.
