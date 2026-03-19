from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from fake_adapters import HeuristicLLMReviewer
from models import NonRetryableProviderError, RetryableProviderError, ReviewResult, TaskRecord
from ports import LLMReviewerPort


REVIEW_OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "grammar_score": {"type": "integer", "minimum": 1, "maximum": 5},
        "style_score": {"type": "integer", "minimum": 1, "maximum": 5},
        "answer_score": {"type": "integer", "minimum": 1, "maximum": 5},
        "passes_threshold": {"type": "boolean"},
        "issues": {
            "type": "array",
            "items": {"type": "string"},
        },
        "summary": {"type": "string"},
    },
    "required": [
        "grammar_score",
        "style_score",
        "answer_score",
        "passes_threshold",
        "issues",
        "summary",
    ],
}


SYSTEM_PROMPT = """You are a strict quality reviewer for LLM training tasks.
Score the provided prompt/response pair.
Use a 1-5 integer scale for each score:
1 = very poor
2 = poor
3 = acceptable
4 = strong
5 = excellent

Judge only these dimensions:
- grammar_score: grammar, spelling, punctuation, readability
- style_score: clarity, tone, structure, concision
- answer_score: whether the response actually answers the prompt well

Return only structured JSON matching the schema."""


class OpenAIResponsesLLMReviewer:
    def __init__(
        self,
        api_key: str,
        *,
        model: str = "gpt-4.1",
        endpoint: str = "https://api.openai.com/v1/responses",
        timeout_seconds: float = 30.0,
        pass_threshold: float = 3.5,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self.pass_threshold = pass_threshold

    def review_task(self, task: TaskRecord) -> ReviewResult:
        if not task.prompt.strip():
            raise NonRetryableProviderError("Prompt is empty")
        if not task.response.strip():
            raise NonRetryableProviderError("Response is empty")

        request_body = self._build_request_body(task)
        request = urllib.request.Request(
            url=self.endpoint,
            data=json.dumps(request_body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if exc.code in {408, 409, 429} or exc.code >= 500:
                raise RetryableProviderError(
                    f"OpenAI Responses API retryable failure {exc.code}: {detail}"
                ) from exc
            raise NonRetryableProviderError(
                f"OpenAI Responses API non-retryable failure {exc.code}: {detail}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RetryableProviderError(f"Network error calling OpenAI: {exc}") from exc
        except TimeoutError as exc:
            raise RetryableProviderError(f"Timeout calling OpenAI: {exc}") from exc
        except OSError as exc:
            raise RetryableProviderError(f"System error calling OpenAI: {exc}") from exc

        parsed = self._parse_review_payload(payload)
        grammar_score = int(parsed["grammar_score"])
        style_score = int(parsed["style_score"])
        answer_score = int(parsed["answer_score"])
        overall_score = round((grammar_score + style_score + answer_score) / 3, 2)
        passes_threshold = bool(parsed["passes_threshold"])

        return ReviewResult(
            task_id=task.task_id,
            overall_score=overall_score,
            grammar_score=grammar_score,
            style_score=style_score,
            answer_score=answer_score,
            passes_threshold=passes_threshold,
            issues=[str(value) for value in parsed["issues"]],
        )

    def _build_request_body(self, task: TaskRecord) -> dict:
        user_prompt = build_task_review_prompt(task)
        return {
            "model": self.model,
            "store": False,
            "temperature": 0,
            "input": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": SYSTEM_PROMPT,
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": user_prompt,
                        }
                    ],
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "task_quality_review",
                    "strict": True,
                    "schema": REVIEW_OUTPUT_SCHEMA,
                }
            },
        }

    def _parse_review_payload(self, payload: dict) -> dict:
        output_text = self._extract_output_text(payload)
        try:
            return json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise NonRetryableProviderError(
                f"OpenAI returned non-JSON structured output: {output_text}"
            ) from exc

    def _extract_output_text(self, payload: dict) -> str:
        parts: list[str] = []
        for item in payload.get("output", []):
            if item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    parts.append(content.get("text", ""))
        if not parts:
            raise NonRetryableProviderError("OpenAI response did not contain output text")
        return "".join(parts)


def build_task_review_prompt(task: TaskRecord) -> str:
    return (
        "Review this LLM training task.\n"
        f"customer: {task.customer}\n"
        f"project_id: {task.project_id}\n"
        f"category: {task.category}\n"
        f"prompt:\n{task.prompt}\n\n"
        f"response:\n{task.response}\n\n"
        "Evaluate the response for correctness, completeness, grammar, and style."
    )


def build_llm_reviewer(
    *,
    openai_api_key: str | None = None,
    model: str = "gpt-4.1",
    pass_threshold: float = 3.5,
) -> LLMReviewerPort:
    resolved_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
    if resolved_api_key:
        return OpenAIResponsesLLMReviewer(
            api_key=resolved_api_key,
            model=model,
            pass_threshold=pass_threshold,
        )
    return HeuristicLLMReviewer(pass_threshold=pass_threshold)
