# Performance Testing Platform

This folder explains how to use the performance-testing control plane.

Start with [01_problem_statement.md](/C:/Users/zhang/00My%20Stuff/Coding/Learning/ScaleAI/system_design/performance_testing_platform/docs/01_problem_statement.md) for the product motivation.

The rest of this README focuses on the current code model.

## Core Mental Model

There are three layers:

1. `Scenario`
   A reusable ordered workflow shape.
   Example: `post-loan -> post-interest -> end-of-day`.

2. `Workload`
   One use of a scenario inside a test plan.
   A workload adds:
   - role: `setup`, `measured`, or `teardown`
   - load profile
   - optional total scenario budget

3. `TestPlan`
   An ordered list of workloads that run sequentially.

The important design choice is:

- `Scenario` owns workflow shape only.
- `WorkloadExecutionSettingsEntity` owns load behavior.

## Example: Three Sequential Workloads

This is a clean setup for:

- provision `100,000` accounts
- warm up `50,000` of them with one initial post
- then measure a 3-step business flow against the prepared state

```python
from perf_control_plane.domain.entities.scenarios import (
    ScenarioEntity,
    ScenarioStepEntity,
)
from perf_control_plane.domain.entities.test_plans import (
    BudgetStepLoadProfileEntity,
    ScenarioWorkloadEntity,
    TestPlanEntity,
    WorkloadExecutionSettingsEntity,
    WorkloadRole,
)


provision_scenario = ScenarioEntity(
    id="scenario-provision",
    name="Provision Auto Accounts",
    owner_eid="orien123",
    owner_name="Orien",
    steps=[
        ScenarioStepEntity(name="provision", endpoint_id="ep-provision"),
    ],
)

warmup_scenario = ScenarioEntity(
    id="scenario-warmup",
    name="Warm-up Post",
    owner_eid="orien123",
    owner_name="Orien",
    steps=[
        ScenarioStepEntity(name="initial-post", endpoint_id="ep-post"),
    ],
)

business_flow_scenario = ScenarioEntity(
    id="scenario-loan-flow",
    name="Loan Post + Interest + EOD",
    owner_eid="orien123",
    owner_name="Orien",
    steps=[
        ScenarioStepEntity(name="post-loan", endpoint_id="ep-post-loan"),
        ScenarioStepEntity(name="post-interest", endpoint_id="ep-post-interest"),
        ScenarioStepEntity(name="end-of-day", endpoint_id="ep-eod"),
    ],
)

test_plan = TestPlanEntity(
    name="March Auto Finance Full Load Test",
    environment="staging-perf",
    notes="Testing SLA compliance before Q2 release",
    workloads=[
        ScenarioWorkloadEntity(
            name="provision-100k",
            scenario_id="scenario-provision",
            scenario_name="Provision Auto Accounts",
            role=WorkloadRole.SETUP,
            execution_settings=WorkloadExecutionSettingsEntity(
                budget_step_profile=BudgetStepLoadProfileEntity(
                    part_count=1,
                    initial_scenario_starts_per_second=2000,
                    step_size=0,
                ),
                max_total_scenario_starts=100_000,
                stop_when_budget_exhausted=True,
            ),
        ),
        ScenarioWorkloadEntity(
            name="warmup-50k",
            scenario_id="scenario-warmup",
            scenario_name="Warm-up Post",
            role=WorkloadRole.SETUP,
            execution_settings=WorkloadExecutionSettingsEntity(
                budget_step_profile=BudgetStepLoadProfileEntity(
                    part_count=1,
                    initial_scenario_starts_per_second=1500,
                    step_size=0,
                ),
                max_total_scenario_starts=50_000,
                stop_when_budget_exhausted=True,
            ),
        ),
        ScenarioWorkloadEntity(
            name="loan-flow-measured",
            scenario_id="scenario-loan-flow",
            scenario_name="Loan Post + Interest + EOD",
            role=WorkloadRole.MEASURED,
            execution_settings=WorkloadExecutionSettingsEntity(
                budget_step_profile=BudgetStepLoadProfileEntity(
                    part_count=4,
                    initial_scenario_starts_per_second=500,
                    step_size=250,
                    max_concurrency=3000,
                ),
                max_total_scenario_starts=100_000,
                stop_when_budget_exhausted=True,
            ),
        ),
    ],
)
```

What this means:

- Workload 1 runs the provision scenario `100,000` times.
- Workload 2 runs the warm-up scenario `50,000` times.
- Workload 3 runs the measured business-flow scenario `100,000` times.
- Workloads run sequentially, not in parallel.

Measurement behavior today:

- `SETUP` workloads measure nothing.
- non-setup workloads measure every step in the attached scenario.

So for `loan-flow-measured`, the compiler will produce measured targets for:

- `step[0].post-loan`
- `step[1].post-interest`
- `step[2].end-of-day`

## `WorkloadExecutionSettingsEntity`

Current shape:

```python
class WorkloadExecutionSettingsEntity(BaseModel):
    load_segments: list[LoadSegmentEntity] = Field(default_factory=list)
    stepped_load_profile: SteppedLoadProfileEntity | None = None
    budget_bands: list[BudgetLoadBandEntity] = Field(default_factory=list)
    budget_step_profile: BudgetStepLoadProfileEntity | None = None
    max_total_scenario_starts: int | None = None
    stop_when_budget_exhausted: bool = True
```

There are 6 fields, not 7.

Exactly one of the 4 load-profile families must be set:

- `load_segments`
- `stepped_load_profile`
- `budget_bands`
- `budget_step_profile`

### 1. `load_segments`

Use this when you want manual time-based control.

```python
WorkloadExecutionSettingsEntity(
    load_segments=[
        LoadSegmentEntity(duration_seconds=600, scenario_starts_per_second=1000),
    ],
)
```

Meaning:

- run at `1000` scenario-starts/sec
- for `600` seconds

More irregular shape:

```python
WorkloadExecutionSettingsEntity(
    load_segments=[
        LoadSegmentEntity(duration_seconds=300, scenario_starts_per_second=200),
        LoadSegmentEntity(duration_seconds=60, scenario_starts_per_second=5000),
        LoadSegmentEntity(duration_seconds=300, scenario_starts_per_second=200),
    ],
)
```

This is useful for:

- spikes
- cool-down periods
- custom non-staircase traffic shapes

### 2. `stepped_load_profile`

Use this when you want shorthand time-based staircase load.

```python
from perf_control_plane.domain.entities.scenarios import SteppedLoadProfileEntity

WorkloadExecutionSettingsEntity(
    stepped_load_profile=SteppedLoadProfileEntity(
        initial_scenario_starts_per_second=500,
        step_size=500,
        step_count=5,
        step_duration_seconds=600,
    ),
)
```

This expands to:

- `500/sec` for `10 min`
- `1000/sec` for `10 min`
- `1500/sec` for `10 min`
- `2000/sec` for `10 min`
- `2500/sec` for `10 min`

This is the right abstraction when the shape is regular and time-based.

### 3. `budget_bands`

Use this when you have a fixed total amount of work and want to split it across explicit rate bands.

```python
WorkloadExecutionSettingsEntity(
    budget_bands=[
        BudgetLoadBandEntity(share=0.10, scenario_starts_per_second=200),
        BudgetLoadBandEntity(share=0.90, scenario_starts_per_second=2000),
    ],
    max_total_scenario_starts=100_000,
)
```

Meaning:

- band 1 gets `10%` of the total scenario budget
- band 2 gets `90%`

With `100,000` total:

- band 1 = `10,000` scenarios at `200/sec`
- band 2 = `90,000` scenarios at `2000/sec`

Important compiler rule:

- for non-final bands, the code uses `floor(total_budget * share)`
- the final band gets the remainder

So the exact total is always preserved.

### 4. `budget_step_profile`

Use this when you want a budget-based staircase without manually writing every band.

```python
WorkloadExecutionSettingsEntity(
    budget_step_profile=BudgetStepLoadProfileEntity(
        part_count=4,
        initial_scenario_starts_per_second=500,
        step_size=250,
    ),
    max_total_scenario_starts=100_000,
)
```

This expands to 4 equal-share budget bands:

- `25,000` at `500/sec`
- `25,000` at `750/sec`
- `25,000` at `1000/sec`
- `25,000` at `1250/sec`

Flat-rate budget-based run:

```python
WorkloadExecutionSettingsEntity(
    budget_step_profile=BudgetStepLoadProfileEntity(
        part_count=1,
        initial_scenario_starts_per_second=2000,
        step_size=0,
    ),
    max_total_scenario_starts=100_000,
)
```

This means:

- one band only
- all `100,000` scenarios at `2000/sec`

### 5. `max_total_scenario_starts`

This field has two uses.

Budget-based profiles:

- required
- defines the total scenario budget

Time-based profiles:

- optional
- acts as a safety cap

```python
WorkloadExecutionSettingsEntity(
    stepped_load_profile=SteppedLoadProfileEntity(
        initial_scenario_starts_per_second=1000,
        step_size=500,
        step_count=3,
        step_duration_seconds=600,
    ),
    max_total_scenario_starts=500_000,
)
```

Without the cap, the planned time schedule implies:

- `1000 * 600 + 1500 * 600 + 2000 * 600 = 2,700,000` scenario starts

With the cap:

- the compiler emits a note saying the executor should stop early when the budget is exhausted

### 6. `stop_when_budget_exhausted`

This flag tells the executor what to do once the available scenario budget is consumed.

```python
WorkloadExecutionSettingsEntity(
    budget_step_profile=BudgetStepLoadProfileEntity(
        part_count=2,
        initial_scenario_starts_per_second=1000,
        step_size=500,
    ),
    max_total_scenario_starts=100_000,
    stop_when_budget_exhausted=True,
)
```

Typical meaning:

- once the budget is exhausted, stop the workload

Rare alternative:

```python
WorkloadExecutionSettingsEntity(
    budget_step_profile=BudgetStepLoadProfileEntity(
        part_count=2,
        initial_scenario_starts_per_second=1000,
        step_size=500,
    ),
    max_total_scenario_starts=100_000,
    stop_when_budget_exhausted=False,
)
```

Interpretation:

- the executor may continue by reusing allowable test state

Important caveat:

- this repository stores and forwards the flag
- the exact reuse behavior depends on the external execution service

For state-mutating ledger-style workloads, `True` is usually the sane default.

## Helper Methods on `WorkloadExecutionSettingsEntity`

These methods are not "doing load testing" themselves.

They are helper methods the compiler and other services call after validation has already happened.

### `uses_time_profile()`

This answers:

- "Did the user choose the time-based family?"

That means either:

- `load_segments`
- `stepped_load_profile`

Example:

```python
if settings.uses_time_profile():
    segments = settings.effective_load_segments()
    # compile time-based bands
```

### `uses_budget_profile()`

This answers:

- "Did the user choose the budget-based family?"

That means either:

- `budget_bands`
- `budget_step_profile`

Example:

```python
if settings.uses_budget_profile():
    bands = settings.effective_budget_bands()
    budget = settings.max_total_scenario_starts
    # allocate integer scenario counts across the bands
```

### `effective_load_segments()`

This is the time-family resolver.

It means:

- if the user already gave manual `load_segments`, return them
- otherwise, if the user gave a `stepped_load_profile`, expand it into concrete segments

Important clarification:

- yes, this method assumes you are in the time-based family
- if the workload is budget-based, this returns `[]`

That is expected.

Typical usage pattern:

```python
if settings.uses_time_profile():
    segments = settings.effective_load_segments()
```

The caller checks the family first, then calls the matching resolver.

### `effective_budget_bands()`

This is the budget-family mirror of `effective_load_segments()`.

It means:

- if the user gave manual `budget_bands`, return them
- otherwise, if the user gave `budget_step_profile`, expand it into concrete equal-share bands

Typical usage pattern:

```python
if settings.uses_budget_profile():
    bands = settings.effective_budget_bands()
```

### `load_profile_family()`

This returns a string label:

- `"time_segments"`
- `"time_step"`
- `"budget_bands"`
- `"budget_step"`

This is useful for:

- compiled output
- logging
- dashboards
- debugging

Example:

```python
CompiledLoadBandEntity(
    sequence=0,
    profile_family=settings.load_profile_family(),
    scenario_starts_per_second=500,
)
```

### What "step" means in load-profile names

This is easy to confuse with `ScenarioStepEntity`.

In load-profile naming:

- `stepped_load_profile`
- `budget_step_profile`

the word `step` means:

- staircase ramp shape
- start here, increase by this amount, repeat

It does **not** mean:

- a workflow step
- a single endpoint call

So the naming split is:

- `segments` and `bands` = manual
- `step` profiles = shorthand that auto-generates the manual form

## Validation Rules

These come directly from the current code:

1. Exactly one load-profile family must be configured.
2. `max_total_scenario_starts`, when provided, must be positive.
3. Budget-based profiles require `max_total_scenario_starts`.
4. `budget_bands` shares must sum to `1.0`.
5. `BudgetStepLoadProfileEntity.part_count` must be positive.
6. `BudgetStepLoadProfileEntity.initial_scenario_starts_per_second` must be positive.
7. `BudgetStepLoadProfileEntity.step_size` must be zero or positive.
8. `SteppedLoadProfileEntity.step_count` and `step_duration_seconds` must be positive.

## Important Result-Model Caveat

The compiler resolves measured targets by step index, but the current top-level run result entity is still workload-oriented:

```python
class WorkloadExecutionResultEntity(BaseModel):
    workload_name: str
    scenario_id: str
    scenario_name: str
    role: WorkloadRole
    status: str
    actual_scenario_starts_per_second: float | None = None
    actual_requests_per_second: float | None = None
    error_rate: float | None = None
    p95_ms: float | None = None
    p99_ms: float | None = None
    status_url: str | None = None
    report_url: str | None = None
```

So today:

- the plan/compiler knows which scenario steps are measured
- the external report link can still expose detailed request-level metrics
- but this repo does not yet model per-step or per-band metric breakdown as first-class result objects

That would be a reasonable future enhancement.

## `CompiledLoadBandEntity`

This is the compiler's common output format for load.

Why it exists:

- users can configure load in 4 different ways
- the executor should not have to understand all 4 raw shapes
- so the compiler resolves everything into one list of compiled bands

Current shape:

```python
class CompiledLoadBandEntity(BaseModel):
    sequence: int
    profile_family: str
    scenario_starts_per_second: int
    max_concurrency: int | None = None
    duration_seconds: int | None = None
    scenario_count: int | None = None
    share: float | None = None
```

### Time-based example

If the user configured a stepped time profile:

```python
SteppedLoadProfileEntity(
    initial_scenario_starts_per_second=500,
    step_size=500,
    step_count=3,
    step_duration_seconds=600,
)
```

the compiler resolves it to:

```python
CompiledLoadBandEntity(
    sequence=0,
    profile_family="time_step",
    scenario_starts_per_second=500,
    duration_seconds=600,
    scenario_count=None,
    share=None,
    max_concurrency=None,
)

CompiledLoadBandEntity(
    sequence=1,
    profile_family="time_step",
    scenario_starts_per_second=1000,
    duration_seconds=600,
    scenario_count=None,
    share=None,
    max_concurrency=None,
)

CompiledLoadBandEntity(
    sequence=2,
    profile_family="time_step",
    scenario_starts_per_second=1500,
    duration_seconds=600,
    scenario_count=None,
    share=None,
    max_concurrency=None,
)
```

Time-based meaning:

- `duration_seconds` matters
- `scenario_count` and `share` do not

### Budget-based example

If the user configured:

```python
BudgetStepLoadProfileEntity(
    part_count=4,
    initial_scenario_starts_per_second=500,
    step_size=250,
)
```

with:

```python
max_total_scenario_starts=100_000
```

the compiler resolves it to:

```python
CompiledLoadBandEntity(
    sequence=0,
    profile_family="budget_step",
    scenario_starts_per_second=500,
    duration_seconds=None,
    scenario_count=25000,
    share=0.25,
    max_concurrency=None,
)

CompiledLoadBandEntity(
    sequence=1,
    profile_family="budget_step",
    scenario_starts_per_second=750,
    duration_seconds=None,
    scenario_count=25000,
    share=0.25,
    max_concurrency=None,
)

CompiledLoadBandEntity(
    sequence=2,
    profile_family="budget_step",
    scenario_starts_per_second=1000,
    duration_seconds=None,
    scenario_count=25000,
    share=0.25,
    max_concurrency=None,
)

CompiledLoadBandEntity(
    sequence=3,
    profile_family="budget_step",
    scenario_starts_per_second=1250,
    duration_seconds=None,
    scenario_count=25000,
    share=0.25,
    max_concurrency=None,
)
```

Budget-based meaning:

- `scenario_count` and `share` matter
- `duration_seconds` does not

## `MeasuredTargetEntity`

`MeasuredTargetEntity` tells the executor and reporting layer:

- which scenario step is measured
- what label should identify that measurement

Current shape:

```python
class MeasuredTargetEntity(BaseModel):
    step_index: int
    request_name: str
    endpoint_id: str
    path: str
```

Example for a measured 3-step scenario:

```python
MeasuredTargetEntity(
    step_index=0,
    request_name="step[0].post-loan",
    endpoint_id="ep-post-loan",
    path="/v1/transactions/loan",
)

MeasuredTargetEntity(
    step_index=1,
    request_name="step[1].post-interest",
    endpoint_id="ep-post-interest",
    path="/v1/transactions/interest",
)

MeasuredTargetEntity(
    step_index=2,
    request_name="step[2].end-of-day",
    endpoint_id="ep-eod",
    path="/v1/transactions/end-of-day",
)
```

It is basically the report-label metadata for measured steps.

For setup workloads:

- `measured_targets = []`

For non-setup workloads:

- every scenario step is currently measured

## `CompiledWorkloadBundleEntity`

This is the fully resolved execution package for one workload.

It combines:

- workload metadata
- resolved scenario steps
- measured targets
- compiled load bands
- control flags
- validation notes

Example:

```python
CompiledWorkloadBundleEntity(
    workload_name="loan-flow-measured",
    scenario_id="scenario-loan-flow",
    scenario_name="Loan Post + Interest + EOD",
    role=WorkloadRole.MEASURED,
    resolved_steps=[
        ResolvedScenarioStepEntity(
            step_index=0,
            name="post-loan",
            endpoint_id="ep-post-loan",
            service_name="ledger-service",
            method="POST",
            path="/v1/transactions/loan",
            base_url="https://staging-perf.internal.example",
            owner_team="auto-finance-platform",
        ),
        ResolvedScenarioStepEntity(
            step_index=1,
            name="post-interest",
            endpoint_id="ep-post-interest",
            service_name="ledger-service",
            method="POST",
            path="/v1/transactions/interest",
            base_url="https://staging-perf.internal.example",
            owner_team="auto-finance-platform",
        ),
        ResolvedScenarioStepEntity(
            step_index=2,
            name="end-of-day",
            endpoint_id="ep-eod",
            service_name="ledger-service",
            method="POST",
            path="/v1/transactions/end-of-day",
            base_url="https://staging-perf.internal.example",
            owner_team="auto-finance-platform",
        ),
    ],
    measured_targets=[
        MeasuredTargetEntity(
            step_index=0,
            request_name="step[0].post-loan",
            endpoint_id="ep-post-loan",
            path="/v1/transactions/loan",
        ),
        MeasuredTargetEntity(
            step_index=1,
            request_name="step[1].post-interest",
            endpoint_id="ep-post-interest",
            path="/v1/transactions/interest",
        ),
        MeasuredTargetEntity(
            step_index=2,
            request_name="step[2].end-of-day",
            endpoint_id="ep-eod",
            path="/v1/transactions/end-of-day",
        ),
    ],
    load_bands=[
        CompiledLoadBandEntity(
            sequence=0,
            profile_family="budget_step",
            scenario_starts_per_second=500,
            scenario_count=25000,
            share=0.25,
        ),
        CompiledLoadBandEntity(
            sequence=1,
            profile_family="budget_step",
            scenario_starts_per_second=750,
            scenario_count=25000,
            share=0.25,
        ),
        CompiledLoadBandEntity(
            sequence=2,
            profile_family="budget_step",
            scenario_starts_per_second=1000,
            scenario_count=25000,
            share=0.25,
        ),
        CompiledLoadBandEntity(
            sequence=3,
            profile_family="budget_step",
            scenario_starts_per_second=1250,
            scenario_count=25000,
            share=0.25,
        ),
    ],
    max_total_scenario_starts=100_000,
    stop_when_budget_exhausted=True,
    validation_notes=[
        "workload 'loan-flow-measured' uses budget-based load partitioning against the scenario budget",
        "workload 'loan-flow-measured' measures every step in the attached scenario",
    ],
)
```

This is what "compiled" means:

- the scenario has already been looked up
- endpoints have already been resolved
- shorthand load config has already been expanded
- measured targets have already been determined

The executor should be able to run directly from this object.

## `CompiledTestPlanBundleEntity`

This is just the plan-level wrapper around the compiled workloads.

Current shape:

```python
class CompiledTestPlanBundleEntity(BaseModel):
    plan_name: str
    requested_by: str
    environment: str
    workloads: list[CompiledWorkloadBundleEntity]
    validation_notes: list[str] = Field(default_factory=list)
```

Example:

```python
CompiledTestPlanBundleEntity(
    plan_name="March Auto Finance Full Load Test",
    requested_by="orien123",
    environment="staging-perf",
    workloads=[
        compiled_provision_workload,
        compiled_warmup_workload,
        compiled_measured_workload,
    ],
    validation_notes=[
        "workload 'provision-100k' is setup-only, so no scenario steps are measured",
        "workload 'warmup-50k' is setup-only, so no scenario steps are measured",
        "workload 'loan-flow-measured' budget bands were auto-generated from the budget step profile",
    ],
)
```

The executor consumes this as:

- run workload `0`
- then workload `1`
- then workload `2`

## Steps vs Load Bands

This is the key execution question.

Suppose one scenario has 3 steps:

1. `post-loan`
2. `post-interest`
3. `end-of-day`

and the compiled workload has 4 load bands.

That does **not** mean:

- band 0 runs step 0
- band 1 runs step 1
- band 2 runs step 2
- band 3 runs something extra

It means:

- every single scenario start always runs all 3 scenario steps in order
- the load bands only control how many scenario starts happen and at what intensity

For example:

- band 0: `25,000` scenario starts at `500/sec`
- band 1: `25,000` scenario starts at `750/sec`
- band 2: `25,000` scenario starts at `1000/sec`
- band 3: `25,000` scenario starts at `1250/sec`

Within each scenario start, the order is still:

1. `post-loan`
2. `post-interest`
3. `end-of-day`

So the staircase changes throughput, not workflow order.

Across the whole measured workload:

- `100,000` scenario starts
- `3` steps per scenario
- `300,000` total endpoint calls
