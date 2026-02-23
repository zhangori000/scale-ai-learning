from __future__ import annotations

import dataclasses
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from csv_parser import CSVValidationError, parse_tasks_csv, parse_users_csv
from gpt_client import ClassificationClient
from models import IngestResult, TaskRecord
from storage import LocalJSONStore


class IngestService:
    def __init__(
        self,
        store: LocalJSONStore,
        classifier: ClassificationClient,
        categories: list[str] | None = None,
        batch_size: int = 20,
        max_parallel_batches: int = 2,
    ) -> None:
        self.store = store
        self.classifier = classifier
        self.categories = categories or ["bug", "feature", "documentation"]
        self.batch_size = max(1, batch_size)
        self.max_parallel_batches = max(1, max_parallel_batches)

    def ingest(
        self,
        users_csv_bytes: bytes,
        tasks_csv_bytes: bytes,
        return_enriched_tasks: bool = False,
    ) -> IngestResult:
        job_id = str(uuid.uuid4())
        errors: list[str] = []

        try:
            users, user_errors = parse_users_csv(users_csv_bytes)
            tasks, task_errors = parse_tasks_csv(tasks_csv_bytes)
        except UnicodeDecodeError as exc:
            return IngestResult(
                status="error",
                job_id=job_id,
                users_count=0,
                tasks_count=0,
                classified_tasks_count=0,
                errors=[f"CSV decode error: {exc}"],
            )
        except CSVValidationError as exc:
            return IngestResult(
                status="error",
                job_id=job_id,
                users_count=0,
                tasks_count=0,
                classified_tasks_count=0,
                errors=[str(exc)],
            )

        errors.extend(user_errors)
        errors.extend(task_errors)

        users_payload = [dataclasses.asdict(u) for u in users]
        tasks_payload = [dataclasses.asdict(t) for t in tasks]

        files: dict[str, str] = {}
        files["users_json"] = str(
            self.store.write_json_atomic(f"users_{job_id}.json", users_payload)
        )
        files["tasks_json"] = str(
            self.store.write_json_atomic(f"tasks_{job_id}.json", tasks_payload)
        )

        classified_count = self._classify_tasks(tasks, errors)
        enriched_payload = [dataclasses.asdict(t) for t in tasks]
        files["tasks_enriched_json"] = str(
            self.store.write_json_atomic(f"tasks_enriched_{job_id}.json", enriched_payload)
        )

        result = IngestResult(
            status="ok",
            job_id=job_id,
            users_count=len(users),
            tasks_count=len(tasks),
            classified_tasks_count=classified_count,
            errors=errors,
            files=files,
            tasks=enriched_payload if return_enriched_tasks else None,
        )
        return result

    def _classify_tasks(self, tasks: list[TaskRecord], errors: list[str]) -> int:
        if not tasks:
            return 0

        batches: list[tuple[int, int]] = []
        for i in range(0, len(tasks), self.batch_size):
            j = min(i + self.batch_size, len(tasks))
            batches.append((i, j))

        if self.max_parallel_batches == 1:
            for start, end in batches:
                self._classify_batch(tasks, start, end, errors)
        else:
            with ThreadPoolExecutor(max_workers=self.max_parallel_batches) as pool:
                future_map = {
                    pool.submit(self._classify_batch, tasks, start, end, []): (start, end)
                    for start, end in batches
                }
                for fut in as_completed(future_map):
                    start, end = future_map[fut]
                    try:
                        batch_errors = fut.result()
                        errors.extend(batch_errors)
                    except Exception as exc:  # Defensive; should be rare.
                        for idx in range(start, end):
                            tasks[idx].category = "unknown"
                            tasks[idx].classification_error = True
                        errors.append(f"classification batch {start}:{end} crashed: {exc}")

        return sum(1 for t in tasks if t.category is not None)

    def _classify_batch(
        self,
        tasks: list[TaskRecord],
        start: int,
        end: int,
        errors: list[str],
    ) -> list[str]:
        local_errors: list[str] = []
        batch = tasks[start:end]
        inputs = [t.description for t in batch]
        try:
            labels = self.classifier.classify_batch(inputs, self.categories)
            if len(labels) != len(batch):
                raise ValueError("classification labels length mismatch")
            for task, label in zip(batch, labels):
                task.category = str(label)
                task.classification_error = False
        except Exception as exc:
            for task in batch:
                task.category = "unknown"
                task.classification_error = True
            local_errors.append(f"classification failed for batch {start}:{end}: {exc}")

        if errors is not None:
            errors.extend(local_errors)
        return local_errors
