from __future__ import annotations

import unittest
from unittest.mock import patch

from google_places_client import GooglePlacesSearchClient
from models import RestaurantRecord
from restaurant_service import build_places_client, build_restaurant_service


class RestaurantFactoryTest(unittest.TestCase):
    def test_build_places_client_prefers_google_when_api_key_present(self) -> None:
        client = build_places_client(google_api_key="test-key")

        self.assertIsInstance(client, GooglePlacesSearchClient)

    def test_build_places_client_uses_fake_when_restaurants_provided(self) -> None:
        client = build_places_client(
            restaurants=[
                RestaurantRecord(
                    place_id="mx-1",
                    name="Mission Mexican Grill",
                    lat=37.78,
                    lng=-122.41,
                )
            ]
        )

        self.assertEqual(client.__class__.__name__, "FakePlacesSearchClient")

    def test_build_restaurant_service_reads_env_api_key(self) -> None:
        with patch.dict("os.environ", {"GOOGLE_PLACES_API_KEY": "env-key"}, clear=False):
            service = build_restaurant_service()

        self.assertIsInstance(service.places_client, GooglePlacesSearchClient)


if __name__ == "__main__":
    unittest.main()
