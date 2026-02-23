# Learning Agentex (Start Here)

If `scale-agentex` feels like a giant blob, this folder is your orientation pack.

## First, what is Agentex as a product?

Agentex is **not** one chatbot app.  
Agentex is an **agent infrastructure framework**: it helps developers build, run, and scale many AI agents with a consistent interface.

Plain-language view:

- You write agent business logic in Python.
- Agentex gives you a standard protocol/API surface (ACP) to invoke agents.
- Agentex handles agent runtime concerns: task/message flow, async workflows, state, streaming, tracing, and deployment patterns.

From the Scale launch post (published **November 13, 2025**), Agentex is positioned as open-source infrastructure for long-running, asynchronous enterprise agents.

## What this folder gives you

1. `01_prerequisites_roadmap.md`  
What to learn before diving into code, in priority order.

2. `02_repo_map_and_first_navigation.md`  
A map of the repo so you know what each major folder does.

3. `03_first_run_playbook.md`  
Hands-on commands/checkpoints to run the stack and your first agent.

4. `04_study_plan_14_days.md`  
A concrete two-week learning path with outcomes each day.

5. `05_sources.md`  
Primary links and local docs used to build this guide.

## Recommended read order

1. This file
2. `01_prerequisites_roadmap.md`
3. `02_repo_map_and_first_navigation.md`
4. `03_first_run_playbook.md`
5. `04_study_plan_14_days.md`

## Expected outcome after this pack

You should be able to answer:

- What product Agentex is, and what it is not
- Which part of the repo is backend infra vs frontend vs your own agent code
- How to run the local stack and test one agent end-to-end
- When to choose sync vs async/Temporal agent patterns
