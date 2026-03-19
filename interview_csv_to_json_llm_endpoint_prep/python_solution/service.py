from __future__ import annotations

import dataclasses
import uuid

from csv_parser import parse_tasks_csv, parse_users_csv
from llm_client import ClassificationClient
from models import ClassificationResult, IngestManifest, IngestResponse
from storage import LocalJSONStore


class CSVToJSONService:
    def __init__(
        self,
        store: LocalJSONStore,
        classifier: ClassificationClient,
    ) -> None:
        self.store = store
        self.classifier = classifier

    def ingest(
        self,
        users_csv_bytes: bytes,
        tasks_csv_bytes: bytes,
    ) -> IngestResponse:
        job_id = str(uuid.uuid4())
        users = parse_users_csv(users_csv_bytes)
        tasks = parse_tasks_csv(tasks_csv_bytes)

        users_payload = [dataclasses.asdict(record) for record in users]
        tasks_payload = [dataclasses.asdict(record) for record in tasks]

        users_path = self.store.write_json_atomic(f"users_{job_id}.json", users_payload)
        tasks_path = self.store.write_json_atomic(f"tasks_{job_id}.json", tasks_payload)

        manifest_payload = {
            "job_id": job_id,
            "users_json_path": str(users_path),
            "tasks_json_path": str(tasks_path),
            "users_count": len(users_payload),
            "tasks_count": len(tasks_payload),
        }
        manifest_path = self.store.write_json_atomic(
            f"manifest_{job_id}.json",
            manifest_payload,
        )

        manifest = IngestManifest(
            job_id=job_id,
            users_json_path=str(users_path),
            tasks_json_path=str(tasks_path),
            manifest_json_path=str(manifest_path),
            users_count=len(users_payload),
            tasks_count=len(tasks_payload),
        )
        return IngestResponse(status="ok", manifest=manifest)

    def classify_record(
        self,
        *,
        job_id: str,
        dataset: str,
        row_index: int,
        label_options: list[str],
    ) -> ClassificationResult:
        if dataset not in {"users", "tasks"}:
            raise ValueError("dataset must be either 'users' or 'tasks'")
        if not label_options:
            raise ValueError("label_options must not be empty")

        manifest = self._load_manifest(job_id)
        dataset_path = manifest[f"{dataset}_json_path"]
        records = self.store.read_json(dataset_path)

        if row_index < 0 or row_index >= len(records):
            raise IndexError(f"row_index {row_index} is out of range for dataset {dataset}")

        record = records[row_index]
        label, prompt = self.classifier.classify_record(record, label_options)

        classification_payload = {
            "job_id": job_id,
            "dataset": dataset,
            "row_index": row_index,
            "label": label,
            "label_options": label_options,
            "record": record,
            "prompt": prompt,
        }
        classification_path = self.store.write_json_atomic(
            f"classification_{job_id}_{dataset}_{row_index}.json",
            classification_payload,
        )

        return ClassificationResult(
            job_id=job_id,
            dataset=dataset,
            row_index=row_index,
            label=label,
            label_options=list(label_options),
            record=record,
            classification_json_path=str(classification_path),
            prompt=prompt,
        )

    def _load_manifest(self, job_id: str) -> dict:
        return self.store.read_json(f"manifest_{job_id}.json")
