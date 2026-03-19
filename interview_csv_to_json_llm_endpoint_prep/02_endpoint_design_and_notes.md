# Endpoint Design and Notes

## Recommended endpoints

### `POST /ingest-csv`

Request:

- `users_file`
- `tasks_file`

Behavior:

1. validate content type and size
2. parse both CSVs
3. attach a generated `row_index` to each task record
4. write `users_<job_id>.json`
5. write `tasks_<job_id>.json`
6. return counts and file paths

### `POST /classify-record`

Request body:

```json
{
  "job_id": "ingest job id",
  "dataset": "tasks",
  "row_index": 1,
  "label_options": ["bug", "feature", "question"]
}
```

Behavior:

1. locate the correct saved JSON file
2. load the record
3. build a simple classification prompt
4. call the LLM client
5. save a local classification artifact
6. return the label and record payload

## Architecture

Keep the same shape as the stronger backend repos:

- parser layer
  - CSV parsing and schema checks
- storage layer
  - atomic JSON writes and reads
- service layer
  - orchestration and validation
- LLM client layer
  - mock client for tests
  - HTTP client for real provider calls
- API layer
  - thin FastAPI endpoints

## Good implementation choices

- use atomic writes so you do not leave half-written JSON files
- keep a manifest per ingestion job so later classification can find the files
- store task rows as a list, not a dict keyed by `id`, because task IDs are ambiguous in the sample
- generate `row_index` on ingest so selecting a record is deterministic
- hide the LLM provider behind an interface so tests never need real network calls

## Minimal prompt for classification

You do not need fancy prompt engineering here. Something like this is enough:

```text
You are classifying one JSON record.
Choose exactly one label from: bug, feature, question.
Return only the label.
Record:
{...json...}
```

## Good interview explanation

The ingestion path and the LLM path should not be tightly coupled. Ingest should succeed even if the LLM is down, and classification should operate on already-saved JSON artifacts. That separation gives you cleaner failure modes and much better testability.
