from __future__ import annotations

from perf_control_plane.domain.entities.endpoints import EndpointEntity, HttpMethod, RiskClass
from perf_control_plane.domain.entities.scenarios import (
    ScenarioEntity,
    ScenarioStepEntity,
    SteppedLoadProfileEntity,
)
from perf_control_plane.domain.entities.test_plans import (
    BudgetLoadBandEntity,
    BudgetStepLoadProfileEntity,
    ScenarioWorkloadEntity,
    TestPlanEntity as PlanTemplateEntity,
    WorkloadExecutionSettingsEntity,
    WorkloadRole,
)
from perf_control_plane.domain.services.compiler_service import CompilerService


def _ledger_endpoints() -> dict[str, EndpointEntity]:
    return {
        "ep_provision": EndpointEntity(
            id="ep_provision",
            service_name="ledger",
            method=HttpMethod.POST,
            path="/provision",
            owner_team="ledger",
            risk_class=RiskClass.MODERATE,
        ),
        "ep_post": EndpointEntity(
            id="ep_post",
            service_name="ledger",
            method=HttpMethod.POST,
            path="/post",
            owner_team="ledger",
            risk_class=RiskClass.MODERATE,
        ),
        "ep_eod": EndpointEntity(
            id="ep_eod",
            service_name="ledger",
            method=HttpMethod.POST,
            path="/end_of_day",
            owner_team="ledger",
            risk_class=RiskClass.EXPENSIVE,
        ),
    }


def test_budget_bands_allocate_exact_counts_and_track_repeated_steps_by_index():
    compiler = CompilerService()
    scenario = ScenarioEntity(
        id="scenario_post_eod",
        name="post_then_eod",
        owner_eid="eid_alice",
        owner_name="Alice",
        steps=[
            ScenarioStepEntity(name="post", endpoint_id="ep_post"),
            ScenarioStepEntity(name="post", endpoint_id="ep_post"),
            ScenarioStepEntity(name="eod", endpoint_id="ep_eod"),
        ],
    )
    plan = PlanTemplateEntity(
        name="budget-plan",
        environment="perf-cell-a",
        workloads=[
            ScenarioWorkloadEntity(
                name="east-budget",
                scenario_id=scenario.id,
                role=WorkloadRole.MEASURED,
                execution_settings=WorkloadExecutionSettingsEntity(
                    budget_bands=[
                        BudgetLoadBandEntity(share=0.33, scenario_starts_per_second=1000),
                        BudgetLoadBandEntity(share=0.67, scenario_starts_per_second=1500),
                    ],
                    max_total_scenario_starts=100_000,
                ),
            )
        ],
    )

    compiled = compiler.compile_test_plan(
        test_plan=plan,
        requested_by="alice",
        scenarios={scenario.id: scenario},
        endpoints=_ledger_endpoints(),
    )

    workload = compiled.workloads[0]
    assert [item.scenario_count for item in workload.load_bands] == [33_000, 67_000]
    assert sum(item.scenario_count or 0 for item in workload.load_bands) == 100_000
    assert [item.step_index for item in workload.measured_targets] == [0, 1, 2]
    assert workload.measured_targets[0].request_name == "step[0].post"
    assert any("budget-based load partitioning" in note for note in workload.validation_notes)
    assert any("measures every step" in note for note in workload.validation_notes)


def test_budget_step_profile_auto_even_and_setup_workload_is_not_measured_by_default():
    compiler = CompilerService()
    setup_scenario = ScenarioEntity(
        id="scenario_provision",
        name="provision_accounts",
        owner_eid="eid_alice",
        owner_name="Alice",
        steps=[
            ScenarioStepEntity(name="provision", endpoint_id="ep_provision"),
        ],
    )
    measured_scenario = ScenarioEntity(
        id="scenario_main",
        name="post_then_eod",
        owner_eid="eid_alice",
        owner_name="Alice",
        steps=[
            ScenarioStepEntity(name="post", endpoint_id="ep_post"),
            ScenarioStepEntity(name="eod", endpoint_id="ep_eod"),
        ],
    )
    plan = PlanTemplateEntity(
        name="sequential-budget-plan",
        environment="perf-cell-a",
        workloads=[
            ScenarioWorkloadEntity(
                name="preload",
                scenario_id=setup_scenario.id,
                role=WorkloadRole.SETUP,
                execution_settings=WorkloadExecutionSettingsEntity(
                    budget_bands=[
                        BudgetLoadBandEntity(share=1.0, scenario_starts_per_second=500),
                    ],
                    max_total_scenario_starts=25_000,
                ),
            ),
            ScenarioWorkloadEntity(
                name="measure",
                scenario_id=measured_scenario.id,
                role=WorkloadRole.MEASURED,
                execution_settings=WorkloadExecutionSettingsEntity(
                    budget_step_profile=BudgetStepLoadProfileEntity(
                        part_count=3,
                        initial_scenario_starts_per_second=1000,
                        step_size=500,
                    ),
                    max_total_scenario_starts=120_000,
                ),
            ),
        ],
    )

    compiled = compiler.compile_test_plan(
        test_plan=plan,
        requested_by="alice",
        scenarios={
            setup_scenario.id: setup_scenario,
            measured_scenario.id: measured_scenario,
        },
        endpoints=_ledger_endpoints(),
    )

    setup_workload = compiled.workloads[0]
    measured_workload = compiled.workloads[1]

    assert setup_workload.measured_targets == []
    assert [item.scenario_starts_per_second for item in measured_workload.load_bands] == [
        1000,
        1500,
        2000,
    ]
    assert [item.scenario_count for item in measured_workload.load_bands] == [
        40_000,
        40_000,
        40_000,
    ]
    assert [item.workload_name for item in compiled.workloads] == ["preload", "measure"]


def test_measured_step_override_limits_targets_to_selected_indexes():
    compiler = CompilerService()
    scenario = ScenarioEntity(
        id="scenario_override",
        name="loan_interest_eod",
        owner_eid="eid_alice",
        owner_name="Alice",
        steps=[
            ScenarioStepEntity(name="post_loan", endpoint_id="ep_post"),
            ScenarioStepEntity(name="post_interest", endpoint_id="ep_post"),
            ScenarioStepEntity(name="eod", endpoint_id="ep_eod"),
        ],
    )
    plan = PlanTemplateEntity(
        name="override-plan",
        environment="perf-cell-a",
        workloads=[
            ScenarioWorkloadEntity(
                name="measure-selected-steps",
                scenario_id=scenario.id,
                role=WorkloadRole.MEASURED,
                measured_step_indexes_override=[0, 2],
                execution_settings=WorkloadExecutionSettingsEntity(
                    budget_bands=[
                        BudgetLoadBandEntity(share=1.0, scenario_starts_per_second=750),
                    ],
                    max_total_scenario_starts=10_000,
                ),
            )
        ],
    )

    compiled = compiler.compile_test_plan(
        test_plan=plan,
        requested_by="alice",
        scenarios={scenario.id: scenario},
        endpoints=_ledger_endpoints(),
    )

    workload = compiled.workloads[0]
    assert [item.step_index for item in workload.measured_targets] == [0, 2]
    assert [item.request_name for item in workload.measured_targets] == [
        "step[0].post_loan",
        "step[2].eod",
    ]
    assert any(
        "measures only the explicitly selected scenario step indexes" in note
        for note in workload.validation_notes
    )


def test_time_step_profile_warns_on_long_runs_and_budget_exhaustion():
    compiler = CompilerService()
    scenario = ScenarioEntity(
        id="scenario_time",
        name="timed_flow",
        owner_eid="eid_alice",
        owner_name="Alice",
        steps=[
            ScenarioStepEntity(name="post", endpoint_id="ep_post"),
            ScenarioStepEntity(name="eod", endpoint_id="ep_eod"),
        ],
    )
    plan = PlanTemplateEntity(
        name="time-plan",
        environment="perf-cell-a",
        workloads=[
            ScenarioWorkloadEntity(
                name="timed-workload",
                scenario_id=scenario.id,
                role=WorkloadRole.MEASURED,
                execution_settings=WorkloadExecutionSettingsEntity(
                    stepped_load_profile=SteppedLoadProfileEntity(
                        initial_scenario_starts_per_second=1000,
                        step_size=500,
                        step_count=6,
                        step_duration_seconds=600,
                    ),
                    max_total_scenario_starts=500_000,
                ),
            )
        ],
    )

    compiled = compiler.compile_test_plan(
        test_plan=plan,
        requested_by="alice",
        scenarios={scenario.id: scenario},
        endpoints=_ledger_endpoints(),
    )

    notes = compiled.workloads[0].validation_notes
    assert any("exceeds max_total_scenario_starts" in note for note in notes)
    assert any("default 30-minute recommendation" in note for note in notes)
    assert any("one hour or longer" in note for note in notes)
