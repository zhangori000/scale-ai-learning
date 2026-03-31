# Performance Testing Platform Backlog

## Executor Integration and Result Ingestion

### Current state

- `LatestMetricsEntity` is the normalized aggregate metrics snapshot for a run.
- In stub mode, `HttpExecutionGateway` fabricates `workload_results` and computes `aggregate_metrics` locally.
- In real executor mode, `HttpExecutionGateway` currently submits the compiled bundle and only captures:
  - `external_run_id`
  - `status_url`
  - `report_url`
  - `raw_response`
- Real executor mode does not yet normalize live metrics or workload-level results into first-class domain objects at submission time.

### What `LatestMetricsEntity` should represent

`LatestMetricsEntity` should stay executor-agnostic. It should mean:

- the latest normalized aggregate snapshot we know about for a run
- regardless of whether that snapshot came from:
  - stubbed local generation
  - polling an executor API
  - an executor callback/webhook
  - a pushed event stream
  - a final downloaded report

This entity should remain part of the domain model, not tied to any one executor vendor.

### Open questions

1. Should submission and status/result retrieval live in the same port, or should we split them?
2. Do we want to support only HTTP executors, or multiple executor families over time?
3. What update delivery modes do we need to support?
   - polling
   - callback/webhook
   - streaming/events
   - synchronous final response
   - report-only retrieval
4. Do we want workload-level metrics only, or richer per-step/per-band metrics later?
5. Should normalized metrics be stored as snapshots over time, or only as the latest state?

### Why translation layers are needed

If executor input/output shapes differ from the domain model, translation is required in both directions.

Input translation:

- domain compiled bundle -> executor-specific request body

Output translation:

- executor-specific response/status/report -> normalized domain entities

This should be handled inside executor adapters so the rest of the app remains unchanged.

### Suggested architecture direction

Keep the domain model executor-agnostic and let adapters own translation.

Possible shape:

- `ExecutionGateway`
  - responsible for submission
- `ExecutionUpdateProvider` or `ExecutionObserver`
  - responsible for fetching or receiving updates

Possible adapter implementations:

- `StubExecutionGateway`
- `HttpExecutionGateway`
- `K6ExecutionGateway`
- `GatlingExecutionGateway`
- `CustomExecutionGateway`

Possible update adapters:

- `PollingExecutionObserver`
- `WebhookExecutionObserver`
- `StreamingExecutionObserver`
- `ImmediateExecutionObserver`
- `ReportDownloadExecutionObserver`

This keeps submission and update ingestion flexible instead of assuming polling is universal.

### Note on polling

Polling is common, but not required.

If an executor does not support polling, alternatives include:

- executor callback/webhook into our API
- event or queue-based updates
- synchronous completion response
- downloadable report ingestion

The code already hints at push-style updates through the existing executor update flow:

- `RunService.record_executor_update(...)`
- `/runs/{run_id}/executor-update`

So polling should be treated as one strategy, not the only strategy.

### Backlog items

#### P0: Define the executor boundary more explicitly

- Decide whether to keep a single `ExecutionGateway` port or split submission and update retrieval into two ports.
- Document the minimal normalized contract for:
  - submission acknowledgement
  - run status updates
  - aggregate metrics
  - workload results

#### P0: Introduce explicit translation responsibilities

- Stop assuming `bundle.to_dict(...)` is the executor request shape.
- Add executor-specific request translation.
- Add executor-specific response normalization.
- Keep translation inside adapters, not in domain services.

#### P1: Support multiple result-ingestion strategies

- Add support for at least one asynchronous update path beyond stub mode.
- Candidate first implementation:
  - polling-based observer for generic HTTP executors
- Keep design open for:
  - webhook/callback
  - report ingestion

#### P1: Improve normalized run-result modeling

- Clarify whether `LatestMetricsEntity` is:
  - latest known aggregate snapshot only
  - or part of a future history/timeline model
- Decide whether workload results should remain coarse or gain richer step-level detail.

#### P2: Make executor capabilities explicit

- Model executor capabilities such as:
  - supports polling
  - supports callbacks
  - returns metrics immediately
  - exposes downloadable reports
- Use capability-driven behavior instead of hard-coding one integration style.

#### P2: Add contract tests for adapters

- Verify every executor adapter can:
  - accept a compiled bundle
  - translate it correctly
  - normalize responses correctly
  - handle missing optional fields safely

### Suggested implementation plan

#### Phase 1: Normalize the integration boundary

- Define a clear `ExecutorSubmissionEntity` contract for submission acknowledgements.
- Decide whether update retrieval belongs in `ExecutionGateway` or a new observer port.
- Add small adapter translation helpers or executor-specific adapter classes.

#### Phase 2: Add one real asynchronous update path

- Implement a polling-based update provider first for generic HTTP executors.
- Feed normalized updates into `RunService.record_executor_update(...)`.
- Persist normalized aggregate metrics and workload results.

#### Phase 3: Generalize update transport

- Add a second update mode, preferably webhook/callback.
- Refactor shared normalization logic so polling and callback paths reuse it.
- Keep transport mechanics out of domain services.

#### Phase 4: Expand result fidelity

- Decide whether to add:
  - per-step metrics
  - per-load-band metrics
  - historical metric snapshots
- Extend domain entities only after the executor boundary is stable.

#### Phase 5: Add a custom executor adapter

- Implement a dedicated adapter for a non-generic executor shape.
- Verify that no route/service/domain changes are needed beyond dependency wiring.

### Near-term recommendation

Do not over-design immediately.

The next concrete step should be:

1. make translation explicit
2. choose one asynchronous update strategy
3. normalize real executor responses into `LatestMetricsEntity` and `WorkloadExecutionResultEntity`

That gives the system a clean path from stub mode to real execution without locking it into one executor style.

## Observability Links and Operator Navigation

### Motivation

Teams may rely on external observability tools to investigate a run, for example:

- New Relic dashboards or traces
- AWS CloudWatch log searches
- ECS service or task views
- internal logging or alerting tools

If a web frontend is added later, the backend should already make these links easy to expose in a normalized way so the UI does not need executor-specific or environment-specific link-building logic.

### Why this matters

- Operators often need to jump from a run to logs, traces, dashboards, or container views.
- These links may depend on:
  - environment
  - service name
  - endpoint ownership
  - executor metadata
  - run timestamps
  - workload names
- If link generation lives only in the frontend, every client has to re-encode the same rules.

### Suggested architecture direction

Treat observability links as backend-generated metadata attached to runs and workloads.

Possible normalized model shape:

- `ObservabilityLinkEntity`
  - `label`
  - `url`
  - `provider`
  - `scope`
  - `description`

Possible scopes:

- run-level
- workload-level
- scenario-level
- endpoint-level
- environment-level

The backend should generate normalized links while hiding provider-specific URL templates from the frontend.

### Open questions

1. Should observability links be generated eagerly at submission time, lazily on read, or both?
2. Which providers should be supported first?
3. Should links be stored in run records, or derived dynamically from metadata?
4. Do we need provider capability/configuration per environment?
5. Should users be able to configure custom org-specific link templates?

### Backlog items

#### P1: Add normalized observability link support

- Define a backend-owned normalized link model for external operator tools.
- Support both run-level and workload-level links.
- Keep the response shape generic enough for future UI usage.

#### P1: Add environment-aware link generation

- Generate links based on environment, service, workload, and time window.
- Avoid hard-coding UI-specific assumptions into domain entities.
- Keep provider URL templates in configuration or dedicated adapter code.

#### P2: Add provider adapters for common observability tools

- Candidate providers:
  - New Relic
  - AWS CloudWatch Logs
  - ECS console
  - internal dashboards
- Let each provider adapter own its own URL construction rules.

#### P2: Decide persistence strategy for links

- Evaluate whether links should be:
  - stored at run submission time
  - regenerated on every read
  - or partially stored with partial dynamic reconstruction

### Suggested implementation plan

#### Phase 1: Normalize the response shape

- Add a generic observability-link entity and response field.
- Decide the minimum metadata needed to build links reliably.

#### Phase 2: Implement one or two providers

- Start with one tracing/dashboard provider and one log/container provider.
- Verify that the frontend can render links without understanding provider internals.

#### Phase 3: Make link generation configurable

- Move provider-specific templates and environment mappings into configuration.
- Support custom org-specific templates without changing core domain logic.
