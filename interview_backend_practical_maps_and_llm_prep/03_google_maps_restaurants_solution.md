# Google Maps Restaurants Solution

## Clean problem statement

Build a backend function that:

1. Searches for restaurants inside a rectangular bounding box
2. Returns the top 20 restaurants sorted by rating
3. Optionally filters to requested cuisines
4. Computes count and average price level per cuisine
5. Scales to larger areas via pagination and tiling

## Best API shape

```python
fetch_top_restaurants(
    bounds=((sw_lat, sw_lng), (ne_lat, ne_lng)),
    cuisine_types=["Mexican", "Italian", "Japanese"],
    limit=20,
)
```

## Practical API design

Use Places API Text Search (New) with:

- `textQuery = "restaurant"`
- `includedType = "restaurant"`
- `strictTypeFiltering = true`
- `locationRestriction.rectangle.low/high`
- a field mask containing only what you need:
  - `places.id`
  - `places.displayName`
  - `places.location`
  - `places.rating`
  - `places.userRatingCount`
  - `places.priceLevel`
  - `places.primaryType`
  - `places.types`

## Service design

Agentex-style decomposition:

- `PlacesSearchPort`
  - hides Google HTTP details
- `GooglePlacesSearchClient`
  - translates the real Places API JSON into domain objects
- `RestaurantService`
  - paginates, dedupes, sorts, filters, summarizes
- `CuisineInference`
  - maps Google place types to higher-level cuisines

## Adapter boundary

This is the important architectural point:

- Google returns top-level `places`
- each place is a nested JSON object
- the service does not work directly on that raw shape

Instead, the adapter converts Google's response into:

- `RestaurantSearchPage`
- `RestaurantRecord`

That is why `RestaurantService` can stay clean. The adapter is where you flatten:

- `displayName.text` into `name`
- `location.latitude` and `location.longitude` into `lat` and `lng`
- `priceLevel` enum strings into the prompt's numeric `0..4` scale
- `nextPageToken` into `next_page_token`

## Core flow

1. Normalize the rectangle into southwest and northeast corners.
2. If the area is large, split it into smaller tiles.
3. For each tile, page through Places results.
4. Deduplicate by `place_id`.
5. Infer cuisine from `primaryType` or `types`.
6. Apply requested cuisine filter if present.
7. Sort by:
   - rating descending
   - user rating count descending
   - stable ID or name ascending
8. Keep the top 20.
9. For each requested cuisine, compute:
   - `count`
   - `avg_price_level` over only records where price is present

## Cuisine inference

Best production strategy:

1. First check fine-grained types such as:
   - `mexican_restaurant`
   - `italian_restaurant`
   - `japanese_restaurant`
2. Then check all returned `types`
3. Then fallback to simple name heuristics if business requirements demand it
4. If still unknown, classify as `Unknown` instead of guessing

## Rate limit answer

If asked how to handle rate limits:

- Reuse a pooled HTTP client
- Respect page tokens instead of refetching the first page
- Bound concurrency per API key
- Cache tile results for repeated queries
- Use exponential backoff with jitter on 429 and transient 5xx
- Push large-area scans to an async job if they exceed normal latency budgets

## Pagination answer

Text Search (New) can paginate, but it also caps total results across pages. So for a dense city rectangle:

1. Page within each tile
2. Stop early when you already have enough high-quality candidates
3. Tile the rectangle if it is too large or too dense
4. Return a next cursor that contains:
   - tile index
   - Google page token
   - dedupe state or enough information to resume safely

## Edge cases

- Empty result set
- Missing `priceLevel`
- Duplicate restaurants across tile boundaries
- One restaurant matching multiple cuisine buckets
- Bounding box crossing the 180-degree longitude line
- Unstable ranking across repeated searches

## What I would say in interview

The simple version is a `RestaurantService` on top of a `PlacesSearchPort`. The service pages through Text Search (New) restricted by a rectangle, dedupes by place ID, infers cuisine from place types, sorts by rating and rating count, and returns the top 20 plus per-cuisine price summaries. For larger areas, I would tile the rectangle and expose pagination rather than pretending one request is enough.
