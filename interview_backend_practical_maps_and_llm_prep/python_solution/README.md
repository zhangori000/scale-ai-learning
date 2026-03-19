# Python Reference Implementation

This folder contains runnable reference code for the three practicals in the study pack.

## Files

- `models.py`
  - shared typed models and custom exceptions
- `ports.py`
  - external dependency interfaces
- `google_places_client.py`
  - real Places API (New) adapter that translates Google JSON into domain models
- `restaurant_service.py`
  - restaurant search orchestration
- `large_area_restaurant_service.py`
  - recursive tiling for dense or wide rectangle searches
- `llm_review_service.py`
  - batch review orchestration with retry handling
- `openai_review_client.py`
  - real OpenAI Responses API reviewer adapter with structured output
- `ski_trip_service.py`
  - place resolution plus route optimization
- `google_ski_trip_clients.py`
  - real Google Places and Routes adapters for the ski-trip problem
- `fake_adapters.py`
  - in-memory implementations for tests and demos
- `demo.py`
  - small end-to-end examples
- `test_restaurant_service.py`
- `test_large_area_restaurant_service.py`
- `test_google_places_client.py`
- `test_llm_review_service.py`
- `test_openai_review_client.py`
- `test_google_ski_trip_clients.py`
- `test_ski_trip_service.py`

## Run

```bash
python -m unittest discover -v
python demo.py
```

## Optional real Google client

If `GOOGLE_PLACES_API_KEY` is set, you can build the restaurant service with the real Places adapter instead of the fake one:

```python
from restaurant_service import build_restaurant_service

service = build_restaurant_service()
```

If the API key is not set, pass sample restaurants to use the fake client:

```python
service = build_restaurant_service(restaurants=sample_restaurants)
```

## Optional real OpenAI reviewer

If `OPENAI_API_KEY` is set, you can build the LLM reviewer with the real OpenAI Responses API adapter:

```python
from openai_review_client import build_llm_reviewer

reviewer = build_llm_reviewer()
```

If the API key is not set, the same helper falls back to the heuristic mock:

```python
reviewer = build_llm_reviewer(openai_api_key=None)
```

The real adapter uses `POST /v1/responses` with `text.format.type = "json_schema"` so the model returns a structured grading object.

## Optional real Google ski-trip clients

If `GOOGLE_MAPS_API_KEY` is set, you can build the ski-trip planner with the real Google adapters:

```python
from ski_trip_service import build_ski_trip_planner

planner = build_ski_trip_planner()
```

Or pass separate keys explicitly:

```python
planner = build_ski_trip_planner(
    places_api_key="...",
    routes_api_key="...",
)
```

## Notes

- No third-party dependencies are required.
- The Google Maps and LLM provider integrations are represented as ports plus fake adapters.
- The folder now also includes a real Google Places Text Search adapter; it is separate from the fake client used in the restaurant service tests.
- `build_places_client()` and `build_restaurant_service()` will use `GOOGLE_PLACES_API_KEY` when present and otherwise fall back to the fake client if you pass sample restaurants.
- `build_llm_reviewer()` will use `OPENAI_API_KEY` when present and otherwise fall back to the heuristic reviewer.
- `build_ski_trip_planner()` can use `GOOGLE_MAPS_API_KEY`, or separate `GOOGLE_PLACES_API_KEY` and `GOOGLE_ROUTES_API_KEY`.
- The ski-trip planner now includes brute force, exact dynamic programming, and a nearest-neighbor fallback.
