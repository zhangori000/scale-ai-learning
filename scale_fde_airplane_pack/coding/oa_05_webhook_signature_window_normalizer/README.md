# OA-05: Webhook Signature Window Normalizer

This coding problem is inferred from: scale-agentex/agentex/docs/docs/development_guides/webhooks.md.

You receive webhook envelopes with: provider. headers. raw_body. received_at.

Implement normalization and validation that: verifies provider signature. checks replay window tolerance. dedupes by provider event identity. emits accepted and rejected records with reason codes.

## Algorithmic Foundations For This Problem

Restate input and output contract in deterministic terms. Define tie-breakers explicitly. Define malformed-input behavior explicitly.

Write invariants before coding. Invariants reduce logical bugs. Examples include deterministic ordering and no duplicate contribution.

Choose data structures based on semantics. Use map for dedupe and latest-by-key patterns. Use heap for progressive ordering extraction. Use stack for nested grammar. Use deque for sliding windows.

Separate transformation phase from aggregation phase when semantics differ. Dry-run tiny examples before implementation. Then scale to stress tests.

Complexity should be explained phase-by-phase. Prefer clarity first, then optimize if bottlenecks are measured.

