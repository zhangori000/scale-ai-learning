# CSV to JSON + LLM Endpoint Prep

This folder is a focused practice pack for the interview prompt:

1. accept `users.csv` and `tasks.csv`
2. parse them into local JSON files
3. expose an endpoint
4. classify one selected JSON record with an LLM API

It overlaps with your older CSV/GPT prep folder, but this version is tighter around the exact prompt and the endpoint design.

## Files

- `00_original_prompt_and_translation.md`
  - the English prompt plus the Chinese discussion translated into clean English
- `01_clarified_requirements.md`
  - hidden assumptions and prompt gaps you should state explicitly
- `02_endpoint_design_and_notes.md`
  - endpoint shape, storage flow, record selection strategy, and failure handling
- `03_interview_answer_script.md`
  - short answer script for interview delivery
- `python_solution/`
  - runnable FastAPI solution with tests

## Suggested study order

1. Read `00_original_prompt_and_translation.md`
2. Read `01_clarified_requirements.md`
3. Read `02_endpoint_design_and_notes.md`
4. Read `03_interview_answer_script.md`
5. Read `python_solution/README.md`
6. Run the tests

## Quick run

From `python_solution/`:

```bash
python -m unittest discover -v
uvicorn app:app --reload --port 8030
```
