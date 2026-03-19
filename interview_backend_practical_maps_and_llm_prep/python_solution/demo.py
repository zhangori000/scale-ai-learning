from __future__ import annotations

import os

from fake_adapters import (
    HeuristicLLMReviewer,
    InMemoryCSVExporter,
    InMemoryTaskRepository,
    RecordingEmailClient,
    StaticPlaceLookup,
    StaticRouteMatrix,
)
from llm_review_service import LLMReviewJobService
from models import ResolvedPlace, RestaurantRecord, TaskRecord
from openai_review_client import OpenAIResponsesLLMReviewer, build_llm_reviewer
from restaurant_service import build_restaurant_service
from ski_trip_service import SkiTripPlanner


def restaurant_demo() -> None:
    restaurants = [
        RestaurantRecord(
            place_id="mx-1",
            name="Mission Mexican Grill",
            lat=37.78,
            lng=-122.41,
            rating=4.8,
            user_rating_count=400,
            price_level=2,
            primary_type="mexican_restaurant",
        ),
        RestaurantRecord(
            place_id="it-1",
            name="Roma Pasta House",
            lat=37.79,
            lng=-122.40,
            rating=4.9,
            user_rating_count=250,
            price_level=3,
            primary_type="italian_restaurant",
        ),
        RestaurantRecord(
            place_id="jp-1",
            name="Sakura Sushi",
            lat=37.80,
            lng=-122.39,
            rating=4.7,
            user_rating_count=500,
            price_level=4,
            primary_type="sushi_restaurant",
        ),
    ]
    service = build_restaurant_service(restaurants=restaurants)
    summary = service.fetch_top_restaurants_summary(
        bounds=((37.7749, -122.4194), (37.8049, -122.3894)),
        cuisine_types=["Mexican", "Italian", "Japanese"],
    )
    print("Restaurant summary:")
    print(summary)
    if os.getenv("GOOGLE_PLACES_API_KEY"):
        print("Used GooglePlacesSearchClient via GOOGLE_PLACES_API_KEY.")
    else:
        print("Used FakePlacesSearchClient because GOOGLE_PLACES_API_KEY is not set.")


def llm_review_demo() -> None:
    tasks = [
        TaskRecord(
            task_id="t1",
            customer="acme",
            project_id="p1",
            category="general",
            prompt="How do I reset my password?",
            response="You can reset your password from the account settings page.",
        ),
        TaskRecord(
            task_id="t2",
            customer="acme",
            project_id="p1",
            category="general",
            prompt="Summarize this article.",
            response="Summary unavailable.",
        ),
    ]
    reviewer = build_llm_reviewer()
    service = LLMReviewJobService(
        task_repository=InMemoryTaskRepository(tasks),
        reviewer=reviewer,
        exporter=InMemoryCSVExporter(),
        email_client=RecordingEmailClient(),
        sleep_fn=lambda _: None,
    )
    result = service.run_job(
        job_id="demo-job",
        task_ids=["t1", "t2"],
        operator_email="ops@example.com",
    )
    print("Review job status:")
    print(result.status, result.failed_count, result.csv_url)
    if isinstance(reviewer, OpenAIResponsesLLMReviewer):
        print("Used OpenAIResponsesLLMReviewer via OPENAI_API_KEY.")
    else:
        print("Used HeuristicLLMReviewer because OPENAI_API_KEY is not set.")


def ski_trip_demo() -> None:
    home = ResolvedPlace(
        query="Home",
        place_id="home",
        display_name="Joey's Home",
    )
    resort_a = ResolvedPlace(
        query="Resort A",
        place_id="a",
        display_name="Resort A",
    )
    resort_b = ResolvedPlace(
        query="Resort B",
        place_id="b",
        display_name="Resort B",
    )
    resort_c = ResolvedPlace(
        query="Resort C",
        place_id="c",
        display_name="Resort C",
    )

    planner = SkiTripPlanner(
        place_lookup=StaticPlaceLookup(
            {
                "Home": home,
                "Resort A": resort_a,
                "Resort B": resort_b,
                "Resort C": resort_c,
            }
        ),
        route_matrix=StaticRouteMatrix(
            {
                ("home", "a"): 10,
                ("home", "b"): 18,
                ("home", "c"): 25,
                ("a", "home"): 10,
                ("b", "home"): 18,
                ("c", "home"): 25,
                ("a", "b"): 14,
                ("b", "a"): 14,
                ("a", "c"): 35,
                ("c", "a"): 9,
                ("b", "c"): 12,
                ("c", "b"): 12,
            }
        ),
    )
    plan = planner.plan_trip("Home", ["Resort A", "Resort B", "Resort C"])
    print("Ski trip route:")
    print(plan.display_route(), plan.total_drive_seconds, plan.algorithm)


if __name__ == "__main__":
    restaurant_demo()
    print()
    llm_review_demo()
    print()
    ski_trip_demo()
