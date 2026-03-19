# Real Google Ski Trip Clients

If you want to see the concrete non-mock implementation for the ski-trip problem, read:

- `python_solution/google_ski_trip_clients.py`
- `python_solution/test_google_ski_trip_clients.py`
- `python_solution/ski_trip_service.py`

## What is real here

The code now includes:

- `GooglePlaceLookupClient`
  - calls Places Text Search (New)
  - sends a text query like `"Vail Ski Resort"`
  - asks only for `places.id` and `places.displayName`
  - returns a `ResolvedPlace`

- `GoogleRouteMatrixClient`
  - calls Routes `computeRouteMatrix`
  - sends all place IDs as origins and destinations
  - parses `originIndex`, `destinationIndex`, and `duration`
  - returns `dict[(origin_place_id, destination_place_id)] -> seconds`

## Real request shape

The current Google Routes request body shape for place IDs is:

```json
{
  "origins": [
    {
      "waypoint": {
        "placeId": "ChIJ..."
      }
    }
  ],
  "destinations": [
    {
      "waypoint": {
        "placeId": "ChIJ..."
      }
    }
  ],
  "travelMode": "DRIVE",
  "routingPreference": "TRAFFIC_AWARE"
}
```

The Places Text Search request shape for lookup is:

```json
{
  "textQuery": "Vail Ski Resort"
}
```

with field mask:

```text
places.id,places.displayName
```

## Practical limits worth remembering

According to the official Routes docs as checked on 2026-03-15:

- non-transit route matrix requests cannot exceed 625 elements
- if you use `TRAFFIC_AWARE_OPTIMAL`, the element limit drops to 100
- if you specify origins or destinations using address or place ID, you can specify up to 50 total that way

## Why this matters

The important architectural point is the same as the restaurant problem:

- Google returns nested transport-specific JSON
- your planner should not depend on that shape
- the adapter converts it into the clean port contract

That is why `SkiTripPlanner` still only depends on:

- `PlaceLookupPort`
- `RouteMatrixPort`

## Environment variables

You can wire the real clients with:

```bash
GOOGLE_MAPS_API_KEY=...
```

or separately:

```bash
GOOGLE_PLACES_API_KEY=...
GOOGLE_ROUTES_API_KEY=...
```

Then:

```python
from ski_trip_service import build_ski_trip_planner

planner = build_ski_trip_planner()
```
