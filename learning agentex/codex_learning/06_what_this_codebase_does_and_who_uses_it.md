# What This Codebase Actually Does

This file answers the direct questions:

1. Is this a single product?
2. Is this only infrastructure?
3. Who is it for?

## Short answer

`scale-agentex` is a **platform codebase** for building and running many AI agents.  
It is mostly **infrastructure + developer tooling**, not a single end-user app.

So:

- It is not "just one chatbot product."
- It is also not "just random infra utilities."
- It is a coherent agent platform made of multiple components.

## Super-direct FAQ (your exact questions)

## "What is an agent in this repo?"

An **agent** is your Python application logic that handles user/task input and produces outputs.

In Agentex terms, an agent is usually:

- code files (for example `project/acp.py`)
- configuration (`manifest.yaml`)
- a running process started by CLI

It is not a terminal window by itself.

## "Are agents terminals on my computer?"

No.

- A **terminal** is just a control window where you type commands.
- A **process** is the actual running program.

You often start an agent process from a terminal command like:

```bash
agentex agents run --manifest manifest.yaml
```

You can run one or many agent processes, using one terminal tab or many.  
The terminal is only how you launch/manage them.

## "Are agents like a server thing?"

Usually yes at runtime.

When you run an agent, it behaves like a small server endpoint behind ACP handlers, and the Agentex backend can call it.

So the clean mental model is:

- **conceptually**: agent = your business logic
- **runtime form**: a running process exposing standard handler entrypoints

## "What is protocol (ACP)?"

ACP = **Agent-to-Client Protocol**.

It is a contract that defines:

- what input shape the agent receives
- what output/event shape it can return
- which handler functions must exist

Examples:

- Sync style: `on_message_send`
- Async style: `on_task_create`, `on_task_event_send`, `on_task_cancel`

Why this matters: clients can call different agents in the same way because all follow the same protocol.

## "What does runtime convention mean?"

Runtime convention means shared rules all agents follow while running.

Examples:

- standard task/message/event model
- standard handler names/signatures (ACP)
- standard way the platform routes and tracks work
- consistent observability/tracing behavior

Because of this, swapping from Agent A to Agent B is easier for clients and tooling.

## Tiny mental diagram

```text
[Terminal] --starts--> [Agent Process]
                           ^
                           | ACP calls
[UI/Client] -> [Agentex Backend Server] -> [Your Agent Logic]
```

## Is it a single product or infrastructure?

Both, depending on perspective:

- As a **developer**, you see it as an infrastructure platform you build on top of.
- As **Scale**, Agentex is a product family:
  - open-source local development edition (this repo)
  - enterprise managed edition inside Scale's GenAI platform

In this repo, the main value is the open-source edition.

## What pieces are in this repo?

## 1) Agentex Server (`scale-agentex/agentex`)

What it does:

- receives API requests from UI/clients
- routes tasks/messages to agent code via ACP
- persists runtime artifacts (messages/state/events)
- supports async workflow patterns and streaming

Think of it as: the runtime engine.

## 2) Agentex UI (`scale-agentex/agentex-ui`)

What it does:

- lets you discover agents
- create tasks and chat with agents
- inspect traces/history/errors

Think of it as: the cockpit/debug console.

## 3) SDK + CLI (`agentex-sdk`)

What it does:

- SDK: Python toolkit for writing agent logic against Agentex contracts
- CLI: terminal commands to scaffold/run/manage agents

Think of it as: developer tools to create agents quickly.

## 4) Local infrastructure composition

What it does:

- spins up required services (Postgres, Redis, MongoDB, Temporal, OTEL, API, worker)
- gives you a realistic local environment close to production architecture

Think of it as: the plumbing pack.

## What does this enable you to build?

Not one app. A **portfolio of agents** that share the same runtime conventions.

Examples of things teams build:

- support/ops copilots that keep context across many turns
- long-running back-office workflows that pause/resume
- multi-agent workflows where specialized agents coordinate
- internal automation agents integrated with existing APIs/databases/human approvals

## Who would use this?

## Primary users

1. Backend/full-stack engineers building production agent features
2. Platform/infra teams standardizing how many internal agents are hosted and observed
3. AI application teams that need long-running or durable workflows
4. Enterprises that need more control than "single prompt in, single response out"

## Secondary users

1. Individual developers learning agent architecture beyond simple chatbots
2. Teams prototyping locally before enterprise rollout

## Who should probably NOT start with this

If you only need:

- one tiny chatbot demo
- no persistence
- no async workflows
- no multi-agent coordination

then this stack may feel heavy. A simpler framework may be faster for that narrow case.

## How to decide if Agentex fits your use case

Use Agentex when at least one is true:

1. You need agents to run longer than a single request/response.
2. You need durable retries/resume behavior after failures.
3. You need standardized invocation across many agents.
4. You need traceability/observability and structured task/message handling.
5. You expect to scale from one agent to many agents.

If none are true, Agentex might be overkill for your current phase.

## Practical framing for your learning

When reading this repo, ask:

1. "What part helps me write agent business logic?"
2. "What part is runtime plumbing I can rely on?"
3. "What part helps me test/debug/operate agents?"

If you keep that frame, the codebase becomes much less blob-like.
