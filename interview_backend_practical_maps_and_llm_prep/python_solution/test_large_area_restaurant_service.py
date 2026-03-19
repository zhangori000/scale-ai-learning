from __future__ import annotations

import unittest

from fake_adapters import FakePlacesSearchClient
from large_area_restaurant_service import LargeAreaRestaurantService
from models import RestaurantRecord
from restaurant_service import RestaurantService


class LargeAreaRestaurantServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        bounds = ((0.0, 0.0), (4.0, 4.0))
        restaurants = [
            RestaurantRecord(
                place_id="sw-low",
                name="SW Low",
                lat=0.5,
                lng=0.5,
                rating=2.0,
                user_rating_count=10,
                primary_type="restaurant",
            ),
            RestaurantRecord(
                place_id="nw-low",
                name="NW Low",
                lat=3.5,
                lng=0.5,
                rating=2.5,
                user_rating_count=20,
                primary_type="restaurant",
            ),
            RestaurantRecord(
                place_id="se-high",
                name="SE High",
                lat=0.5,
                lng=3.5,
                rating=4.9,
                user_rating_count=400,
                primary_type="restaurant",
            ),
            RestaurantRecord(
                place_id="ne-high",
                name="NE High",
                lat=3.5,
                lng=3.5,
                rating=4.8,
                user_rating_count=500,
                primary_type="restaurant",
            ),
        ]
        self.bounds = bounds
        self.base_service = RestaurantService(FakePlacesSearchClient(restaurants))
        self.large_area_service = LargeAreaRestaurantService(self.base_service)

    def test_tiling_recovers_high_rated_restaurants_from_dense_large_query(self) -> None:
        single_rectangle = self.base_service.fetch_top_restaurants(
            self.bounds,
            limit=2,
            page_size=2,
            max_pages=1,
        )
        tiled = self.large_area_service.fetch_top_restaurants_large_area(
            self.bounds,
            limit=2,
            page_size=2,
            max_pages_per_tile=1,
            max_tile_depth=1,
            min_lat_span=0.5,
            min_lng_span=0.5,
        )

        self.assertEqual(
            [restaurant.place_id for restaurant in single_rectangle],
            ["nw-low", "sw-low"],
        )
        self.assertEqual(
            [restaurant.place_id for restaurant in tiled],
            ["se-high", "ne-high"],
        )

    def test_bfs_tiling_returns_same_best_restaurants(self) -> None:
        tiled = self.large_area_service.fetch_top_restaurants_large_area_bfs(
            self.bounds,
            limit=2,
            page_size=2,
            max_pages_per_tile=1,
            max_tile_depth=1,
            min_lat_span=0.5,
            min_lng_span=0.5,
        )

        self.assertEqual(
            [restaurant.place_id for restaurant in tiled],
            ["se-high", "ne-high"],
        )


if __name__ == "__main__":
    unittest.main()
