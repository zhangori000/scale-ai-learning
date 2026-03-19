# Backend Practical Maps + LLM Prep

This study pack turns the contributor prompt into three cleaner backend practicals:

1. Google Maps restaurant search in a bounding box
2. LLM batch quality review over task JSON blobs
3. Google Maps ski-trip route optimization

It is organized around patterns that show up repeatedly in `scale-agentex` and `scale-agentex-python`: typed models, ports/adapters, orchestration services, retries, pagination, and tests.

## Files

- `00_original_prompt_verbatim.md`
  - the contributor prompt saved verbatim, typos included
- `01_agentex_pattern_digest.md`
  - the backend patterns worth copying from the Agentex repos
- `02_clarified_requirements_and_hidden_assumptions.md`
  - the missing details you should state explicitly in interview
- `03_google_maps_restaurants_solution.md`
  - design, edge cases, and follow-up answers
- `04_llm_quality_review_solution.md`
  - job architecture, retry logic, data model, and failure handling
- `05_ski_trip_route_solution.md`
  - Places lookup, route matrix construction, and exact route optimization
- `06_interview_answer_script.md`
  - short answer scripts you can practice aloud
- `07_sources_and_api_notes.md`
  - official Google API links and the concrete facts that matter
- `08_large_area_tiling_followup.md`
  - the dense-query follow-up for very large rectangles
- `09_real_openai_llm_call.md`
  - concrete OpenAI Responses API version of the LLM reviewer
- `10_real_google_ski_trip_clients.md`
  - concrete Google Places and Routes adapters for the ski-trip problem
- `python_solution/`
  - runnable reference code with tests

## Suggested study order

1. Read `00_original_prompt_verbatim.md`
2. Read `01_agentex_pattern_digest.md`
3. Read `02_clarified_requirements_and_hidden_assumptions.md`
4. Read `03_google_maps_restaurants_solution.md`
5. Read `04_llm_quality_review_solution.md`
6. Read `05_ski_trip_route_solution.md`
7. Read `06_interview_answer_script.md`
8. Read `07_sources_and_api_notes.md`
9. Read `08_large_area_tiling_followup.md`
10. Read `09_real_openai_llm_call.md`
11. Read `10_real_google_ski_trip_clients.md`
12. Run the tests in `python_solution/`

## Quick run

From `python_solution/`:

```bash
python -m unittest discover -v
python demo.py
```
