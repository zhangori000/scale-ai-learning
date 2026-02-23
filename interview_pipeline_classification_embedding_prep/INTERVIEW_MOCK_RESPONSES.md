# Mock Interview Responses

Use these as spoken templates.

## 1) "Walk me through your design."

"I split the API into synchronous and asynchronous paths.  
For small uploads, `POST /v1/documents:process` handles files inline for low latency.  
For bulk uploads up to 1,000 files, `POST /v1/documents/batch:upload` stores raw files in object storage, creates metadata records, and enqueues per-document tasks.  
Workers consume tasks, extract text, call classification and embedding services in batched parallel requests, then persist labels and embeddings.  
Clients poll `GET /v1/jobs/{job_id}` for progress and can fetch detailed results later."

## 2) "How do you meet both low latency and high throughput?"

"I use two execution paths.  
Sync path avoids queue delay and returns immediate results for small requests.  
Bulk path decouples ingestion from heavy ML work using a queue, so API latency is low even for 1,000 files.  
Workers scale horizontally and batch calls to ML services for throughput."

## 3) "How do you handle partial failures?"

"Failure is tracked per document, not only per job.  
If one file fails extraction or ML calls keep failing after retries, that document is marked failed with an error reason.  
Other documents continue processing.  
Job status becomes `partial` if there is a mix of successes and failures."

## 4) "What are your retry and timeout policies?"

"Each ML service call has a strict timeout and bounded retries with exponential backoff.  
Messages are acknowledged only after terminal outcome is persisted.  
Repeated failures can be moved to a dead-letter queue in production."

## 5) "How do you store embeddings for semantic search?"

"I store metadata in a relational model and embeddings in a vector store keyed by `document_id`.  
That supports semantic search and filtering by metadata such as `user_id`, `job_id`, and label."

## 6) "What metrics would you monitor?"

"Job counters by status, document success/failure rate, queue depth and age, worker utilization, classification/embedding latency distributions, and ML call error rates.  
I also log with `job_id` and `document_id` for fast debugging."

## 7) "How do you avoid memory issues with 1,000 files?"

"I stream each file to object storage during upload rather than buffering all files in memory.  
Workers then pull file content on demand, process in bounded-size batches, and release memory quickly."

## 8) "How would you extend this design?"

"Add idempotency keys, dedupe by file hash, support chunked document parsing, implement priority queues for latency-sensitive traffic, and autoscale workers based on queue depth and task age."
