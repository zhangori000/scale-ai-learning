from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

# Simulated persistent side-effect store.
MESSAGE_STORE: dict[str, list[dict[str, Any]]] = defaultdict(list)


def create_message(task_id: str, author: str, content: str) -> dict[str, Any]:
    message = {"task_id": task_id, "author": author, "content": content}
    MESSAGE_STORE[task_id].append(message)
    return message


def fetch_briefing(source: str, symbols: list[str]) -> str:
    source_lower = source.lower()
    if source_lower == "coinbase":
        return f"{source} market briefing: {', '.join(symbols)} showed strong upward momentum this hour."
    return f"{source} editorial briefing: {', '.join(symbols)} saw mixed outlook with cautious analyst commentary."


def analyze_sentiment(text: str) -> str:
    lower = text.lower()
    positive_markers = ["upward", "bull", "strong", "rally", "growth"]
    negative_markers = ["downward", "bear", "weak", "drop", "cautious", "risk"]
    score = 0
    for marker in positive_markers:
        if marker in lower:
            score += 1
    for marker in negative_markers:
        if marker in lower:
            score -= 1

    if score > 0:
        return "positive"
    if score < 0:
        return "negative"
    return "neutral"


def get_all_activities() -> dict[str, Callable[..., Any]]:
    return {
        "create_message": create_message,
        "fetch_briefing": fetch_briefing,
        "analyze_sentiment": analyze_sentiment,
    }
