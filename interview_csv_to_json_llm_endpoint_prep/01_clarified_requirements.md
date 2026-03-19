# Clarified Requirements

This prompt sounds simple, but it hides several design decisions.

## Assumptions I would say out loud

- The endpoint accepts two CSV uploads in one request.
- We write two local JSON files, one for users and one for tasks.
- The endpoint returns the file paths and basic counts.
- Classification is a separate operation from ingestion.
- We classify exactly one selected record from one of the saved JSON datasets.
- Because `tasks.csv` in the sample does not have a unique task ID, the classification endpoint should identify a record by dataset plus row index, or by a generated `row_id`.

## Better API split

Instead of forcing everything into one huge endpoint, I would expose:

1. `POST /ingest-csv`
   - upload `users.csv` and `tasks.csv`
   - parse
   - write JSON locally
   - return metadata
2. `POST /classify-record`
   - specify which dataset and which row to classify
   - call the LLM client
   - optionally persist the classification result locally

This is easier to test, easier to reason about, and closer to production design.

## Hidden edge cases

- missing required CSV headers
- invalid UTF-8
- duplicate or ambiguous IDs
- very large files
- partial write failure
- classifying a row index that does not exist
- LLM timeout or provider outage

## What the interviewer is probably testing

- Can you handle file uploads?
- Can you parse CSV safely?
- Can you write files atomically?
- Can you avoid coupling your business logic directly to the LLM API?
- Can you design something testable under time pressure?
