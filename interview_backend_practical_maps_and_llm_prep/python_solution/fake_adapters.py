from __future__ import annotations

import csv
import io

from models import (
    Bounds,
    NonRetryableProviderError,
    ResolvedPlace,
    RestaurantRecord,
    RestaurantSearchPage,
    RetryableProviderError,
    ReviewResult,
    TaskRecord,
)


class FakePlacesSearchClient:
    def __init__(self, restaurants: list[RestaurantRecord]) -> None:
        self.restaurants = list(restaurants)

    def search_restaurants(
        self,
        bounds: Bounds,
        *,
        page_token: str | None = None,
        page_size: int = 20,
    ) -> RestaurantSearchPage:
        filtered = [
            restaurant
            for restaurant in self.restaurants
            if _within_bounds(restaurant, bounds)
        ]
        start = int(page_token) if page_token is not None else 0
        end = min(start + page_size, len(filtered))
        next_page_token = str(end) if end < len(filtered) else None
        return RestaurantSearchPage(
            restaurants=filtered[start:end],
            next_page_token=next_page_token,
        )


class InMemoryTaskRepository:
    def __init__(self, tasks: list[TaskRecord]) -> None:
        self._tasks = {task.task_id: task for task in tasks}

    def get_tasks(self, task_ids: list[str]) -> list[TaskRecord]:
        return [self._tasks[task_id] for task_id in task_ids if task_id in self._tasks]


class HeuristicLLMReviewer:
    def __init__(self, pass_threshold: float = 3.5) -> None:
        self.pass_threshold = pass_threshold

    def review_task(self, task: TaskRecord) -> ReviewResult:
        if not task.prompt.strip():
            raise NonRetryableProviderError("Prompt is empty")
        if not task.response.strip():
            raise NonRetryableProviderError("Response is empty")

        issues: list[str] = []
        grammar_score = 4
        if not task.response[0].isupper():
            grammar_score -= 1
            issues.append("response_should_start_with_capital_letter")
        if task.response[-1] not in ".!?":
            grammar_score -= 1
            issues.append("response_should_end_with_punctuation")

        style_score = 4
        response_word_count = len(task.response.split())
        if response_word_count < 5:
            style_score -= 1
            issues.append("response_is_brief")
        if response_word_count > 80:
            style_score -= 1
            issues.append("response_is_verbose")

        answer_score = 5
        if len(task.response.split()) < max(3, len(task.prompt.split()) // 4):
            answer_score -= 2
            issues.append("response_may_not_fully_answer_prompt")

        overall_score = round((grammar_score + style_score + answer_score) / 3, 2)
        return ReviewResult(
            task_id=task.task_id,
            overall_score=overall_score,
            grammar_score=grammar_score,
            style_score=style_score,
            answer_score=answer_score,
            passes_threshold=overall_score >= self.pass_threshold,
            issues=issues,
        )


class FlakyLLMReviewer:
    def __init__(
        self,
        inner_reviewer: HeuristicLLMReviewer,
        *,
        retryable_failures: dict[str, int] | None = None,
        non_retryable_tasks: set[str] | None = None,
    ) -> None:
        self.inner_reviewer = inner_reviewer
        self.retryable_failures = dict(retryable_failures or {})
        self.non_retryable_tasks = set(non_retryable_tasks or set())
        self.calls: dict[str, int] = {}

    def review_task(self, task: TaskRecord) -> ReviewResult:
        self.calls[task.task_id] = self.calls.get(task.task_id, 0) + 1

        if task.task_id in self.non_retryable_tasks:
            raise NonRetryableProviderError("Provider rejected task payload")

        remaining_failures = self.retryable_failures.get(task.task_id, 0)
        if remaining_failures > 0:
            self.retryable_failures[task.task_id] = remaining_failures - 1
            raise RetryableProviderError("Provider rate limited this request")

        return self.inner_reviewer.review_task(task)


class InMemoryCSVExporter:
    def __init__(self) -> None:
        self.exports: dict[str, str] = {}

    def export_results(self, job_id: str, results: list[ReviewResult]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "task_id",
                "review_status",
                "overall_score",
                "passes_threshold",
                "attempt_count",
                "issues",
                "error_message",
            ]
        )
        for result in results:
            writer.writerow(
                [
                    result.task_id,
                    result.review_status,
                    result.overall_score,
                    result.passes_threshold,
                    result.attempt_count,
                    "|".join(result.issues),
                    result.error_message or "",
                ]
            )
        self.exports[job_id] = output.getvalue()
        return f"memory://review-jobs/{job_id}.csv"


class RecordingEmailClient:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    def send_results_ready(self, operator_email: str, csv_url: str) -> None:
        self.sent.append((operator_email, csv_url))


class StaticPlaceLookup:
    def __init__(self, mapping: dict[str, ResolvedPlace]) -> None:
        self.mapping = dict(mapping)

    def resolve_place(self, query: str) -> ResolvedPlace:
        if query not in self.mapping:
            raise KeyError(f"Unknown place query: {query}")
        return self.mapping[query]


class StaticRouteMatrix:
    def __init__(self, durations: dict[tuple[str, str], int]) -> None:
        self.durations = dict(durations)

    def build_drive_time_matrix(
        self,
        place_ids: list[str],
    ) -> dict[tuple[str, str], int]:
        matrix: dict[tuple[str, str], int] = {}
        for origin in place_ids:
            for destination in place_ids:
                key = (origin, destination)
                if origin == destination:
                    matrix[key] = 0
                elif key in self.durations:
                    matrix[key] = self.durations[key]
                else:
                    raise KeyError(f"Missing duration for {key}")
        return matrix


def _within_bounds(restaurant: RestaurantRecord, bounds: Bounds) -> bool:
    (lat1, lng1), (lat2, lng2) = bounds
    min_lat = min(lat1, lat2)
    max_lat = max(lat1, lat2)
    min_lng = min(lng1, lng2)
    max_lng = max(lng1, lng2)
    return min_lat <= restaurant.lat <= max_lat and min_lng <= restaurant.lng <= max_lng
