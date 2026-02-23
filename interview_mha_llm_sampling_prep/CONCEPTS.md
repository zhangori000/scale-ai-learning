# Concepts: Multi-Head Attention + LLM Sampling

This note explains the core ideas behind the code in this folder.

## Task A: Multi-head scaled dot-product attention

Given:

- `Q, K, V` of shape `(L, d_model)`
- `h` heads, `d_head = d_model / h`
- projections `Wq, Wk, Wv, Wo` each `(d_model, d_model)`
- optional mask `(L, L)` where `1=allowed`, `0=disallowed`

Computation:

1. `Q' = QWq`, `K' = KWk`, `V' = VWv`
2. reshape each to `(h, L, d_head)`
3. per head:
   - `scores = (Qh @ Kh^T) / sqrt(d_head)` -> `(L, L)`
   - apply mask: disallowed positions get very negative value (e.g. `-1e30`)
   - `weights = softmax(scores)` over last dimension
   - `head_out = weights @ Vh` -> `(L, d_head)`
4. concatenate all heads back to `(L, d_model)`
5. output projection with `Wo`

## Mask numerical handling

In practice:

- set masked logits to `-inf` (or `-1e30`) before softmax.
- this drives their probability to ~0 after softmax.

Important edge case:

- If a whole query row is masked (no valid keys), softmax is undefined.
- This implementation defines that row's attention weights as all zeros (and output row becomes zeros).

## Softmax numerical stability

Stable softmax:

1. subtract max logit from each logit
2. exponentiate shifted values
3. normalize by sum

This avoids overflow when logits are large.

## Complexity

Let `d_head = d_model / h`.

Main terms:

1. Projections (`QWq`, `KWk`, `VWv`, output projection):
   - each `O(L * d_model^2)`
   - total projection cost `O(L * d_model^2)`
2. Attention scores per head:
   - `Qh @ Kh^T`: `O(L^2 * d_head)`
   - times `h` heads => `O(L^2 * d_model)`
3. Weighted sum (`weights @ Vh`) across heads:
   - also `O(L^2 * d_model)`

Total:

- `O(L * d_model^2 + L^2 * d_model)`

Space (activations):

- scores/weights per head `O(L^2)`
- across heads `O(h * L^2)` plus projection/outputs `O(L * d_model)`

## Edge cases to discuss

1. `L = 1`
   - attention weight is `[1]` (if unmasked)
2. Fully masked query row
   - row output defined as zeros
3. `d_model % h != 0`
   - invalid configuration

---

## Task B: next-token sampling from logits

Given logits vector of size `V`, and parameters:

- `temperature > 0`
- optional `top_k`
- optional `top_p` (`0 < p <= 1`)
- optional random seed

Steps:

1. Scale logits by temperature: `scaled = logits / temperature`
2. Apply filtering:
   - `top_k`: keep only highest `k` logits
   - `top_p` (nucleus): sort by probability descending and keep smallest prefix with cumulative prob >= `p`
3. Softmax over kept logits only
4. Sample from resulting categorical distribution

## Temperature behavior

- `temperature -> 0`: distribution becomes very peaky -> greedy-like
- For exact/near-zero, many systems switch to deterministic argmax
- High temperature makes distribution flatter (more diverse, less deterministic)

## Ties in logits

To keep behavior deterministic in edge cases:

- break ties by smallest token index (or documented rule)

## Both top_k and top_p provided

Common deterministic policy:

1. apply `top_k` first
2. apply `top_p` within that reduced set

Document this explicitly so behavior is predictable.

## Sampling complexity

For vocabulary size `V`:

- sorting for filtering: `O(V log V)`
- softmax + sampling: `O(V)`

If you optimize with partial sort for top-k, can reduce practical cost.
