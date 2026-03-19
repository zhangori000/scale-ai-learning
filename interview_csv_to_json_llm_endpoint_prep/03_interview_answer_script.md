# Interview Answer Script

I would split this into two endpoints. The first endpoint accepts `users.csv` and `tasks.csv`, validates them, parses them into typed records, and writes two local JSON files atomically. I would also generate a `job_id` and attach a `row_index` to each task row because the sample `tasks.csv` does not actually give me a unique task identifier.

For the LLM part, I would expose a second endpoint that takes the `job_id`, the dataset name, and the row index of the record to classify. That endpoint would load the saved JSON, select one record, build a very small classification prompt, call an LLM client wrapper, and return the label. I would keep the LLM behind an interface so I can swap between a mock client in tests and a real HTTP client in production.

If the interviewer asks about production concerns, I would mention file size limits, atomic writes, validation errors, idempotency, and retry handling for transient LLM failures.
