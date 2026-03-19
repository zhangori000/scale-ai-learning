from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app import create_app
from llm_client import MockKeywordClassificationClient
from service import CSVToJSONService
from storage import LocalJSONStore


class AppTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="csv_json_llm_app_"))
        service = CSVToJSONService(
            store=LocalJSONStore(self.temp_dir),
            classifier=MockKeywordClassificationClient(),
        )
        self.client = TestClient(create_app(service))

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_ingest_csv_endpoint(self) -> None:
        response = self.client.post(
            "/ingest-csv",
            files={
                "users_file": ("users.csv", b"id,name\n1,Alice\n2,Bob\n", "text/csv"),
                "tasks_file": ("tasks.csv", b"id,task\n1,Task1\n1,Task2\n2,Task3\n", "text/csv"),
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["users_count"], 2)
        self.assertEqual(payload["tasks_count"], 3)

    def test_classify_record_endpoint(self) -> None:
        ingest_response = self.client.post(
            "/ingest-csv",
            files={
                "users_file": ("users.csv", b"id,name\n1,Alice\n2,Bob\n", "text/csv"),
                "tasks_file": ("tasks.csv", b"id,task\n1,Task1\n1,Task2\n2,Task3\n", "text/csv"),
            },
        )
        job_id = ingest_response.json()["job_id"]

        classify_response = self.client.post(
            "/classify-record",
            json={
                "job_id": job_id,
                "dataset": "tasks",
                "row_index": 2,
                "label_options": ["task", "user"],
            },
        )

        self.assertEqual(classify_response.status_code, 200)
        payload = classify_response.json()
        self.assertEqual(payload["label"], "task")
        self.assertEqual(payload["record"]["task"], "Task3")


if __name__ == "__main__":
    unittest.main()
