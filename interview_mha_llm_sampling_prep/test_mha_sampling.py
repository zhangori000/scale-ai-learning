from __future__ import annotations

import math
import unittest

from attention import identity_matrix, multi_head_attention_forward
from sampling import build_sampling_distribution, sample_next_token


class MultiHeadAttentionTest(unittest.TestCase):
    def test_l_equals_1_identity_projection(self) -> None:
        # With L=1 and identity projections, output should equal V.
        q = [[1.0, 2.0, 3.0, 4.0]]
        k = [[1.0, 2.0, 3.0, 4.0]]
        v = [[0.5, -1.0, 2.0, 1.5]]
        w = identity_matrix(4)
        out = multi_head_attention_forward(q, k, v, w, w, w, w, h=2)
        self.assertEqual(len(out), 1)
        self.assertEqual(len(out[0]), 4)
        for got, want in zip(out[0], v[0]):
            self.assertAlmostEqual(got, want, places=7)

    def test_fully_masked_row_becomes_zero(self) -> None:
        q = [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
        ]
        k = [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
        ]
        v = [
            [10.0, 0.0, 0.0, 0.0],
            [0.0, 20.0, 0.0, 0.0],
        ]
        w = identity_matrix(4)
        mask = [
            [1, 1],  # normal
            [0, 0],  # fully masked query row
        ]
        out, weights = multi_head_attention_forward(
            q, k, v, w, w, w, w, h=2, mask=mask, return_attention_weights=True
        )

        # Second output row should be all zeros by design choice.
        for x in out[1]:
            self.assertAlmostEqual(x, 0.0, places=8)
        # Check attention rows per head: row 1 sum is zero.
        for head in weights:
            self.assertAlmostEqual(sum(head[1]), 0.0, places=8)

    def test_masked_positions_have_zero_probability(self) -> None:
        q = [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
        ]
        k = [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
        ]
        v = [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
        ]
        w = identity_matrix(4)
        mask = [
            [1, 0],  # token 0 can only attend to token 0
            [1, 1],
        ]
        _, weights = multi_head_attention_forward(
            q, k, v, w, w, w, w, h=2, mask=mask, return_attention_weights=True
        )
        for head in weights:
            self.assertAlmostEqual(head[0][1], 0.0, places=8)
            self.assertAlmostEqual(sum(head[0]), 1.0, places=8)


class SamplingTest(unittest.TestCase):
    def test_temperature_near_zero_is_greedy(self) -> None:
        logits = [1.0, 3.0, 3.0, 2.5]
        # Tie between token 1 and 2 -> smallest index should win.
        token = sample_next_token(logits, temperature=1e-12, seed=7)
        self.assertEqual(token, 1)

    def test_top_k_filters_distribution(self) -> None:
        logits = [0.0, 10.0, 9.0, -5.0]
        probs, kept = build_sampling_distribution(logits, temperature=1.0, top_k=2)
        self.assertEqual(set(kept), {1, 2})
        self.assertAlmostEqual(probs[0], 0.0, places=10)
        self.assertAlmostEqual(probs[3], 0.0, places=10)
        self.assertAlmostEqual(sum(probs), 1.0, places=10)

    def test_top_p_keeps_small_nucleus(self) -> None:
        logits = [8.0, 7.0, 1.0, 0.0]
        probs, kept = build_sampling_distribution(logits, temperature=1.0, top_p=0.75)
        # Should keep a small highest-probability prefix.
        self.assertTrue(0 in kept)
        self.assertGreaterEqual(len(kept), 1)
        self.assertAlmostEqual(sum(probs), 1.0, places=10)
        for i in range(len(logits)):
            if i not in kept:
                self.assertAlmostEqual(probs[i], 0.0, places=10)

    def test_top_k_then_top_p_interaction(self) -> None:
        logits = [10.0, 9.0, 8.0, 7.0, 6.0]
        probs, kept = build_sampling_distribution(
            logits,
            temperature=1.0,
            top_k=3,
            top_p=0.80,
        )
        self.assertTrue(set(kept).issubset({0, 1, 2}))
        self.assertAlmostEqual(sum(probs), 1.0, places=10)

    def test_seeded_sampling_is_reproducible(self) -> None:
        logits = [1.0, 1.2, 0.9]
        t1 = sample_next_token(logits, temperature=1.0, top_k=3, seed=42)
        t2 = sample_next_token(logits, temperature=1.0, top_k=3, seed=42)
        self.assertEqual(t1, t2)


if __name__ == "__main__":
    unittest.main()
