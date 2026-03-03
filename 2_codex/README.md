# 2_codex: Temporal Workflow Inference Lab

This folder is a hands-on lab to learn how `from temporalio import workflow` is used in AgentEx and infer how it likely works under the hood.

## What you will do

1. Trace real runtime flow in this repo:
- ACP task create -> Temporal `start_workflow(...)` -> your `@workflow.run`
- ACP event send -> Temporal `signal(...)` -> your `@workflow.signal`
2. Build a tiny decorator system that mimics `@workflow.defn`, `@workflow.run`, and `@workflow.signal`.
3. Validate your mental model with a runnable checker.

## Suggested order

1. `exercises/01_trace_create_path.md`
2. `exercises/02_trace_signal_path.md`
3. `exercises/03_build_mini_temporal.md`

## Optional setup

You do not need `temporalio` installed for these exercises.

Run checker for the coding exercise:

```powershell
python .\2_codex\code\mini_temporal_check.py
```
