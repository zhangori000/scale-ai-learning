from __future__ import annotations

from pydantic import model_validator

from perf_control_plane.domain.entities.base import BaseModel


class TimeSegmentEntity(BaseModel):
    duration_seconds: int
    scenario_starts_per_second: int
    max_concurrency: int | None = None


class TimeRampProfileEntity(BaseModel):
    initial_scenario_starts_per_second: int = 1000
    step_size: int = 250
    step_count: int = 3
    step_duration_seconds: int = 600
    max_concurrency: int | None = None

    @model_validator(mode="after")
    def validate_profile(self) -> "TimeRampProfileEntity":
        if self.initial_scenario_starts_per_second <= 0:
            raise ValueError("initial_scenario_starts_per_second must be positive")
        if self.step_size < 0:
            raise ValueError("step_size must be zero or positive")
        if self.step_count <= 0:
            raise ValueError("step_count must be positive")
        if self.step_duration_seconds <= 0:
            raise ValueError("step_duration_seconds must be positive")
        return self

    def to_time_segments(self) -> list[TimeSegmentEntity]:
        return [
            TimeSegmentEntity(
                duration_seconds=self.step_duration_seconds,
                scenario_starts_per_second=(
                    self.initial_scenario_starts_per_second + (index * self.step_size)
                ),
                max_concurrency=self.max_concurrency,
            )
            for index in range(self.step_count)
        ]

    def total_duration_seconds(self) -> int:
        return self.step_count * self.step_duration_seconds


class BudgetSegmentEntity(BaseModel):
    share: float
    scenario_starts_per_second: int
    max_concurrency: int | None = None

    @model_validator(mode="after")
    def validate_segment(self) -> "BudgetSegmentEntity":
        if self.share <= 0 or self.share > 1:
            raise ValueError("budget segment share must be in the range (0, 1]")
        if self.scenario_starts_per_second <= 0:
            raise ValueError("scenario_starts_per_second must be positive")
        return self


class BudgetRampProfileEntity(BaseModel):
    part_count: int = 3
    initial_scenario_starts_per_second: int = 1000
    step_size: int = 250
    max_concurrency: int | None = None

    @model_validator(mode="after")
    def validate_profile(self) -> "BudgetRampProfileEntity":
        if self.part_count <= 0:
            raise ValueError("part_count must be positive")
        if self.initial_scenario_starts_per_second <= 0:
            raise ValueError("initial_scenario_starts_per_second must be positive")
        if self.step_size < 0:
            raise ValueError("step_size must be zero or positive")
        return self

    def to_budget_segments(self) -> list[BudgetSegmentEntity]:
        equal_share = 1.0 / self.part_count
        return [
            BudgetSegmentEntity(
                share=equal_share,
                scenario_starts_per_second=(
                    self.initial_scenario_starts_per_second + (index * self.step_size)
                ),
                max_concurrency=self.max_concurrency,
            )
            for index in range(self.part_count)
        ]
