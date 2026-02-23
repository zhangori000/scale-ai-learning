# Annotated Notes: CSV Upload + GPT Classification Endpoint

This file adds deeper explanation to the original prompt so you can study offline.

## 1) What this interview question is *really* testing

Not just "can you parse CSV."

They are testing if you can build a reliable ingestion pipeline with:

1. HTTP contract clarity
2. input validation
3. safe local persistence
4. third-party API integration under failure
5. concurrency safety and testability

## 2) Most confusing terms explained

## `multipart/form-data`

- This is how browsers/clients upload files over HTTP.
- Request body has multiple "parts" (fields/files), each with headers.
- Your endpoint should extract `users_file` and `tasks_file`.

What interviewers care about:

1. You validate both files exist.
2. You enforce size limits.
3. You reject unsupported file types early.

## "Stream parse CSV"

- Means parse rows incrementally instead of loading full file into RAM first.
- Python `csv.DictReader(file_obj)` already works row-by-row.

Why it matters:

- Prevents memory spikes on large uploads.
- Allows row-level validation without full buffering.

## "Write atomically"

Bad pattern:

1. Open `tasks.json`
2. Write directly
3. Crash mid-write -> corrupted partial file

Good pattern:

1. Write `tasks.json.tmp`
2. `flush + fsync`
3. `os.replace(tmp, final)` (atomic rename on same filesystem)

## "Concurrency-safe local files"

If all requests write to `tasks.json`, concurrent requests overwrite each other.

Fix:

- use per-request `job_id` filenames:
  - `users_<job_id>.json`
  - `tasks_<job_id>.json`
  - `tasks_enriched_<job_id>.json`

## GPT integration: per-record vs batch

Per-record:

- easy mapping
- too many network calls

Batch:

- fewer calls, better throughput
- requires index mapping between inputs and labels

Interview-safe answer:

1. default to batch size 20~50
2. adjustable by config
3. keep order so label maps back to original task row

## "Partial failure policy"

When one GPT batch fails, do not fail entire ingestion by default.

Common policy:

1. retry few times (exponential backoff)
2. if still failing, mark those records:
   - `category="unknown"`
   - `classification_error=true`
3. continue other batches

## Idempotency (important)

If client retries same upload due to timeout, avoid duplicated side effects.

Practical interview options:

1. simple: always create new job (acceptable baseline)
2. better: optional `Idempotency-Key` header
3. best: content hash mapping `(users_hash, tasks_hash) -> prior job_id`

## Timeout strategy

Use layered timeouts:

1. Upload parsing timeout / file size caps
2. Per GPT request timeout (e.g., 8-10s)
3. Optional total endpoint timeout budget (e.g., 60s)

If budget exceeded:

- return partial stats + error summary, or
- move to async job model (`202 Accepted + job_id`)

## 3) Suggested architecture decomposition

Keep logic modular:

1. `api layer`
   - parse multipart
   - return HTTP response
2. `csv parser layer`
   - schema/header validation
   - row normalization
3. `storage layer`
   - atomic JSON writes
4. `classifier client layer`
   - GPT calls + retry/backoff
5. `ingestion service layer`
   - orchestration

This separation makes tests much easier.

## 4) Interview talk track (2-3 minutes)

1. "I define a strict multipart API contract with two required files."
2. "I stream-parse both CSVs and validate schema + required fields."
3. "I write parsed JSON atomically using per-job filenames."
4. "I classify task descriptions via batched GPT calls with retries and timeouts."
5. "I tolerate partial GPT failures by tagging affected tasks."
6. "I return counts + error summary + optional enriched tasks."
7. "I keep components separated for testability and concurrent safety."

## 5) Common pitfalls (mention proactively)

1. assuming `text/csv` only; many clients send `application/vnd.ms-excel`
2. not validating missing CSV headers
3. writing same output filename across concurrent requests
4. no timeout/retry around GPT call
5. dropping row-level parse errors silently
6. leaking full file content in logs (PII risk)

## 6) If interviewer asks "how to scale"

Say:

1. synchronous path for small files
2. async job queue for large files
3. object storage instead of local disk
4. background workers for GPT classification
5. job status endpoint for progress polling
