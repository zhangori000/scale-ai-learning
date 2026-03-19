from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from google_places_client import GooglePlacesSearchClient


class _FakeHTTPResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class GooglePlacesSearchClientTest(unittest.TestCase):
    def test_search_restaurants_translates_google_shape(self) -> None:
        captured = {}

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            captured["method"] = request.get_method()
            captured["timeout"] = timeout
            captured["headers"] = dict(request.header_items())
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return _FakeHTTPResponse(
                {
                    "places": [
                        {
                            "id": "place-1",
                            "displayName": {"text": "Roma Pasta House"},
                            "location": {
                                "latitude": 37.79,
                                "longitude": -122.40,
                            },
                            "rating": 4.9,
                            "userRatingCount": 250,
                            "priceLevel": "PRICE_LEVEL_EXPENSIVE",
                            "primaryType": "italian_restaurant",
                            "types": ["restaurant", "food", "italian_restaurant"],
                        }
                    ],
                    "nextPageToken": "token-2",
                }
            )

        client = GooglePlacesSearchClient(
            api_key="test-key",
            language_code="en",
        )

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            page = client.search_restaurants(
                ((37.8049, -122.3894), (37.7749, -122.4194)),
                page_token="token-1",
                page_size=25,
            )

        self.assertEqual(
            captured["url"],
            "https://places.googleapis.com/v1/places:searchText",
        )
        self.assertEqual(captured["method"], "POST")
        self.assertEqual(captured["timeout"], 20.0)
        self.assertEqual(captured["headers"]["X-goog-api-key"], "test-key")
        self.assertIn("places.id", captured["headers"]["X-goog-fieldmask"])
        self.assertEqual(captured["body"]["textQuery"], "restaurant")
        self.assertEqual(captured["body"]["includedType"], "restaurant")
        self.assertTrue(captured["body"]["strictTypeFiltering"])
        self.assertEqual(captured["body"]["languageCode"], "en")
        self.assertEqual(captured["body"]["pageToken"], "token-1")
        self.assertEqual(captured["body"]["pageSize"], 20)
        self.assertEqual(
            captured["body"]["locationRestriction"]["rectangle"]["low"],
            {"latitude": 37.7749, "longitude": -122.4194},
        )
        self.assertEqual(
            captured["body"]["locationRestriction"]["rectangle"]["high"],
            {"latitude": 37.8049, "longitude": -122.3894},
        )

        self.assertEqual(page.next_page_token, "token-2")
        self.assertEqual(len(page.restaurants), 1)
        restaurant = page.restaurants[0]
        self.assertEqual(restaurant.place_id, "place-1")
        self.assertEqual(restaurant.name, "Roma Pasta House")
        self.assertEqual(restaurant.lat, 37.79)
        self.assertEqual(restaurant.lng, -122.4)
        self.assertEqual(restaurant.rating, 4.9)
        self.assertEqual(restaurant.user_rating_count, 250)
        self.assertEqual(restaurant.price_level, 3)
        self.assertEqual(restaurant.primary_type, "italian_restaurant")
        self.assertEqual(
            restaurant.types,
            ("restaurant", "food", "italian_restaurant"),
        )


if __name__ == "__main__":
    unittest.main()
