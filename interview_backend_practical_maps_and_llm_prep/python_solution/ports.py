from __future__ import annotations

from typing import Protocol

from models import (
    Bounds,
    ResolvedPlace,
    RestaurantSearchPage,
    ReviewResult,
    TaskRecord,
)


class PlacesSearchPort(Protocol):
    def search_restaurants(
        self,
        bounds: Bounds,
        *,
        page_token: str | None = None,
        page_size: int = 20,
    ) -> RestaurantSearchPage:
        raise NotImplementedError


class TaskRepositoryPort(Protocol):
    def get_tasks(self, task_ids: list[str]) -> list[TaskRecord]:
        raise NotImplementedError


class LLMReviewerPort(Protocol):
    def review_task(self, task: TaskRecord) -> ReviewResult:
        raise NotImplementedError


class CSVExporterPort(Protocol):
    def export_results(self, job_id: str, results: list[ReviewResult]) -> str:
        raise NotImplementedError


class EmailPort(Protocol):
    def send_results_ready(self, operator_email: str, csv_url: str) -> None:
        raise NotImplementedError


class PlaceLookupPort(Protocol):
    def resolve_place(self, query: str) -> ResolvedPlace:
        raise NotImplementedError


class RouteMatrixPort(Protocol):
    def build_drive_time_matrix(
        self,
        place_ids: list[str],
    ) -> dict[tuple[str, str], int]:
        raise NotImplementedError
