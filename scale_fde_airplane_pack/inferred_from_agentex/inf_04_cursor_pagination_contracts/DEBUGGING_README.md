# INF-04 Debugging Editorial: Cursor Pagination Contracts and Validation

This chapter is a detailed debugging guide for cursor pagination failures.

## 1. Symptom Profile

Users report:

- duplicate rows between pages
- missing rows while scrolling
- pagination jumps after refresh

These are usually not frontend rendering bugs. They are contract bugs between cursor encoding, sort order, and boundary predicates.

## 2. Ground Truth Method

Start by extracting full canonical ordered result set without pagination limits. This becomes your truth sequence.

Then replay paginated requests exactly and compare concatenated IDs to truth sequence.

Without this baseline, debugging stays anecdotal.

## 3. Contract Components To Audit

1. deterministic sort order and tie-breaker
2. cursor payload fields
3. cursor decode/validation behavior
4. boundary predicate for older/newer traversal
5. stale-cursor handling behavior

Any mismatch creates instability.

## 4. Common Bug Classes

- timestamp-only ordering without unique tie-breaker
- malformed cursor silently ignored
- predicate sign inversion on tie-break field
- stale anchor fallback to first page without explicit signal

## 5. Reproduction Plan

1. seed data with equal timestamps to stress tie-breaking
2. fetch page 1 and page 2
3. check overlap and gaps
4. delete anchor row and retry with cursor
5. send malformed cursor

This sequence covers most real failures quickly.

## 6. Patch Guidelines

- enforce composite order (for example created_at + id)
- enforce strict cursor decode validation (`400 invalid_cursor`)
- align older/newer predicates exactly with chosen ordering
- define explicit stale-anchor policy

## 7. Post-Patch Invariants

1. no overlap between consecutive pages
2. no missing rows across full traversal
3. equal-timestamp rows remain deterministic
4. invalid cursor never silently resets traversal

## 8. Observability

Instrument:

- invalid_cursor_total
- stale_cursor_total
- pagination_overlap_detected (test/probe metric)

Add request logs with cursor hash/version for traceability.

## 9. Interview Delivery Paragraph

"I debugged pagination by treating it as a contract system, not a query fragment. After establishing canonical ordering, I replayed cursor traversal and found boundary mismatch under tie conditions. I fixed ordering and predicate alignment, added strict cursor validation, and verified no-overlap/no-gap invariants end to end."

## 10. Closing Thought

Cursor bugs persist when teams optimize query snippets without owning the full contract. The durable fix is contract coherence across encoding, decoding, ordering, and predicate logic.
