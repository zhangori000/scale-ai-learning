# Multi-Head Attention + LLM Sampling Prep Pack

This folder teaches and implements:

1. Transformer multi-head scaled dot-product attention (forward pass)
2. Next-token sampling (temperature, top-k, top-p)

## Files

- `CONCEPTS.md` - conceptual explanations, complexity, masking semantics, edge cases
- `attention.py` - multi-head attention implementation (pure Python lists)
- `sampling.py` - sampling implementation with filtering + stable softmax
- `test_mha_sampling.py` - unit tests

## Run tests

```bash
python -m unittest test_mha_sampling.py -v
```

## Quick usage

```python
from attention import multi_head_attention_forward, identity_matrix
from sampling import sample_next_token

q = [[1.0, 2.0, 3.0, 4.0]]
k = [[1.0, 2.0, 3.0, 4.0]]
v = [[0.5, -1.0, 2.0, 1.5]]
w = identity_matrix(4)

out = multi_head_attention_forward(q, k, v, w, w, w, w, h=2)
token = sample_next_token([1.1, 0.2, 2.0], temperature=0.8, top_k=2, top_p=0.9, seed=7)
```

## Interview tips

For attention:

1. Mention mask application before softmax.
2. Mention stable softmax.
3. Mention fully-masked row behavior.
4. Give `O(L*d_model^2 + L^2*d_model)` complexity.

For sampling:

1. Explain temperature extremes.
2. Explain deterministic tie-break.
3. Explain explicit policy for top-k + top-p order.
4. Mention numerical stability and reproducibility via seed.
