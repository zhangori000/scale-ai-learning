# Production Notes

This file is the concrete follow-up answer for "how would you implement this in production?"

## 1. Geography hierarchy

- `Town` is the parent geographic region.
- `Neighborhood` is the child geographic region.
- A town contains many neighborhoods.
- A party belongs to exactly one neighborhood.
- A party's town is derived from its neighborhood.

In the interview JSON, the geo row repeats both `neighborhood` and `town` for the same `party_id`. That is denormalized transport data. In a production data model, the stable relationship should be:

`parties.neighborhood_id -> neighborhoods.id -> neighborhoods.town_id -> towns.id`

That matters because it avoids ambiguity when two towns have a neighborhood with the same display name.

## 2. Concrete daily batch flow

Recommended shape:

1. Extract all parties for a service day.
2. Join parties to neighborhoods and towns.
3. Aggregate earliest start / latest end per neighborhood.
4. Persist those neighborhood windows into a daily stats table.
5. Load the neighborhood windows grouped by town.
6. Merge town intervals in application code.
7. Persist dead-zone hours into a town daily stats table.
8. Serve API reads from the precomputed stats tables.

## 3. Suggested schedules

Two schedules work well together:

- Near-real-time refresh: every 5 or 15 minutes for `today`, so dashboards stay fresh.
- Final reconciliation: nightly for `yesterday`, so late-arriving data or corrections are folded in.

Both runs should be idempotent. The batch job in `batch_job.py` models this by overwriting the same day's stats via upsert behavior.

## 4. Concrete SQL split

The neighborhood step is easy to push into SQL:

```sql
SELECT
  neighborhood_id,
  MIN(EXTRACT(HOUR FROM start_time AT TIME ZONE 'UTC')) AS window_start_hour,
  MAX(EXTRACT(HOUR FROM end_time AT TIME ZONE 'UTC')) AS window_end_hour,
  COUNT(*) AS party_count
FROM parties
WHERE start_time >= :day_start
  AND start_time < :day_end
GROUP BY neighborhood_id;
```

The town dead-zone step is easier to keep in application code, because interval merging is more readable and less error-prone there.

## 5. API read path

A practical endpoint is:

`GET /v1/towns/{town_id}/stats/daily?date=2024-01-01`

Response shape:

```json
{
  "town_id": 42,
  "date": "2024-01-01",
  "deadzone_hours": 4,
  "merged_intervals": [[10, 13], [17, 20]],
  "first_party_hour": 10,
  "last_party_hour": 20
}
```

That endpoint should read from `town_stats_daily`, not recompute from raw parties at request time.

## 6. Operational concerns

- Validation: reject rows with `end_time < start_time`.
- Cross-day parties: split them into per-day slices before daily aggregation.
- Idempotency: key stats by `(service_day, neighborhood_id)` and `(service_day, town_id)`.
- Late data: rerun the job for the affected day instead of trying to patch rows by hand.
- Observability: record rows read, rows skipped, parties per town, and job duration.

## 7. What to say in the interview

Short version:

"I would normalize parties onto neighborhoods, because neighborhood is the leaf geography and town is the parent. Then I would precompute neighborhood windows and town dead zones in a batch job, store them in daily stats tables with upserts, and have the API read from those precomputed tables so request latency stays low and the logic is deterministic."
