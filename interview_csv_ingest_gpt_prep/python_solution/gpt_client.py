from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol


class ClassificationClient(Protocol):
    def classify_batch(self, inputs: list[str], labels: list[str]) -> list[str]:
        """Return one label per input (same order)."""
        ...


@dataclass
class HTTPClassificationClient:
    endpoint: str
    model: str = "gpt-classifier-001"
    timeout_s: float = 10.0
    max_retries: int = 2
    backoff_base_s: float = 0.25
    api_key: str | None = None

    def classify_batch(self, inputs: list[str], labels: list[str]) -> list[str]:
        body = {
            "model": self.model,
            "examples": labels,
            "inputs": inputs,
        }
        payload = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint,
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                **({"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}),
            },
        )

        last_err: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                    resp_body = resp.read().decode("utf-8")
                parsed = json.loads(resp_body)
                labels_out = parsed.get("labels")
                if not isinstance(labels_out, list) or len(labels_out) != len(inputs):
                    raise ValueError("invalid GPT response payload: labels length mismatch")
                return [str(x) for x in labels_out]
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
                last_err = exc
                if attempt == self.max_retries:
                    break
                time.sleep(self.backoff_base_s * (2**attempt))
        raise RuntimeError(f"classification request failed after retries: {last_err}")


@dataclass
class MockKeywordClassificationClient:
    """Deterministic classifier for local testing/interview prep."""

    def classify_batch(self, inputs: list[str], labels: list[str]) -> list[str]:
        output: list[str] = []
        labels_set = {x.lower() for x in labels}
        for text in inputs:
            t = text.lower()
            if "bug" in t or "fix" in t or "error" in t:
                candidate = "bug"
            elif "doc" in t or "readme" in t:
                candidate = "documentation"
            else:
                candidate = "feature"

            if candidate not in labels_set:
                candidate = labels[0] if labels else "unknown"
            output.append(candidate)
        return output
