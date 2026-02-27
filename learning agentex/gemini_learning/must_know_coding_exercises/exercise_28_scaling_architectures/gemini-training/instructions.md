# Gemini Training: Scaling Agentic Architectures (Sync vs. Async vs. Durable)

## Goal
Master the architectural patterns used in `scale-agentex` to handle high-concurrency workloads, focusing on how Temporal's **Durable Execution** solves the "fragile async" problem.

## The Scaling Problem in Agentex
In an AI agent system, "scaling" is harder than in a typical REST API. Why?
1. **Long-running tasks**: LLM calls and tool executions can take seconds or minutes.
2. **State management**: If a task is interrupted, you can't just restart it if it has side effects (like sending an email or charging a card).
3. **Concurrency bottlenecks**: Too many parallel tasks can exhaust database connections or rate-limit the LLM provider.

## What To Read
- `scale-agentex/agentex/docs/docs/concepts/architecture.md` (System layers)
- `scale-agentex/agentex/docs/docs/concepts/agents.md` (Scaling section)
- `scale-agentex-python/src/agentex/lib/core/temporal/workers/worker.py` (Worker configuration)
- `scale-agentex-python/src/agentex/lib/core/temporal/services/temporal_task_service.py` (Workflow submission)

## Tasks
1. **Analyze the 4-Layer Scaling Model**:
    - **Deployment**: How pods are scaled.
    - **Queue**: How Temporal decouples ingest from execution.
    - **Worker**: How concurrency is managed within a single pod.
    - **Data-Plane**: How the database and locks constrain total throughput.
2. **Code Evidence Table**: Identify specific file paths and lines in the codebase that implement these scaling controls.
3. **The "Durable" Difference**: Explain why `asyncio.gather` is insufficient for production agents and how Temporal's `Worker` pattern replaces it.
4. **Failure Modes**: Identify 3 scenarios where scaling fails (e.g., DB pool exhaustion) and propose concrete mitigations using Agentex/Temporal features.
5. **Implementation**: Complete the `TemporalSimulation` in the parent folder's `01_instructions.md` or a new specialized version in a subfolder.

## Scoring Rubric
- **Level 1**: Understands the basic sync vs async difference.
- **Level 2**: Identifies Temporal as the scaling backbone but lacks code-level evidence.
- **Level 3**: Maps scaling claims to actual Agentex configuration and code paths.
- **Level 4**: Provides deep architectural analysis of bottlenecks (locks, DB pools, idempotency) and how to tune them.
