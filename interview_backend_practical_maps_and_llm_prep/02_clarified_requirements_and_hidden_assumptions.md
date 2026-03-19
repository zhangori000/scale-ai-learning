# Clarified Requirements and Hidden Assumptions

The contributor prompt actually bundles three different backend practicals. In interview, I would explicitly separate them and state assumptions before designing anything.

## 1. Restaurant Search in a Rectangle

Assumptions I would say out loud:

- We are using Places API (New), not legacy search.
- "Top 20" means highest rating, with ties broken by `userRatingCount` and then name or place ID for stability.
- The rectangle is a hard restriction, not just a bias.
- We dedupe by Google place ID because the same restaurant can appear across pages or overlapping tiles.
- `priceLevel` may be missing. Average price should ignore missing values instead of treating them as zero.
- Cuisine is not a clean first-class field. The best production answer is to infer from `primaryType`, `types`, or fallback heuristics on display name.
- A single Places request is not enough for large areas because Text Search (New) paginates and caps total results.

## 2. LLM Task Quality Review Job

Assumptions I would say out loud:

- The webapp only creates a review job. It does not synchronously wait for up to 5000 external LLM calls.
- Mongo remains the source of truth for tasks.
- We need a separate job record and per-task result records so operators can inspect progress, failures, and retries.
- The external LLM can rate-limit, timeout, or partially fail, so retries must be per task, not all-or-nothing for the entire job.
- CSV generation and email happen after the job reaches a terminal state.
- Operators are filtering existing tasks, not uploading new task blobs in this flow.

## 3. Ski Trip Route Optimization

Assumptions I would say out loud:

- We only care about driving time between ski resorts and Joey's home.
- This is a round trip: start at home, visit each resort exactly once, return home.
- Places lookup uses the new Places API only.
- Travel times come from Routes API, ideally via a route matrix call rather than calling point-to-point directions repeatedly.
- For a small number of resorts, I would compute the exact optimal route with dynamic programming.
- For a large number of resorts, I would switch to a heuristic such as nearest neighbor plus 2-opt, or mention the built-in waypoint optimization feature as an alternative.

## Contributor Prompt Errors or Gaps Worth Fixing

- The prompt says "Google Maps Places API" in one section and "Places API (New APIs)" in another. I would standardize on Places API (New).
- The restaurant prompt asks for cuisine filtering, but the API does not hand you a neat generic `cuisine` property. You need an inference strategy.
- The restaurant prompt asks for the "top 20" inside a rectangle, but large rectangles can contain far more than 20 candidate places. That means pagination and possibly area tiling are part of the real answer.
- The LLM prompt implies a batch job but does not define job state or result storage. You should add those explicitly.
- The ski-trip prompt asks for pairwise drive times. That is basically a traveling salesperson problem once you have the matrix, so you should call out exact versus heuristic approaches.
