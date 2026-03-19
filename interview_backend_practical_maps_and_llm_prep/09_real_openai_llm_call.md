# Real OpenAI LLM Call

If you want to see the concrete non-mock implementation for the LLM review problem, read:

- `python_solution/openai_review_client.py`
- `python_solution/test_openai_review_client.py`

## What it does

The adapter:

1. builds a review prompt from one `TaskRecord`
2. sends `POST /v1/responses`
3. requests structured JSON output using `text.format.type = "json_schema"`
4. parses the result into the existing `ReviewResult` dataclass
5. maps network and HTTP failures into retryable vs non-retryable errors

## Why structured output is important

If you let the model answer in free-form text, your parser becomes fragile.

For a batch review job, a much better production pattern is:

- ask for a small strict JSON object
- validate it
- convert it into your domain result

That is why the adapter asks the model for:

- `grammar_score`
- `style_score`
- `answer_score`
- `passes_threshold`
- `issues`
- `summary`

## Environment variable

Set:

```bash
OPENAI_API_KEY=...
```

Then:

```python
from openai_review_client import build_llm_reviewer

reviewer = build_llm_reviewer()
```

Without that key, the helper falls back to the heuristic mock reviewer so the rest of the code stays runnable.
