from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from llm_client import MockKeywordClassificationClient
from service import CSVToJSONService
from storage import LocalJSONStore


class CSVToJSONServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="csv_json_llm_"))
        self.service = CSVToJSONService(
            store=LocalJSONStore(self.temp_dir),
            classifier=MockKeywordClassificationClient(),
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_ingest_writes_json_and_manifest(self) -> None:
        users_csv = b"id,name\n1,Alice\n2,Bob\n"
        tasks_csv = b"id,task\n1,Task1\n1,Task2\n2,Task3\n"

        result = self.service.ingest(users_csv, tasks_csv)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.manifest.users_count, 2)
        self.assertEqual(result.manifest.tasks_count, 3)
        self.assertTrue(Path(result.manifest.users_json_path).exists())
        self.assertTrue(Path(result.manifest.tasks_json_path).exists())
        self.assertTrue(Path(result.manifest.manifest_json_path).exists())

    def test_classify_record_uses_row_index_and_writes_artifact(self) -> None:
        users_csv = b"id,name\n1,Alice\n2,Bob\n"
        tasks_csv = b"id,task\n1,Task1\n1,Task2\n2,Task3\n"
        ingest_result = self.service.ingest(users_csv, tasks_csv)

        result = self.service.classify_record(
            job_id=ingest_result.manifest.job_id,
            dataset="tasks",
            row_index=1,
            label_options=["task", "user"],
        )

        self.assertEqual(result.label, "task")
        self.assertEqual(result.record["task"], "Task2")
        self.assertTrue(Path(result.classification_json_path).exists())

    def test_classify_record_invalid_row_index_raises(self) -> None:
        users_csv = b"id,name\n1,Alice\n2,Bob\n"
        tasks_csv = b"id,task\n1,Task1\n1,Task2\n2,Task3\n"
        ingest_result = self.service.ingest(users_csv, tasks_csv)

        with self.assertRaises(IndexError):
            self.service.classify_record(
                job_id=ingest_result.manifest.job_id,
                dataset="tasks",
                row_index=10,
                label_options=["task", "user"],
            )


if __name__ == "__main__":
    unittest.main()
