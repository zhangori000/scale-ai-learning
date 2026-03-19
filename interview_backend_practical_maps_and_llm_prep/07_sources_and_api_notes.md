# Sources and API Notes

Last checked against official Google docs on 2026-03-14.

## Official links

- Places API overview
  - https://developers.google.com/maps/documentation/places/web-service/overview
- Text Search (New)
  - https://developers.google.com/maps/documentation/places/web-service/text-search
- Place types
  - https://developers.google.com/maps/documentation/places/web-service/place-types
- Routes API overview
  - https://developers.google.com/maps/documentation/routes
- Compute Route Matrix
  - https://developers.google.com/maps/documentation/routes/reference/rest/v2/TopLevel/computeRouteMatrix
- Optimize waypoint order
  - https://developers.google.com/maps/documentation/routes_preferred/waypoint_optimization_proxy_api

## Facts that matter for these interview questions

- Places Text Search (New) supports rectangular `locationRestriction`, which fits the restaurant bounding-box question.
- You should request only the fields you need via a field mask. Relevant fields include:
  - `places.id`
  - `places.displayName`
  - `places.location`
  - `places.rating`
  - `places.userRatingCount`
  - `places.priceLevel`
  - `places.primaryType`
  - `places.types`
- The place-types list includes cuisine-like types such as `mexican_restaurant`, `italian_restaurant`, and `japanese_restaurant`. That is the cleanest way to infer cuisine when there is no generic `cuisine` field.
- Places Text Search returns top-level `places` and `nextPageToken`, so a production adapter should translate that shape into your own domain objects instead of leaking Google JSON into service code.
- `priceLevel` in the Places API is represented as enum strings, so if the interview prompt wants `0..4`, the adapter should map those enum values into integers.
- Routes API `computeRouteMatrix` is the right primitive for pairwise travel-time calculation.
- If an interviewer asks for alternatives, Google also exposes waypoint optimization. It is useful to mention, but the contributor prompt explicitly asks for pairwise durations and then an optimization step.

## Practical interview implication

The strongest answer is not "I know Google Maps". It is:

1. know which endpoint gives place IDs
2. know which endpoint gives the duration matrix
3. know that cuisine needs inference from place types
4. know that large search regions need pagination and tiling
