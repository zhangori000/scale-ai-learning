# LLM Quality Review Solution

## Clean problem statement

Operators can filter existing Mongo task blobs down to at most 5000 items, launch a review job, and later receive a CSV with LLM quality judgments.

The real backend problem is not "call an LLM 5000 times". It is:

1. selection
2. asynchronous job execution
3. provider instability
4. rate limits
5. resumability
6. result export

## Minimal architecture

```text
webapp -> review job API -> job row + task ids
                      -> worker pool
                      -> rate-limited LLM adapter
                      -> result store
                      -> CSV exporter
                      -> email service
```

## Main data models

I would add tables or collections like:

- `review_jobs`
  - `job_id`
  - `operator_email`
  - `status`
  - `selected_task_count`
  - `created_at`
  - `started_at`
  - `completed_at`
  - `csv_url`
  - `error_summary`
- `review_job_items`
  - `job_id`
  - `task_id`
  - `status`
  - `attempt_count`
  - `score`
  - `passes_threshold`
  - `issues`
  - `provider_response_excerpt`

## Agentex-style decomposition

- `TaskRepositoryPort`
  - reads selected task blobs from Mongo
- `LLMReviewerPort`
  - owns external provider HTTP calls
- `OpenAIResponsesLLMReviewer`
  - one concrete implementation using OpenAI's Responses API plus structured outputs
- `ReviewJobService`
  - orchestrates retries, progress, persistence, completion
- `CSVExporterPort`
  - writes final CSV somewhere durable
- `EmailPort`
  - notifies operator when the job is done

## Job lifecycle

1. Operator filters tasks in the webapp.
2. API validates `count <= 5000`.
3. API creates a `review_job` record and returns immediately.
4. Background workers process task reviews in bounded parallelism.
5. Each task review uses per-task retry with exponential backoff and jitter.
6. Terminal outputs are stored even when some items fail.
7. Once all items are terminal, build CSV and send email.

## Provider instability handling

Separate failures into two classes:

- Retryable
  - 429
  - connect timeout
  - read timeout
  - transient 5xx
- Non-retryable
  - malformed prompt
  - unsupported model parameters
  - invalid task payload
  - schema validation failure after several repair attempts

That is the same shape used in the Agentex Temporal examples: retry platform failures, stop retrying bad data.

## Real OpenAI call shape

If you want a concrete production-style implementation, the adapter in `python_solution/openai_review_client.py` uses:

- `POST https://api.openai.com/v1/responses`
- `Authorization: Bearer $OPENAI_API_KEY`
- `store: false`
- `text.format.type = "json_schema"`

That lets the reviewer ask the model for a structured grading object instead of free-form text, which makes parsing and downstream CSV generation much more reliable.

## Rate limit answer

Strong answer:

- Use bounded concurrency, not unbounded fan-out
- Enforce a token bucket or leaky bucket per model/API key
- Batch only if the provider supports reliable structured multi-item evaluation
- Keep retry state per task
- Add idempotency keys so replays do not duplicate stored results
- Persist partial progress so worker crashes do not restart from zero

## CSV output

Useful CSV columns:

- `task_id`
- `customer`
- `project_id`
- `category`
- `overall_score`
- `passes_threshold`
- `grammar_score`
- `style_score`
- `answer_quality_score`
- `issues`
- `review_status`
- `attempt_count`

## Good interview extension

If the interviewer pushes on scaling:

- 5000 tasks is batchable in one job, but not in one web request
- use a queue and worker fleet
- shard work at the item level
- surface job progress in the UI
- support cancel, retry failed-only, and re-export CSV

## What I would say in interview

I would model this as a job system, not a single request-response handler. The API only creates the job. Workers then fetch tasks from Mongo, call the external LLM through a rate-limited adapter, store per-task results with retry metadata, and once all items finish, export a CSV and email the operator. The important part is idempotent progress and per-task retries, not the raw HTTP call itself.
