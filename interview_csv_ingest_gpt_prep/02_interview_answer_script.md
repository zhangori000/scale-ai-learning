# Interview Answer Script (Concise + Structured)

Use this if asked to explain your solution quickly.

## 1) Clarify assumptions

1. Two CSV files arrive in one multipart request.
2. Required headers are fixed (`users`: user_id,name,email; `tasks`: task_id,user_id,description).
3. Synchronous response is acceptable for moderate file sizes.
4. GPT endpoint returns one label per input text.

## 2) API contract

`POST /ingest-data`

Request:

- `multipart/form-data`
- `users_file` (required)
- `tasks_file` (required)

Response (success):

- status
- counts
- error summary
- optional enriched tasks (small payload mode)

Response (error):

- clear message
- validation details

## 3) Internal flow

1. Validate files + size + mime.
2. Parse CSV streams with header and row validation.
3. Persist `users` and `tasks` to JSON atomically under per-job filenames.
4. Batch classify task descriptions via GPT client with retry/backoff and timeout.
5. Merge labels into tasks; mark partial failures explicitly.
6. Persist enriched tasks JSON.
7. Return stats.

## 4) Failure handling

1. Missing/malformed CSV -> 400.
2. Oversized upload -> 413.
3. GPT timeout/error -> partial success with task-level errors (or fail-fast policy, if product requires).
4. Unexpected internal error -> 500 with trace-safe message.

## 5) Concurrency and reliability

1. No shared output filenames; use `job_id`.
2. Atomic file writes (`tmp -> os.replace`).
3. Bounded parallel GPT batches to avoid vendor rate-limit overload.
4. Optional idempotency key to dedupe retries.

## 6) Testing plan

1. Unit:
   - CSV parser valid/invalid
   - atomic writer
   - batch classifier mapping/retry behavior
2. Integration:
   - endpoint happy path with mocked GPT
   - missing file, bad headers, GPT failures
3. Concurrency:
   - multiple simultaneous requests produce distinct output files
