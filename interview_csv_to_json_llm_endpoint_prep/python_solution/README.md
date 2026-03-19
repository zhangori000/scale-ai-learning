# Python Reference Solution

This solution is built around two endpoints:

- `POST /ingest-csv`
- `POST /classify-record`

It uses a manifest file per ingestion job so later classification requests can find the saved JSON artifacts.

## Files

- `models.py`
  - typed dataclasses for records and results
- `csv_parser.py`
  - CSV validation and parsing
- `storage.py`
  - atomic JSON read and write helpers
- `llm_client.py`
  - mock and HTTP classification clients
- `service.py`
  - orchestration logic
- `app.py`
  - FastAPI app factory and endpoints
- `test_service.py`
  - service-level tests
- `test_app.py`
  - endpoint tests with `TestClient`

## Run

```bash
python -m unittest discover -v
uvicorn app:app --reload --port 8030
```

## Endpoints

### `POST /ingest-csv`

Multipart form fields:

- `users_file`
- `tasks_file`

### `POST /classify-record`

JSON body:

```json
{
  "job_id": "returned by /ingest-csv",
  "dataset": "tasks",
  "row_index": 1,
  "label_options": ["task", "user"]
}
```

## Environment variables

- `USE_MOCK_CLASSIFIER=1` uses the mock classifier
- `USE_MOCK_CLASSIFIER=0` uses the HTTP classifier
- `CLASSIFIER_ENDPOINT=https://...`
- `CLASSIFIER_API_KEY=...`
- `STORE_DIR=./data`
