Design CSV upload endpoint with GPT classification
Last updated: Dec 23, 2025
Quick Overview
This question evaluates backend engineering skills including HTTP API design, multipart file handling, CSV parsing and serialization, local JSON persistence, and integration with an external GPT-style classification API.

Scale AI logo
Scale AI
Dec 8, 2025, 7:32 PM
Software Engineer
Onsite
Software Engineering Fundamentals
15
0



You are building a backend service that needs to process two CSV files and then call an external GPT-like API for classification.

Requirements

HTTP Endpoint
Expose an HTTP endpoint, e.g. POST /ingest-data .
The client uploads two CSV files in a single request:
users.csv
tasks.csv
A typical row in users.csv might be: user_id,name,email .
A typical row in tasks.csv might be: task_id,user_id,description .
CSV Parsing and Local JSON Storage
The endpoint should:
Receive the two CSV files.
Parse them into in-memory data structures (e.g., lists of objects).
Serialize each dataset into JSON.
Persist the resulting JSON to the local filesystem (e.g., users.json , tasks.json ).
GPT Classification Step
After parsing, the service should call an external GPT-like API to classify one field in the JSON data. For example:
For each task in tasks.json , classify the description into one of a small set of categories (e.g., "bug" , "feature" , "documentation" ).
The GPT API:
Is accessed via HTTPS.
Takes a text prompt and returns a classification label in JSON.
You are free to design the prompt and to decide whether to call the GPT API per-record or in batches, as long as all tasks end up with a classification label.
Response
After classification, return an HTTP response that includes at least:
A success indicator.
Basic stats (e.g., number of users, number of tasks processed).
Optionally, the enriched tasks data with the new classification field.
Non-functional Requirements
Handle basic validation and error cases (missing file, malformed CSV, GPT API failure).
Assume multiple clients may call this endpoint concurrently.
The solution should be reasonably testable.
Task

Describe how you would design and implement this endpoint, including:

The HTTP API contract (request format, response format).
How you handle file uploads and CSV parsing.
How you structure the code to write JSON to local storage.
How you integrate with the GPT classification API (including error handling and possible batching).
Considerations for concurrency, timeouts, and testing.
Solution
Hide
1. API Contract
Endpoint

POST /ingest-data
Request Format

Content-Type: multipart/form-data .
Fields:
users_file : file ( users.csv )
tasks_file : file ( tasks.csv )
Example (curl):
curl -X POST https://api.example.com/ingest-data \
  -F "users_file=@users.csv" \
  -F "tasks_file=@tasks.csv"
Response Format (success)

{
  "status": "ok",
  "users_count": 123,
  "tasks_count": 456,
  "classified_tasks_count": 456,
  "errors": []
}
Optionally add a field like "tasks": [ ... ] if you want to return the enriched data (for small datasets).

Response Format (error)

{
  "status": "error",
  "message": "tasks_file is missing",
  "errors": ["tasks_file is required"]
}
2. High-level Flow Inside the Endpoint
Validate Request
Check both users_file and tasks_file are present.
Enforce size limits (e.g., max 10MB each) to avoid memory issues.
Store Raw Uploads (optional)
Optionally stream files to a temp directory for auditing or reprocessing.
Parse CSVs
Stream-parse users.csv into a list of User objects.
Stream-parse tasks.csv into a list of Task objects.
Serialize to JSON and Save Locally
Convert users list to JSON and write to users.json .
Convert tasks list to JSON and write to tasks.json .
Call GPT Classification API
For each task, call GPT (individually or batched) to classify the description .
Add a category field to each task.
Persist Enriched Data
Optionally write an enriched tasks_enriched.json with classifications.
Return Response
Include counts and any high-level error information.
3. Handling File Uploads & CSV Parsing
File Upload Handling

Use built-in framework support (examples):
Python / FastAPI: UploadFile with File(...) .
Node.js / Express: multer for multipart handling.
Java / Spring: @RequestPart MultipartFile users_file .
Enforce:
MIME type checks ( text/csv , application/vnd.ms-excel etc.).
Size limit via server configuration or application-level checks.
CSV Parsing Strategy

Use a streaming parser (to avoid loading entire file into memory at once):
Python: csv module iterating over file object.
Node: csv-parser or similar.
Java: OpenCSV or Apache Commons CSV with streaming.
Pseudocode for parsing tasks.csv :
tasks = []
for row in csv_reader(tasks_file_stream):
    # Validate required columns exist once, on header
    # Assume columns: task_id, user_id, description
    tasks.append({
        "task_id": row["task_id"],
        "user_id": row["user_id"],
        "description": row["description"]
    })
Validation

On header row:
Ensure required columns present.
On each row:
Basic validation (non-empty IDs, description length within limits).
Collect row-level errors but keep processing when possible.
4. Writing JSON to Local Storage
File Paths

Store under a known directory, e.g., /var/app/data/ :
/var/app/data/users.json
/var/app/data/tasks.json
/var/app/data/tasks_enriched.json (after classification).
Serialization

Use the language's native JSON library (e.g. json in Python, Jackson in Java).
Write atomically:
Write to a temp file users.json.tmp then rename to users.json to avoid partial writes.
Concurrency Considerations

If multiple requests might write to the same filename:
Include a request ID or timestamp in filenames, e.g., users_<uuid>.json .
Alternatively, make ingestion jobs explicit and store job_id that maps to filenames.
5. Integrating with the GPT Classification API
Assume a hypothetical GPT API:

Endpoint: POST https://gpt.example.com/v1/classify
Request body:
{
  "model": "gpt-classifier-001",
  "examples": ["bug", "feature", "documentation"],
  "inputs": ["text1", "text2", ...]
}
Response body:
{
  "labels": ["bug", "feature", ...]
}
Strategy: Batch vs Per-record

If GPT API supports multiple inputs per call, prefer batching :
Reduces network overhead and improves throughput.
Example: batch size of 20–50 descriptions per request.
Steps:
Extract all description fields from tasks .
Break them into batches.
For each batch, call GPT and receive labels.
Attach labels back to the corresponding task objects.
Pseudocode for Batching

batch_size = 20
for i in range(0, len(tasks), batch_size):
    batch = tasks[i : i + batch_size]
    inputs = [t.description for t in batch]
    response = call_gpt_api(inputs)
    labels = response.labels
    for j, task in enumerate(batch):
        task.category = labels[j]
Error Handling for GPT Calls

Network/timeout errors:
Retry with exponential backoff, up to a small number of attempts.
API errors (4xx, 5xx):
Log details.
Mark affected tasks with category = "unknown" or classification_error = true .
Partial failures:
If one batch fails, continue with others to maximize successful classification.
Timeouts

Set reasonable per-request timeouts (e.g., 5–15 seconds per GPT call).
If the overall classification might be long, consider:
Asynchronous job model (client gets job_id and checks later). For this exercise, a synchronous implementation is acceptable if datasets are small.
6. Concurrency & Performance Considerations
Parallel GPT Requests
If you have many tasks and GPT API rate limits allow, send multiple batches in parallel using a worker pool.
Maintain pool size based on:
CPU/network capacity of your server.
GPT vendor's QPS and concurrency limits.
Memory Usage
For very large CSVs, avoid building huge in-memory structures. Since you also need to send data to GPT, some in-memory representation is inevitable, but you can:
Stream parse and classify in chunks.
Write intermediate results to disk if necessary.
Idempotency
If the client retries the same upload, you may:
Generate a job_id and store mapping from content hash(s) to job results.
Or accept re-processing (simpler for an interview solution).
7. Testing Strategy
Unit Tests

CSV parsing:
Test with well-formed CSV.
Test missing columns and malformed rows.
JSON serialization:
Verify the expected structure and field names.
Integration Tests

Endpoint with mocked GPT API:
Use an HTTP mock (or dependency injection) to return deterministic labels.
Verify that category is added to each task and JSON files are written.
Error-path Tests

Missing one of the files.
GPT API failure (500, timeout).
Oversized file rejection.
This design cleanly separates concerns (upload handling, parsing, persistence, GPT integration), is safe under concurrent calls (with careful filename/job handling), and is straightforward to extend (e.g., moving from local disk to cloud storage or switching GPT vendors).
