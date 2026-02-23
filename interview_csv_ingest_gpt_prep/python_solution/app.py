from __future__ import annotations

import io
import os
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile

from gpt_client import HTTPClassificationClient, MockKeywordClassificationClient
from service import IngestService
from storage import LocalJSONStore

MAX_FILE_BYTES = 10 * 1024 * 1024  # 10MB
ALLOWED_CONTENT_TYPES = {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",  # common browser/client CSV content type
    "application/octet-stream",  # some clients send this
}

app = FastAPI(title="CSV Ingest + GPT Classification")

USE_MOCK = os.getenv("USE_MOCK_CLASSIFIER", "1") == "1"
STORE_DIR = os.getenv("STORE_DIR", "./data")

if USE_MOCK:
    classifier = MockKeywordClassificationClient()
else:
    endpoint = os.getenv("GPT_CLASSIFIER_ENDPOINT", "https://gpt.example.com/v1/classify")
    api_key = os.getenv("GPT_API_KEY")
    classifier = HTTPClassificationClient(endpoint=endpoint, api_key=api_key)

service = IngestService(
    store=LocalJSONStore(STORE_DIR),
    classifier=classifier,
    categories=["bug", "feature", "documentation"],
    batch_size=20,
    max_parallel_batches=2,
)


async def _read_with_limit(upload: UploadFile, max_bytes: int) -> bytes:
    buf = io.BytesIO()
    total = 0
    while True:
        chunk = await upload.read(64 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"{upload.filename or 'file'} exceeds size limit {max_bytes} bytes",
            )
        buf.write(chunk)
    return buf.getvalue()


def _validate_content_type(upload: UploadFile, field_name: str) -> None:
    content_type = (upload.content_type or "").lower().strip()
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name}: unsupported content type {content_type}",
        )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ingest-data")
async def ingest_data(
    users_file: UploadFile = File(...),
    tasks_file: UploadFile = File(...),
    return_tasks: bool = False,
) -> dict[str, Any]:
    if users_file is None:
        raise HTTPException(status_code=400, detail="users_file is required")
    if tasks_file is None:
        raise HTTPException(status_code=400, detail="tasks_file is required")

    _validate_content_type(users_file, "users_file")
    _validate_content_type(tasks_file, "tasks_file")

    users_bytes = await _read_with_limit(users_file, MAX_FILE_BYTES)
    tasks_bytes = await _read_with_limit(tasks_file, MAX_FILE_BYTES)

    result = service.ingest(
        users_csv_bytes=users_bytes,
        tasks_csv_bytes=tasks_bytes,
        return_enriched_tasks=return_tasks,
    )

    if result.status == "error":
        raise HTTPException(status_code=400, detail={"status": result.status, "errors": result.errors})

    payload = {
        "status": result.status,
        "job_id": result.job_id,
        "users_count": result.users_count,
        "tasks_count": result.tasks_count,
        "classified_tasks_count": result.classified_tasks_count,
        "errors": result.errors,
        "files": result.files,
    }
    if return_tasks:
        payload["tasks"] = result.tasks
    return payload
