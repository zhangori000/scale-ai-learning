# Party Times Interview Question

This folder turns the prompt into a small, production-oriented interview prep package.

## Files

- `domain_models.py` - typed domain models and timestamp parsing
- `party_analytics.py` - the exact interview functions plus cleaner internal helpers
- `repositories.py` - repository interfaces and in-memory implementations
- `batch_job.py` - scheduled-job style orchestration for daily stats
- `demo.py` - end-to-end example using both the prompt API and the batch job
- `test_party_analytics.py` - unit tests for the core logic and batch flow
- `PRODUCTION_NOTES.md` - concrete follow-up notes for hierarchy, batch jobs, and serving
- `schema.sql` - a realistic relational schema for a production version

## Neighborhood vs Town

- A `neighborhood` is the smaller geographic unit where an individual party happens.
- A `town` is the parent region that contains one or more neighborhoods.
- In a normalized production model, a party belongs to a `neighborhood_id`, and the town is derived from `neighborhoods -> towns`.
- The interview JSON is denormalized, so each geo record repeats both the neighborhood and the town for the same `party_id`.

That distinction matters because:

- Part 1 aggregates parties into one window per neighborhood.
- Part 2 takes those neighborhood windows, groups them by town, merges them, and computes dead-zone gaps between merged blocks.

## Quick Start

From this folder:

```bash
python -m unittest test_party_analytics.py -v
python demo.py
```

## Interview Mapping

- Use `compute_party_windows(...)` in `party_analytics.py` for the exact Part 1 prompt shape.
- Use `compute_deadzones(...)` in `party_analytics.py` for the exact Part 2 prompt shape.
- Use `PartyAnalyticsBatchJob` in `batch_job.py` when the interviewer asks how you would run this in production.
