from __future__ import annotations

import json
import urllib.request
from typing import Protocol


class ClassificationClient(Protocol):
    def classify_record(self, record: dict, label_options: list[str]) -> tuple[str, str]:
        raise NotImplementedError


class MockKeywordClassificationClient:
    def classify_record(
        self,
        record: dict,
        label_options: list[str],
    ) -> tuple[str, str]:
        prompt = build_classification_prompt(record, label_options)
        lowered_record = json.dumps(record, sort_keys=True).lower()
        lowered_options = [option.lower() for option in label_options]

        for option, lowered_option in zip(label_options, lowered_options):
            if lowered_option in lowered_record:
                return option, prompt

        if "task" in record and "task" in lowered_options:
            return label_options[lowered_options.index("task")], prompt
        if "name" in record and "user" in lowered_options:
            return label_options[lowered_options.index("user")], prompt

        return label_options[0], prompt


class HTTPClassificationClient:
    def __init__(
        self,
        endpoint: str,
        api_key: str | None = None,
        timeout_seconds: float = 20.0,
    ) -> None:
        self.endpoint = endpoint
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def classify_record(
        self,
        record: dict,
        label_options: list[str],
    ) -> tuple[str, str]:
        prompt = build_classification_prompt(record, label_options)
        payload = {
            "prompt": prompt,
            "label_options": label_options,
        }
        request = urllib.request.Request(
            url=self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                **(
                    {"Authorization": f"Bearer {self.api_key}"}
                    if self.api_key
                    else {}
                ),
            },
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            body = response.read().decode("utf-8")

        parsed = json.loads(body)
        if "label" not in parsed:
            raise ValueError("Classifier response must contain a 'label' field")
        return str(parsed["label"]), prompt


def build_classification_prompt(record: dict, label_options: list[str]) -> str:
    options = ", ".join(label_options)
    payload = json.dumps(record, ensure_ascii=True, sort_keys=True)
    return (
        "You are classifying one JSON record.\n"
        f"Choose exactly one label from: {options}.\n"
        "Return only the label.\n"
        f"Record:\n{payload}"
    )
