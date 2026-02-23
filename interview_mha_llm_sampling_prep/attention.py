from __future__ import annotations

import math
from typing import Any

Matrix = list[list[float]]
Tensor3D = list[list[list[float]]]  # (h, L, d_head)


def _validate_rectangular(matrix: Matrix, name: str) -> tuple[int, int]:
    if not matrix:
        raise ValueError(f"{name} cannot be empty")
    cols = len(matrix[0])
    if cols == 0:
        raise ValueError(f"{name} has zero columns")
    for row in matrix:
        if len(row) != cols:
            raise ValueError(f"{name} must be rectangular")
    return len(matrix), cols


def _matmul(a: Matrix, b: Matrix) -> Matrix:
    m, n = _validate_rectangular(a, "matmul_left")
    bn, p = _validate_rectangular(b, "matmul_right")
    if n != bn:
        raise ValueError(f"shape mismatch for matmul: ({m},{n}) x ({bn},{p})")

    out: Matrix = [[0.0 for _ in range(p)] for _ in range(m)]
    for i in range(m):
        for k in range(n):
            aik = a[i][k]
            if aik == 0.0:
                continue
            for j in range(p):
                out[i][j] += aik * b[k][j]
    return out


def _transpose(a: Matrix) -> Matrix:
    m, n = _validate_rectangular(a, "transpose_input")
    return [[a[i][j] for i in range(m)] for j in range(n)]


def _softmax_stable(values: list[float]) -> list[float]:
    if not values:
        return []
    max_v = max(values)
    exps = [math.exp(v - max_v) for v in values]
    denom = sum(exps)
    if denom == 0.0:
        # Should not happen in normal settings; safe fallback.
        return [1.0 / len(values) for _ in values]
    return [x / denom for x in exps]


def _split_heads(x: Matrix, h: int) -> Tensor3D:
    l, d_model = _validate_rectangular(x, "split_heads_input")
    if d_model % h != 0:
        raise ValueError(f"d_model={d_model} must be divisible by h={h}")
    d_head = d_model // h

    out: Tensor3D = [[[0.0 for _ in range(d_head)] for _ in range(l)] for _ in range(h)]
    for i in range(l):
        row = x[i]
        for head in range(h):
            start = head * d_head
            out[head][i] = row[start : start + d_head]
    return out


def _combine_heads(heads: Tensor3D) -> Matrix:
    if not heads:
        raise ValueError("heads cannot be empty")
    h = len(heads)
    l = len(heads[0])
    if l == 0:
        raise ValueError("heads sequence length cannot be zero")
    d_head = len(heads[0][0])
    d_model = h * d_head

    out: Matrix = [[0.0 for _ in range(d_model)] for _ in range(l)]
    for head in range(h):
        for i in range(l):
            start = head * d_head
            out[i][start : start + d_head] = heads[head][i]
    return out


def _validate_mask(mask: Matrix | None, l: int) -> None:
    if mask is None:
        return
    ml, mk = _validate_rectangular(mask, "mask")
    if ml != l or mk != l:
        raise ValueError(f"mask must have shape ({l},{l}), got ({ml},{mk})")
    for row in mask:
        for v in row:
            if v not in (0, 1):
                raise ValueError("mask values must be 0 or 1")


def multi_head_attention_forward(
    q: Matrix,
    k: Matrix,
    v: Matrix,
    wq: Matrix,
    wk: Matrix,
    wv: Matrix,
    wo: Matrix,
    h: int,
    mask: Matrix | None = None,
    mask_fill_value: float = -1e30,
    return_attention_weights: bool = False,
) -> Matrix | tuple[Matrix, Tensor3D]:
    """
    Multi-head scaled dot-product attention (forward pass).

    Shapes:
    - q,k,v: (L, d_model)
    - wq,wk,wv,wo: (d_model, d_model)
    - mask: (L, L), where 1 means allowed and 0 means disallowed
    - output: (L, d_model)
    """
    lq, d_model = _validate_rectangular(q, "Q")
    lk, dk = _validate_rectangular(k, "K")
    lv, dv = _validate_rectangular(v, "V")
    if lq != lk or lk != lv:
        raise ValueError("Q, K, V must share same sequence length L in this implementation")
    if dk != d_model or dv != d_model:
        raise ValueError("Q, K, V must share same d_model")
    if h <= 0:
        raise ValueError("h must be > 0")
    if d_model % h != 0:
        raise ValueError(f"d_model={d_model} must be divisible by h={h}")
    _validate_mask(mask, lq)

    # 1) Linear projections
    qp = _matmul(q, wq)
    kp = _matmul(k, wk)
    vp = _matmul(v, wv)

    # 2) Split into heads: (h, L, d_head)
    qh = _split_heads(qp, h)
    kh = _split_heads(kp, h)
    vh = _split_heads(vp, h)

    d_head = d_model // h
    scale = 1.0 / math.sqrt(float(d_head))

    all_head_outputs: Tensor3D = []
    all_head_weights: Tensor3D = []

    for head in range(h):
        q_head = qh[head]  # (L, d_head)
        k_head = kh[head]  # (L, d_head)
        v_head = vh[head]  # (L, d_head)

        # scores: (L, L) = q_head @ k_head^T / sqrt(d_head)
        scores = _matmul(q_head, _transpose(k_head))
        for i in range(lq):
            for j in range(lq):
                scores[i][j] *= scale

        weights: Matrix = [[0.0 for _ in range(lq)] for _ in range(lq)]
        for i in range(lq):
            if mask is not None and all(mask[i][j] == 0 for j in range(lq)):
                # Edge case: fully masked query row -> define zero weights.
                continue

            masked_scores = []
            for j in range(lq):
                if mask is not None and mask[i][j] == 0:
                    masked_scores.append(mask_fill_value)
                else:
                    masked_scores.append(scores[i][j])

            row_probs = _softmax_stable(masked_scores)
            # Enforce exact zero on masked positions.
            if mask is not None:
                for j in range(lq):
                    if mask[i][j] == 0:
                        row_probs[j] = 0.0
                row_sum = sum(row_probs)
                if row_sum > 0:
                    row_probs = [x / row_sum for x in row_probs]
            weights[i] = row_probs

        # head_out: (L, d_head)
        head_out = _matmul(weights, v_head)
        all_head_outputs.append(head_out)
        all_head_weights.append(weights)

    # 3) Concatenate + output projection
    concatenated = _combine_heads(all_head_outputs)  # (L, d_model)
    output = _matmul(concatenated, wo)  # (L, d_model)

    if return_attention_weights:
        return output, all_head_weights
    return output


def identity_matrix(n: int) -> Matrix:
    if n <= 0:
        raise ValueError("n must be > 0")
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]


__all__ = ["multi_head_attention_forward", "identity_matrix"]
