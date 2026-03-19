from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from fake_adapters import HeuristicLLMReviewer
from models import TaskRecord
from openai_review_client import OpenAIResponsesLLMReviewer, build_llm_reviewer


class _FakeHTTPResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class OpenAIResponsesLLMReviewerTest(unittest.TestCase):
    def test_review_task_uses_responses_api_and_parses_structured_output(self) -> None:
        task = TaskRecord(
            task_id="t1",
            customer="acme",
            project_id="p1",
            category="general",
            prompt="How do I reset my password?",
            response="You can reset your password from the account settings page.",
        )
        captured = {}

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            captured["method"] = request.get_method()
            captured["timeout"] = timeout
            captured["headers"] = dict(request.header_items())
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return _FakeHTTPResponse(
                {
                    "output": [
                        {
                            "type": "message",
                            "status": "completed",
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": json.dumps(
                                        {
                                            "grammar_score": 5,
                                            "style_score": 4,
                                            "answer_score": 5,
                                            "passes_threshold": True,
                                            "issues": [],
                                            "summary": "Strong answer.",
                                        }
                                    ),
                                }
                            ],
                        }
                    ]
                }
            )

        reviewer = OpenAIResponsesLLMReviewer(api_key="test-key")

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            result = reviewer.review_task(task)

        self.assertEqual(captured["url"], "https://api.openai.com/v1/responses")
        self.assertEqual(captured["method"], "POST")
        self.assertEqual(captured["timeout"], 30.0)
        self.assertEqual(captured["headers"]["Authorization"], "Bearer test-key")
        self.assertEqual(captured["body"]["model"], "gpt-4.1")
        self.assertFalse(captured["body"]["store"])
        self.assertEqual(captured["body"]["temperature"], 0)
        self.assertEqual(
            captured["body"]["text"]["format"]["type"],
            "json_schema",
        )
        self.assertTrue(captured["body"]["text"]["format"]["strict"])
        self.assertEqual(result.task_id, "t1")
        self.assertEqual(result.grammar_score, 5)
        self.assertEqual(result.style_score, 4)
        self.assertEqual(result.answer_score, 5)
        self.assertEqual(result.overall_score, 4.67)
        self.assertTrue(result.passes_threshold)

    def test_build_llm_reviewer_falls_back_without_api_key(self) -> None:
        reviewer = build_llm_reviewer(openai_api_key=None)
        self.assertIsInstance(reviewer, HeuristicLLMReviewer)


if __name__ == "__main__":
    unittest.main()
