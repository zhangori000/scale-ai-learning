from __future__ import annotations

import os

from fake_adapters import FakePlacesSearchClient
from google_places_client import GooglePlacesSearchClient
from models import Bounds, CuisineSummary, RestaurantRecord, RestaurantScanResult
from ports import PlacesSearchPort


DEFAULT_CUISINE_TYPE_MAP: dict[str, set[str]] = {
    "mexican": {"mexican_restaurant"},
    "italian": {"italian_restaurant"},
    "japanese": {
        "japanese_restaurant",
        "sushi_restaurant",
        "ramen_restaurant",
        "izakaya_restaurant",
    },
}


class RestaurantService:
    def __init__(
        self,
        places_client: PlacesSearchPort,
        cuisine_type_map: dict[str, set[str]] | None = None,
    ) -> None:
        self.places_client = places_client
        self.cuisine_type_map = cuisine_type_map or DEFAULT_CUISINE_TYPE_MAP

    def fetch_top_restaurants(
        self,
        bounds: Bounds,
        *,
        cuisine_types: list[str] | None = None,
        limit: int = 20,
        page_size: int = 20,
        max_pages: int = 10,
    ) -> list[RestaurantRecord]:
        scan_result = self.scan_restaurants(
            bounds,
            cuisine_types=cuisine_types,
            page_size=page_size,
            max_pages=max_pages,
        )
        restaurants = sorted(scan_result.restaurants, key=self._sort_key)
        return restaurants[:limit]

    def scan_restaurants(
        self,
        bounds: Bounds,
        *,
        cuisine_types: list[str] | None = None,
        page_size: int = 20,
        max_pages: int = 10,
    ) -> RestaurantScanResult:
        requested = self._normalize_requested_cuisines(cuisine_types)
        deduped: dict[str, RestaurantRecord] = {}
        page_token: str | None = None
        pages_fetched = 0

        for _ in range(max_pages):
            pages_fetched += 1
            page = self.places_client.search_restaurants(
                bounds,
                page_token=page_token,
                page_size=page_size,
            )
            for restaurant in page.restaurants:
                if restaurant.place_id in deduped:
                    continue
                if requested and not self._matches_requested_cuisines(
                    restaurant,
                    requested,
                ):
                    continue
                deduped[restaurant.place_id] = restaurant
            if page.next_page_token is None:
                page_token = None
                break
            page_token = page.next_page_token

        restaurants = sorted(deduped.values(), key=self._sort_key)
        return RestaurantScanResult(
            restaurants=restaurants,
            saturated=page_token is not None,
            pages_fetched=pages_fetched,
        )

    def fetch_top_restaurants_summary(
        self,
        bounds: Bounds,
        *,
        cuisine_types: list[str],
        limit: int = 20,
        page_size: int = 20,
        max_pages: int = 10,
    ) -> dict[str, dict[str, float | int | None]]:
        restaurants = self.fetch_top_restaurants(
            bounds,
            cuisine_types=cuisine_types,
            limit=limit,
            page_size=page_size,
            max_pages=max_pages,
        )
        summaries = self.summarize_by_cuisine(restaurants, cuisine_types)
        return {
            cuisine: {
                "count": summary.count,
                "avg_price_level": summary.avg_price_level,
            }
            for cuisine, summary in summaries.items()
        }

    def summarize_by_cuisine(
        self,
        restaurants: list[RestaurantRecord],
        cuisine_types: list[str],
    ) -> dict[str, CuisineSummary]:
        summaries: dict[str, CuisineSummary] = {}
        for cuisine in cuisine_types:
            canonical = self._canonical_cuisine_name(cuisine)
            matches = [
                restaurant
                for restaurant in restaurants
                if canonical in self.infer_cuisines(restaurant)
            ]
            prices = [
                restaurant.price_level
                for restaurant in matches
                if restaurant.price_level is not None
            ]
            avg_price = None
            if prices:
                avg_price = round(sum(prices) / len(prices), 2)
            summaries[cuisine] = CuisineSummary(
                count=len(matches),
                avg_price_level=avg_price,
            )
        return summaries

    def infer_cuisines(self, restaurant: RestaurantRecord) -> set[str]:
        observed_types: set[str] = set()
        if restaurant.primary_type is not None:
            observed_types.add(restaurant.primary_type.lower())
        observed_types.update(value.lower() for value in restaurant.types)

        matches: set[str] = set()
        for cuisine_name, google_types in self.cuisine_type_map.items():
            if observed_types.intersection(google_types):
                matches.add(cuisine_name)

        lowered_name = restaurant.name.lower()
        for cuisine_name in self.cuisine_type_map:
            if cuisine_name in lowered_name:
                matches.add(cuisine_name)
        return matches

    def _normalize_requested_cuisines(
        self,
        cuisine_types: list[str] | None,
    ) -> set[str]:
        if not cuisine_types:
            return set()
        return {self._canonical_cuisine_name(cuisine) for cuisine in cuisine_types}

    def _canonical_cuisine_name(self, cuisine_name: str) -> str:
        return cuisine_name.strip().lower()

    def _matches_requested_cuisines(
        self,
        restaurant: RestaurantRecord,
        requested_cuisines: set[str],
    ) -> bool:
        return bool(self.infer_cuisines(restaurant).intersection(requested_cuisines))

    def _sort_key(self, restaurant: RestaurantRecord) -> tuple[float, int, str]:
        rating = restaurant.rating if restaurant.rating is not None else -1.0
        return (-rating, -restaurant.user_rating_count, restaurant.place_id)


def build_places_client(
    *,
    restaurants: list[RestaurantRecord] | None = None,
    google_api_key: str | None = None,
) -> PlacesSearchPort:
    resolved_api_key = google_api_key or os.getenv("GOOGLE_PLACES_API_KEY")
    if resolved_api_key:
        return GooglePlacesSearchClient(api_key=resolved_api_key)
    if restaurants is not None:
        return FakePlacesSearchClient(restaurants)
    raise ValueError(
        "Provide GOOGLE_PLACES_API_KEY or pass sample restaurants for the fake client"
    )


def build_restaurant_service(
    *,
    restaurants: list[RestaurantRecord] | None = None,
    google_api_key: str | None = None,
    cuisine_type_map: dict[str, set[str]] | None = None,
) -> RestaurantService:
    return RestaurantService(
        places_client=build_places_client(
            restaurants=restaurants,
            google_api_key=google_api_key,
        ),
        cuisine_type_map=cuisine_type_map,
    )
