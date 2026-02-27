# Codex Training: Reference Solution

## 1) What "scale up or down based on demand and usage patterns" means in this codebase
It is not one thing. It is a stack of scaling controls:

- Deployment layer: scale pod replicas independently.
- Queue layer: route work to Temporal task queues.
- Worker layer: control in-process concurrency per worker.
- Data-plane layer: avoid DB and lock bottlenecks under load.

## 2) Evidence Table
| Claim | Proof | Why it matters |
|---|---|---|
| Agentex handles scaling automatically | `scale-agentex/agentex/docs/docs/concepts/agents.md` ("Scaling: Scale up or down based on demand and usage patterns") | This is the product claim you must map to implementation. |
| Agents are independently scalable services | `scale-agentex/agentex/docs/docs/concepts/architecture.md` ("Scalable, Isolated Deployments") | You can scale one hot agent without impacting others. |
| Replica and autoscaling knobs exist in config | `scale-agentex/agentex/docs/docs/configuration.md` (`replicaCount`, `autoscaling`) | Demand-based pod scaling is explicit and tunable. |
| CLI injects autoscaling defaults for deployments | `scale-agentex-python/src/agentex/lib/cli/handlers/deploy_handlers.py` (`autoscaling.enabled`, `minReplicas=1`, `maxReplicas=10`, `targetCPUUtilizationPercentage=50`) | Scaling policy is set programmatically, not left as manual YAML-only process. |
| Temporal workers also get autoscaling config | same file, `helm_values["temporal-worker"]["autoscaling"]` | Async path can scale independently from ACP server pods. |
| Queue name comes from agent manifest temporal workflow config | `scale-agentex-python/src/agentex/lib/types/agent_configs.py` (`queue_name`), `run_handlers.py` (`WORKFLOW_TASK_QUEUE`) | Routing by queue supports workload isolation and horizontal expansion. |
| Tasks are submitted to Temporal queue, not executed inline in request thread | `scale-agentex-python/src/agentex/lib/core/temporal/services/temporal_task_service.py` (`start_workflow(... task_queue=WORKFLOW_TASK_QUEUE)`) | Decouples API request spikes from execution spikes. |
| Worker throughput is bounded and tunable | `scale-agentex-python/src/agentex/lib/core/temporal/workers/worker.py` (`max_workers`, `max_concurrent_activities`) and `scale-agentex/agentex/src/temporal/run_worker.py` | You tune parallelism per pod before adding pods. |
| High-concurrency bottlenecks are acknowledged in server code | `scale-agentex/agentex/src/domain/services/agent_acp_service.py` (advisory lock and DB pool bottleneck warning) and `src/config/dependencies.py` (pool sizing comments) | Real scaling is constrained by DB pool/locks, not only CPU. |

## 3) Interview Answer
"How can Agentex scale a Temporal agent during demand spikes without changing business logic code?"

- Keep business logic inside workflow and activity code.
- Increase replicas via deployment/autoscaling (`replicaCount`, HPA-style fields).
- Keep task routing stable via `WORKFLOW_TASK_QUEUE` and workflow name from manifest.
- Each new worker pod polls the same queue, so backlog is drained faster.
- Tune per-worker concurrency (`max_workers`, `max_concurrent_activities`) for vertical gain before or with horizontal gain.
- Preserve idempotency and retry-safe behavior so duplicate execution attempts do not corrupt state.

## 4) Three scaling failure modes and mitigations
- Failure mode: backlog grows but worker replicas stay flat due weak policy.
  - Mitigation: tighten autoscaling thresholds and monitor queue depth plus CPU.
- Failure mode: high stream concurrency exhausts DB connections.
  - Mitigation: avoid long-lived DB locks during streams and tune pool sizes.
- Failure mode: retries or worker restarts cause duplicate side effects.
  - Mitigation: enforce idempotency keys and dedupe by event/task identifiers.

## 5) Why the old exercise felt too easy
The old exercise compares sync vs async vs durable execution, but it does not require:
- independent ACP vs Temporal worker scaling
- queue-based routing and isolation
- replica/autoscaling policy tuning
- bottleneck analysis (locks, DB pools, per-worker concurrency)

`exercise1` in this folder fixes that gap.
