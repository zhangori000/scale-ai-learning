# Gemini Training: Reference Solution

## 1) The 4-Layer Scaling Model in Agentex
The following four layers must be considered when scaling an agentic application:

- **Layer 1: Deployment (Horizontal Pod Autoscaling)**
  - Use Kubernetes or Helm to scale replicas of the ACP (Agent Control Plane) or the Temporal Worker.
  - Controls: `replicaCount`, `autoscaling.minReplicas`, `autoscaling.maxReplicas`.
- **Layer 2: Queue (Temporal Task Routing)**
  - Decouples API ingest from backend execution.
  - Controls: `WORKFLOW_TASK_QUEUE` and agent-specific manifest fields (`queue_name`).
- **Layer 3: Worker (In-Process Concurrency)**
  - Controls how many parallel activities a single pod can handle.
  - Controls: `max_concurrent_activities`, `max_workers`, `max_cached_workflows`.
- **Layer 4: Data-Plane (Bottleneck Analysis)**
  - The shared resources that all workers depend on.
  - Controls: DB connection pool size, advisory locks, LLM provider rate limits.

## 2) Code Evidence Table
| Scaling Concept | Implementation File | Why It Matters |
|---|---|---|
| Automatic Scaling | `scale-agentex/agentex/docs/docs/concepts/agents.md` | Maps the product claim to the user's architectural understanding. |
| Isolated Deployments | `scale-agentex/agentex/docs/docs/concepts/architecture.md` | Enables scaling individual agents without impacting the entire system. |
| CLI-Managed Scaling | `scale-agentex-python/src/agentex/lib/cli/handlers/deploy_handlers.py` | Shows how `autoscaling` fields are injected into Helm templates (`minReplicas=1`, `maxReplicas=10`). |
| Workflow Task Routing | `scale-agentex-python/src/agentex/lib/core/temporal/services/temporal_task_service.py` | Demonstrates decoupling: tasks are queued, not executed in-thread. |
| Per-Worker Concurrency | `scale-agentex-python/src/agentex/lib/core/temporal/workers/worker.py` | Tuning `max_concurrent_activities` allows vertical scaling per pod. |
| Data-Plane Constraints | `scale-agentex/agentex/src/domain/services/agent_acp_service.py` | Highlights that scaling workers can exhaust DB pools or cause lock contention. |

## 3) The "Durable" Difference
While `asyncio.gather` provides concurrency, it lacks **durability**. If a server restarts:
- **Async**: All tasks in memory are lost.
- **Durable (Temporal)**: The "History Service" persists the state of each task. A new worker pulls the task and "replays" the history to resume exactly where it left off.

This is how Agentex handles "thousands of events" at once without dropping any.

## 4) Interview Answer: Scaling Without Logic Changes
"How can Agentex scale a Temporal agent during demand spikes without changing business logic code?"

> "Agentex abstracts the infrastructure via Temporal. The business logic stays in Workflow and Activity functions. When demand spikes, we can horizontally scale the number of **Worker Pods** connected to the agent's specific **Task Queue**. Because the system is decoupled, new workers simply poll the same queue and start draining the backlog. We can also tune the **per-worker concurrency limits** (`max_concurrent_activities`) to maximize resource utilization on existing pods. Throughout this, the logic remains unchanged, and Temporal's persistence ensures that even if workers crash under load, tasks are resumed rather than lost."

## 5) Failure Modes and Mitigations
- **Failure**: Worker backlog grows, but CPU is low (I/O bound), and HPA doesn't trigger.
  - **Mitigation**: Scale based on **queue depth** or custom metrics rather than just CPU/Memory.
- **Failure**: Scaling workers exhausts the Database Connection Pool.
  - **Mitigation**: Increase DB pool size in `src/config/dependencies.py` or use a connection pooling proxy (like PgBouncer).
- **Failure**: Rapid restarts or scaling triggers "double-execution" of non-idempotent code.
  - **Mitigation**: Enforce **Idempotency Keys** and use `workflow_id` or unique identifiers in activity logic.
