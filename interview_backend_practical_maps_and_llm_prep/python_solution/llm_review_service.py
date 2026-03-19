from __future__ import annotations

import time

from models import (
    NonRetryableProviderError,
    RetryableProviderError,
    ReviewJobResult,
    ReviewResult,
    TaskRecord,
)
from ports import CSVExporterPort, EmailPort, LLMReviewerPort, TaskRepositoryPort


class LLMReviewJobService:
    def __init__(
        self,
        task_repository: TaskRepositoryPort,
        reviewer: LLMReviewerPort,
        exporter: CSVExporterPort,
        email_client: EmailPort,
        *,
        max_tasks: int = 5000,
        max_retries: int = 3,
        base_backoff_seconds: float = 0.25,
        sleep_fn=None,
    ) -> None:
        self.task_repository = task_repository
        self.reviewer = reviewer
        self.exporter = exporter
        self.email_client = email_client
        self.max_tasks = max_tasks
        self.max_retries = max_retries
        self.base_backoff_seconds = base_backoff_seconds
        self.sleep_fn = sleep_fn or time.sleep

    def run_job(
        self,
        job_id: str,
        task_ids: list[str],
        operator_email: str,
    ) -> ReviewJobResult:
        if len(task_ids) > self.max_tasks:
            raise ValueError(
                f"Operators may review at most {self.max_tasks} tasks per job"
            )

        fetched_tasks = self.task_repository.get_tasks(task_ids)
        tasks_by_id = {task.task_id: task for task in fetched_tasks}

        results: list[ReviewResult] = []
        for task_id in task_ids:
            task = tasks_by_id.get(task_id)
            if task is None:
                results.append(
                    ReviewResult(
                        task_id=task_id,
                        overall_score=None,
                        grammar_score=None,
                        style_score=None,
                        answer_score=None,
                        passes_threshold=None,
                        issues=["task_not_found"],
                        review_status="failed",
                        attempt_count=0,
                        error_message="Task not found",
                    )
                )
                continue
            results.append(self._review_with_retries(task))

        csv_url = self.exporter.export_results(job_id, results)
        self.email_client.send_results_ready(operator_email, csv_url)

        failed_count = sum(
            1 for result in results if result.review_status != "completed"
        )
        return ReviewJobResult(
            job_id=job_id,
            status="completed",
            total_count=len(task_ids),
            processed_count=len(results),
            failed_count=failed_count,
            csv_url=csv_url,
            results=results,
        )

    def _review_with_retries(self, task: TaskRecord) -> ReviewResult:
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 2):
            try:
                result = self.reviewer.review_task(task)
                result.task_id = task.task_id
                result.attempt_count = attempt
                return result
            except RetryableProviderError as exc:
                last_error = exc
                if attempt > self.max_retries:
                    break
                self.sleep_fn(self.base_backoff_seconds * (2 ** (attempt - 1)))
            except NonRetryableProviderError as exc:
                return ReviewResult(
                    task_id=task.task_id,
                    overall_score=None,
                    grammar_score=None,
                    style_score=None,
                    answer_score=None,
                    passes_threshold=None,
                    issues=["provider_non_retryable_error"],
                    review_status="failed",
                    attempt_count=attempt,
                    error_message=str(exc),
                )

        return ReviewResult(
            task_id=task.task_id,
            overall_score=None,
            grammar_score=None,
            style_score=None,
            answer_score=None,
            passes_threshold=None,
            issues=["provider_retry_exhausted"],
            review_status="failed",
            attempt_count=self.max_retries + 1,
            error_message=str(last_error) if last_error is not None else None,
        )
