# Concepts: Classification + Embedding Pipeline Design

This note teaches the design at interview depth.

## 1) Problem framing

You must integrate two black-box ML APIs:

1. Classification API: text -> label
2. Embedding API: text -> vector

And support two very different workloads:

1. Small/single uploads (low latency)
2. Large/bulk uploads up to 1,000 files (high throughput)

## 2) API strategy: split sync and async paths

Use two endpoints:

1. `POST /v1/documents:process` (sync)
   - small requests only
   - return results immediately
2. `POST /v1/documents/batch:upload` (async)
   - up to 1,000 files
   - return `job_id`
   - client polls `GET /v1/jobs/{job_id}`

Why:

- sync only path cannot scale reliably for 1,000 files
- async only path hurts UX for small requests
- split path gives both low latency and throughput

## 3) Core architecture

```text
Client
  -> API/Ingestion
       -> Object Store (raw files)
       -> Metadata DB (jobs, documents, statuses)
       -> Queue (document work items)
  -> Worker Pool
       -> Text extraction
       -> Classification Service (batched)
       -> Embedding Service (batched, parallel to classification)
       -> Results DB + Vector Store
  -> Status/Results API
```

## 4) Data model essentials

Job:

- `job_id`, `user_id`, `status`
- `total_files`, `processed_files`, `failed_files`
- `errors[]`

Document:

- `document_id`, `job_id`, `filename`, `storage_uri`
- `status`, `attempts`, `error_message`

DocumentResult:

- `document_id`
- `label`
- `embedding`

## 5) Throughput strategy

For bulk:

1. stream upload directly to object store (avoid loading all files in memory)
2. enqueue one work item per document
3. workers pull queue items and batch ML calls
4. workers scale horizontally on queue depth

Batch tuning knobs:

- `batch_size`
- `batch_wait_ms`
- number of worker threads/processes

Tradeoff:

- larger batches improve throughput
- smaller batches improve per-document latency

## 6) Reliability behavior

Per-document failure handling:

- extraction failure -> mark that document failed
- ML call failure -> retry document with exponential backoff
- retry exhausted -> failed document

Job status derives from document outcomes:

- all success -> `completed`
- all failed -> `failed`
- mixed -> `partial`

Important:

- do not fail entire job because one document fails
- this is expected in real ingestion systems

## 7) Observability checklist

Metrics:

- jobs created/completed/failed/partial
- documents processed/failed
- queue depth
- classification/embedding latency + failure count

Logs:

- always include `job_id` and `document_id` for correlation

Tracing:

- if available, trace API -> queue -> worker -> ML calls

## 8) Interview pitfalls to avoid

1. one endpoint that blocks on 1,000 files synchronously
2. writing raw file bytes into DB instead of object storage
3. no retry/backoff around ML calls
4. no per-document status, only job-level status
5. no vector storage/search plan for embeddings

## 9) Why black-box constraint matters

You cannot optimize model internals.
So your levers are:

- request batching
- concurrency limits
- retries/timeouts/circuit breakers
- graceful degradation on partial failures
