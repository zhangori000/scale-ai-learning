# 14-Day Study Plan for Agentex

Use this if you want a structured path from zero context to productive contributor.

## Week 1: Understand the platform and run it

## Day 1

- Read `learning agentex/README.md`
- Read `01_prerequisites_roadmap.md`
- Outcome: explain Agentex product in 3 sentences

## Day 2

- Read:
  - `scale-agentex/README.md`
  - `scale-agentex/agentex/docs/docs/getting_started/agentex_overview.md`
- Outcome: draw request flow (client -> server -> agent -> client)

## Day 3

- Read:
  - `scale-agentex/agentex/docs/docs/agent_types/overview.md`
  - `scale-agentex/agentex/docs/docs/getting_started/choose_your_agent_type.md`
- Outcome: know when to choose sync vs async vs Temporal

## Day 4

- Read:
  - `scale-agentex/agentex/docs/docs/concepts/agents.md`
  - `scale-agentex/agentex/docs/docs/concepts/task.md`
- Outcome: explain agent/task/message/event/state clearly

## Day 5

- Execute `03_first_run_playbook.md`
- Outcome: local stack and UI running

## Day 6

- Create first agent with `agentex init`
- Send test messages from UI
- Outcome: one working agent connected to local Agentex

## Day 7

- Add a simple external API/tool call in your agent
- Outcome: understand where business logic lives

## Week 2: Move from "it runs" to "I can reason about architecture"

## Day 8

- Read UI docs: `scale-agentex/agentex-ui/README.md`
- Outcome: know where chat/tasks/traces UI logic lives

## Day 9

- Inspect backend service map in `scale-agentex/agentex/docker-compose.yml`
- Outcome: explain why Postgres/Redis/Mongo/Temporal are all present

## Day 10

- Read streaming + state docs:
  - `concepts/streaming.md`
  - `concepts/state.md`
- Outcome: know how multi-turn memory and live updates work

## Day 11

- Read Temporal docs:
  - `temporal_development/overview.md`
  - `agent_types/async/temporal.md`
- Outcome: understand durable workflow value

## Day 12

- Convert your simple sync example to async base or Temporal skeleton
- Outcome: compare complexity and behavior

## Day 13

- Observe traces in UI for both versions
- Outcome: connect execution behavior with architecture

## Day 14

- Write your own internal "Agentex starter note" with:
  - product definition
  - repo map
  - startup commands
  - sync vs async decision rule
- Outcome: you can onboard someone else

## Completion rubric

You are "ready to build" when you can do all:

- Start local stack without trial-and-error guessing
- Scaffold and run a new agent
- Explain ACP/task/message/state to another engineer
- Pick an agent type intentionally
- Debug a failing run using logs + UI traces
