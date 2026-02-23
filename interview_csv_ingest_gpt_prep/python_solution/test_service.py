from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from csv_parser import CSVValidationError
from gpt_client import MockKeywordClassificationClient
from service import IngestService
from storage import LocalJSONStore


class FailingClassifier:
    def classify_batch(self, inputs, labels):
        raise RuntimeError("simulated GPT outage")


class IngestServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="ingest_test_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_happy_path(self) -> None:
        users_csv = b"user_id,name,email\nu1,Alice,alice@example.com\nu2,Bob,bob@example.com\n"
        tasks_csv = (
            b"task_id,user_id,description\n"
            b"t1,u1,Fix bug in auth\n"
            b"t2,u2,Add new feature for search\n"
            b"t3,u1,Update docs for setup\n"
        )

        svc = IngestService(
            store=LocalJSONStore(self.temp_dir),
            classifier=MockKeywordClassificationClient(),
            batch_size=2,
            max_parallel_batches=1,
        )
        result = svc.ingest(users_csv, tasks_csv, return_enriched_tasks=True)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.users_count, 2)
        self.assertEqual(result.tasks_count, 3)
        self.assertEqual(result.classified_tasks_count, 3)
        self.assertTrue(result.files["users_json"].endswith(".json"))
        self.assertTrue(result.files["tasks_enriched_json"].endswith(".json"))
        self.assertEqual(len(result.tasks or []), 3)
        cats = [t["category"] for t in (result.tasks or [])]
        self.assertIn("bug", cats)
        self.assertIn("feature", cats)
        self.assertIn("documentation", cats)

    def test_missing_required_header(self) -> None:
        users_csv = b"user_id,name\nu1,Alice\n"
        tasks_csv = b"task_id,user_id,description\nt1,u1,test\n"

        svc = IngestService(
            store=LocalJSONStore(self.temp_dir),
            classifier=MockKeywordClassificationClient(),
        )
        result = svc.ingest(users_csv, tasks_csv, return_enriched_tasks=False)
        self.assertEqual(result.status, "error")
        self.assertTrue(any("missing required columns" in e for e in result.errors))

    def test_gpt_failure_marks_unknown(self) -> None:
        users_csv = b"user_id,name,email\nu1,Alice,alice@example.com\n"
        tasks_csv = b"task_id,user_id,description\nt1,u1,Something\n"

        svc = IngestService(
            store=LocalJSONStore(self.temp_dir),
            classifier=FailingClassifier(),
        )
        result = svc.ingest(users_csv, tasks_csv, return_enriched_tasks=True)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.classified_tasks_count, 1)
        self.assertEqual((result.tasks or [])[0]["category"], "unknown")
        self.assertTrue((result.tasks or [])[0]["classification_error"])
        self.assertTrue(any("classification failed" in e for e in result.errors))

    def test_atomic_outputs_are_json(self) -> None:
        users_csv = b"user_id,name,email\nu1,Alice,alice@example.com\n"
        tasks_csv = b"task_id,user_id,description\nt1,u1,Fix bug\n"

        svc = IngestService(
            store=LocalJSONStore(self.temp_dir),
            classifier=MockKeywordClassificationClient(),
        )
        result = svc.ingest(users_csv, tasks_csv)
        for _, path in result.files.items():
            content = Path(path).read_text(encoding="utf-8")
            json.loads(content)  # must parse


if __name__ == "__main__":
    unittest.main()
