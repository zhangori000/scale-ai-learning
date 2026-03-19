from __future__ import annotations

import unittest

from fake_adapters import FakePlacesSearchClient
from models import RestaurantRecord
from restaurant_service import RestaurantService


class RestaurantServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.bounds = ((37.7749, -122.4194), (37.8049, -122.3894))
        self.restaurants = [
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
                rating=4.9,
                user_rating_count=500,
                price_level=4,
                primary_type="sushi_restaurant",
            ),
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
                place_id="mx-1",
                name="Mission Mexican Grill Duplicate",
                lat=37.78,
                lng=-122.41,
                rating=4.7,
                user_rating_count=5,
                price_level=2,
                primary_type="mexican_restaurant",
            ),
            RestaurantRecord(
                place_id="it-2",
                name="Little Italy",
                lat=37.781,
                lng=-122.405,
                rating=4.6,
                user_rating_count=150,
                price_level=None,
                primary_type="italian_restaurant",
            ),
        ]

    def test_fetch_top_restaurants_filters_and_sorts(self) -> None:
        service = RestaurantService(FakePlacesSearchClient(self.restaurants))
        result = service.fetch_top_restaurants(
            self.bounds,
            cuisine_types=["Italian", "Japanese"],
            limit=10,
            page_size=2,
        )

        self.assertEqual([item.place_id for item in result], ["jp-1", "it-1", "it-2"])

    def test_fetch_top_restaurants_summary(self) -> None:
        service = RestaurantService(FakePlacesSearchClient(self.restaurants))
        result = service.fetch_top_restaurants_summary(
            self.bounds,
            cuisine_types=["Mexican", "Italian", "Japanese"],
            limit=10,
            page_size=2,
        )

        expected = {
            "Mexican": {"count": 1, "avg_price_level": 2.0},
            "Italian": {"count": 2, "avg_price_level": 3.0},
            "Japanese": {"count": 1, "avg_price_level": 4.0},
        }
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
