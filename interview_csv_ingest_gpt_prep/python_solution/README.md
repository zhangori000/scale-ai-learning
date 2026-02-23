# Python Reference Implementation (Interview Prep)

This folder contains a practical implementation you can study and run.

## Contents

- `app.py` - FastAPI endpoint (`POST /ingest-data`)
- `service.py` - orchestration logic
- `csv_parser.py` - CSV validation/parsing
- `storage.py` - atomic local JSON writes
- `gpt_client.py` - GPT client abstraction + mock classifier
- `models.py` - data models/result shape
- `test_service.py` - unit tests for core flow

## Run tests (no FastAPI install needed)

```bash
python -m unittest test_service.py -v
```

## Run API (FastAPI required)

Install deps:

```bash
python -m pip install fastapi uvicorn
```

Run:

```bash
uvicorn app:app --reload --port 8020
```

Health check:

- `GET http://127.0.0.1:8020/health`

Swagger docs:

- `http://127.0.0.1:8020/docs`

## Sample request (curl)

```bash
curl -X POST "http://127.0.0.1:8020/ingest-data?return_tasks=true" \
  -F "users_file=@users.csv" \
  -F "tasks_file=@tasks.csv"
```

## Environment variables

- `USE_MOCK_CLASSIFIER=1` (default) uses keyword mock, no external API needed.
- `USE_MOCK_CLASSIFIER=0` to use real HTTP classifier.
- `GPT_CLASSIFIER_ENDPOINT=https://...`
- `GPT_API_KEY=...`
- `STORE_DIR=./data`
