from __future__ import annotations

import math
import random
from typing import Iterable


def _argmax_tiebreak_smallest_index(values: list[float]) -> int:
    best_idx = 0
    best_val = values[0]
    for i, v in enumerate(values[1:], start=1):
        if v > best_val:
            best_val = v
            best_idx = i
    return best_idx


def _softmax_over_indices(logits: list[float], indices: list[int]) -> dict[int, float]:
    # Stable softmax on subset.
    max_logit = max(logits[i] for i in indices)
    exps = {i: math.exp(logits[i] - max_logit) for i in indices}
    denom = sum(exps.values())
    if denom == 0.0:
        p = 1.0 / len(indices)
        return {i: p for i in indices}
    return {i: exps[i] / denom for i in indices}


def _sorted_indices_desc(logits: list[float], indices: Iterable[int]) -> list[int]:
    # Desc by logit, tie-break by smaller token id for deterministic behavior.
    return sorted(indices, key=lambda i: (-logits[i], i))


def build_sampling_distribution(
    logits: list[float],
    temperature: float = 1.0,
    top_k: int | None = None,
    top_p: float | None = None,
) -> tuple[list[float], list[int]]:
    """
    Returns:
    - probs: length V, filtered probs with zeros for removed tokens
    - kept_indices: token ids kept after filtering
    """
    if not logits:
        raise ValueError("logits cannot be empty")
    if temperature <= 0:
        raise ValueError("temperature must be > 0")
    if top_k is not None and top_k <= 0:
        raise ValueError("top_k must be > 0 when provided")
    if top_p is not None and not (0.0 < top_p <= 1.0):
        raise ValueError("top_p must satisfy 0 < top_p <= 1")

    v = len(logits)
    scaled = [x / temperature for x in logits]
    candidate = set(range(v))

    # Apply top-k first.
    if top_k is not None:
        k = min(top_k, v)
        ordered = _sorted_indices_desc(scaled, range(v))
        candidate = set(ordered[:k])

    # Apply top-p over current candidate set.
    if top_p is not None:
        ordered = _sorted_indices_desc(scaled, candidate)
        probs_subset = _softmax_over_indices(scaled, ordered)
        running = 0.0
        nucleus: list[int] = []
        for token_id in ordered:
            nucleus.append(token_id)
            running += probs_subset[token_id]
            if running >= top_p:
                break
        candidate = set(nucleus)

    if not candidate:
        # Defensive fallback.
        idx = _argmax_tiebreak_smallest_index(scaled)
        probs = [0.0 for _ in range(v)]
        probs[idx] = 1.0
        return probs, [idx]

    probs_subset = _softmax_over_indices(scaled, list(candidate))
    probs = [0.0 for _ in range(v)]
    for idx, p in probs_subset.items():
        probs[idx] = p
    return probs, _sorted_indices_desc(scaled, candidate)


def sample_next_token(
    logits: list[float],
    temperature: float = 1.0,
    top_k: int | None = None,
    top_p: float | None = None,
    seed: int | None = None,
) -> int:
    """
    Sample one token id from next-token logits.

    Behavior:
    - If temperature is near zero, returns greedy argmax with deterministic tie-break.
    - Supports top-k and top-p filtering.
    """
    if not logits:
        raise ValueError("logits cannot be empty")
    if temperature <= 0:
        raise ValueError("temperature must be > 0")

    # temperature -> 0 behavior: deterministic greedy.
    if temperature <= 1e-8:
        return _argmax_tiebreak_smallest_index(logits)

    probs, _ = build_sampling_distribution(
        logits=logits,
        temperature=temperature,
        top_k=top_k,
        top_p=top_p,
    )

    rng = random.Random(seed)
    r = rng.random()
    acc = 0.0
    for token_id, p in enumerate(probs):
        acc += p
        if r <= acc:
            return token_id
    # Floating-point tail fallback.
    return _argmax_tiebreak_smallest_index(probs)


__all__ = ["sample_next_token", "build_sampling_distribution"]
