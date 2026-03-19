from __future__ import annotations

import io
import os
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from csv_parser import CSVValidationError
from llm_client import HTTPClassificationClient, MockKeywordClassificationClient
from service import CSVToJSONService
from storage import LocalJSONStore

MAX_FILE_BYTES = 10 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
    "application/octet-stream",
}


class ClassifyRecordRequest(BaseModel):
    job_id: str
    dataset: str = Field(..., pattern="^(users|tasks)$")
    row_index: int = Field(..., ge=0)
    label_options: list[str]


def create_app(service: CSVToJSONService | None = None) -> FastAPI:
    app = FastAPI(title="CSV to JSON + LLM Classification")
    resolved_service = service or _default_service()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/ingest-csv")
    async def ingest_csv(
        users_file: UploadFile = File(...),
        tasks_file: UploadFile = File(...),
    ) -> dict[str, Any]:
        _validate_content_type(users_file, "users_file")
        _validate_content_type(tasks_file, "tasks_file")

        try:
            users_bytes = await _read_with_limit(users_file, MAX_FILE_BYTES)
            tasks_bytes = await _read_with_limit(tasks_file, MAX_FILE_BYTES)
            result = resolved_service.ingest(users_bytes, tasks_bytes)
        except (CSVValidationError, UnicodeDecodeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return {
            "status": result.status,
            "job_id": result.manifest.job_id,
            "users_count": result.manifest.users_count,
            "tasks_count": result.manifest.tasks_count,
            "users_json_path": result.manifest.users_json_path,
            "tasks_json_path": result.manifest.tasks_json_path,
            "manifest_json_path": result.manifest.manifest_json_path,
        }

    @app.post("/classify-record")
    def classify_record(request: ClassifyRecordRequest) -> dict[str, Any]:
        try:
            result = resolved_service.classify_record(
                job_id=request.job_id,
                dataset=request.dataset,
                row_index=request.row_index,
                label_options=request.label_options,
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except IndexError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return {
            "job_id": result.job_id,
            "dataset": result.dataset,
            "row_index": result.row_index,
            "label": result.label,
            "label_options": result.label_options,
            "record": result.record,
            "classification_json_path": result.classification_json_path,
            "prompt": result.prompt,
        }

    return app


async def _read_with_limit(upload: UploadFile, max_bytes: int) -> bytes:
    buffer = io.BytesIO()
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
        buffer.write(chunk)
    return buffer.getvalue()


def _validate_content_type(upload: UploadFile, field_name: str) -> None:
    content_type = (upload.content_type or "").lower().strip()
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name}: unsupported content type {content_type}",
        )


def _default_service() -> CSVToJSONService:
    use_mock = os.getenv("USE_MOCK_CLASSIFIER", "1") == "1"
    store_dir = os.getenv("STORE_DIR", "./data")

    if use_mock:
        classifier = MockKeywordClassificationClient()
    else:
        classifier = HTTPClassificationClient(
            endpoint=os.getenv("CLASSIFIER_ENDPOINT", "https://example.com/classify"),
            api_key=os.getenv("CLASSIFIER_API_KEY"),
        )

    return CSVToJSONService(
        store=LocalJSONStore(store_dir),
        classifier=classifier,
    )


app = create_app()
