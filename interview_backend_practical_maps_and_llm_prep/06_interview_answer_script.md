# Interview Answer Script

## 1. Restaurants in a Rectangle

I would wrap Google Places behind a `PlacesSearchPort` and put the orchestration in a `RestaurantService`. The service would search within a rectangular `locationRestriction`, page through results, dedupe by place ID, infer cuisine from `primaryType` or `types`, then sort by rating and rating count before returning the top 20. For large rectangles, I would tile the area and expose pagination instead of assuming one request can cover everything.

## 2. LLM Batch Review Job

I would model this as an async batch job. The API validates that the operator selected at most 5000 tasks, writes a job record, and returns immediately. Workers then fetch the task blobs from Mongo, review them through a rate-limited LLM adapter with per-task retries, persist partial progress, and after completion generate a CSV and send the operator an email link. The main backend concerns are idempotency, retries, progress tracking, and partial failure handling.

## 3. Ski Trip Route Optimization

I would first resolve home and resort names into place IDs using Places API (New). Then I would call Routes API `computeRouteMatrix` to build all pairwise drive times. Once I have the matrix, I would solve the round-trip optimization as a traveling salesperson problem: exact dynamic programming for small numbers of resorts, heuristic optimization for larger trip plans.

## Follow-up one-liners

- Rate limits: bounded concurrency, pooled clients, exponential backoff with jitter, and caching.
- Missing cuisine field: infer from `primaryType`, `types`, and only then lightweight heuristics on the name.
- Large areas: tile the map, paginate within each tile, and dedupe by place ID.
- Provider instability: classify retryable versus non-retryable failures and persist per-item progress.
- Large route sets: switch from exact DP to a heuristic or platform waypoint optimization.
