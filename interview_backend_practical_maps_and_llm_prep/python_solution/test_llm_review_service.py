from __future__ import annotations

import unittest

from fake_adapters import (
    FlakyLLMReviewer,
    HeuristicLLMReviewer,
    InMemoryCSVExporter,
    InMemoryTaskRepository,
    RecordingEmailClient,
)
from llm_review_service import LLMReviewJobService
from models import TaskRecord


class LLMReviewJobServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tasks = [
            TaskRecord(
                task_id="t1",
                customer="acme",
                project_id="p1",
                category="help",
                prompt="How do I reset my password?",
                response="You can reset your password from the account settings page.",
            ),
            TaskRecord(
                task_id="t2",
                customer="acme",
                project_id="p1",
                category="help",
                prompt="Explain caching.",
                response="Caching stores reusable results to reduce repeated work.",
            ),
            TaskRecord(
                task_id="t3",
                customer="acme",
                project_id="p2",
                category="help",
                prompt="Summarize this article.",
                response="summary unavailable",
            ),
        ]

    def test_run_job_generates_csv_and_email(self) -> None:
        exporter = InMemoryCSVExporter()
        email_client = RecordingEmailClient()
        service = LLMReviewJobService(
            task_repository=InMemoryTaskRepository(self.tasks),
            reviewer=HeuristicLLMReviewer(),
            exporter=exporter,
            email_client=email_client,
            sleep_fn=lambda _: None,
        )

        result = service.run_job(
            job_id="job-1",
            task_ids=["t1", "missing-task", "t2"],
            operator_email="ops@example.com",
        )

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.total_count, 3)
        self.assertEqual(result.failed_count, 1)
        self.assertEqual(result.csv_url, "memory://review-jobs/job-1.csv")
        self.assertIn("missing-task", exporter.exports["job-1"])
        self.assertEqual(email_client.sent, [("ops@example.com", result.csv_url)])

    def test_retryable_failures_are_retried(self) -> None:
        reviewer = FlakyLLMReviewer(
            HeuristicLLMReviewer(),
            retryable_failures={"t1": 2},
        )
        service = LLMReviewJobService(
            task_repository=InMemoryTaskRepository(self.tasks),
            reviewer=reviewer,
            exporter=InMemoryCSVExporter(),
            email_client=RecordingEmailClient(),
            max_retries=3,
            sleep_fn=lambda _: None,
        )

        result = service.run_job(
            job_id="job-2",
            task_ids=["t1"],
            operator_email="ops@example.com",
        )

        self.assertEqual(reviewer.calls["t1"], 3)
        self.assertEqual(result.results[0].review_status, "completed")
        self.assertEqual(result.results[0].attempt_count, 3)

    def test_task_limit_is_enforced(self) -> None:
        service = LLMReviewJobService(
            task_repository=InMemoryTaskRepository(self.tasks),
            reviewer=HeuristicLLMReviewer(),
            exporter=InMemoryCSVExporter(),
            email_client=RecordingEmailClient(),
            max_tasks=2,
            sleep_fn=lambda _: None,
        )

        with self.assertRaises(ValueError):
            service.run_job(
                job_id="job-3",
                task_ids=["t1", "t2", "t3"],
                operator_email="ops@example.com",
            )


if __name__ == "__main__":
    unittest.main()
