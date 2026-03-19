from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from google_ski_trip_clients import (
    GooglePlaceLookupClient,
    GoogleRouteMatrixClient,
    build_google_ski_trip_clients,
)


class _FakeHTTPResponse:
    def __init__(self, payload) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class GoogleSkiTripClientsTest(unittest.TestCase):
    def test_place_lookup_translates_places_text_search(self) -> None:
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
                            "id": "ChIJ-place",
                            "displayName": {"text": "Vail Ski Resort"},
                        }
                    ]
                }
            )

        client = GooglePlaceLookupClient(api_key="test-key", language_code="en")

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            place = client.resolve_place("Vail Ski Resort")

        self.assertEqual(
            captured["url"],
            "https://places.googleapis.com/v1/places:searchText",
        )
        self.assertEqual(captured["method"], "POST")
        self.assertEqual(captured["timeout"], 20.0)
        self.assertEqual(captured["headers"]["X-goog-api-key"], "test-key")
        self.assertEqual(
            captured["headers"]["X-goog-fieldmask"],
            "places.id,places.displayName",
        )
        self.assertEqual(captured["body"]["textQuery"], "Vail Ski Resort")
        self.assertEqual(captured["body"]["languageCode"], "en")
        self.assertEqual(place.query, "Vail Ski Resort")
        self.assertEqual(place.place_id, "ChIJ-place")
        self.assertEqual(place.display_name, "Vail Ski Resort")

    def test_route_matrix_translates_compute_route_matrix(self) -> None:
        captured = {}

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            captured["method"] = request.get_method()
            captured["timeout"] = timeout
            captured["headers"] = dict(request.header_items())
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return _FakeHTTPResponse(
                [
                    {
                        "originIndex": 0,
                        "destinationIndex": 1,
                        "condition": "ROUTE_EXISTS",
                        "status": {},
                        "duration": "600s",
                    },
                    {
                        "originIndex": 1,
                        "destinationIndex": 0,
                        "condition": "ROUTE_EXISTS",
                        "status": {},
                        "duration": "720s",
                    },
                ]
            )

        client = GoogleRouteMatrixClient(api_key="routes-key")

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            matrix = client.build_drive_time_matrix(["home", "vail"])

        self.assertEqual(
            captured["url"],
            "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix",
        )
        self.assertEqual(captured["method"], "POST")
        self.assertEqual(captured["timeout"], 30.0)
        self.assertEqual(captured["headers"]["X-goog-api-key"], "routes-key")
        self.assertEqual(
            captured["headers"]["X-goog-fieldmask"],
            "originIndex,destinationIndex,duration,condition,status",
        )
        self.assertEqual(captured["body"]["travelMode"], "DRIVE")
        self.assertEqual(captured["body"]["routingPreference"], "TRAFFIC_AWARE")
        self.assertEqual(
            captured["body"]["origins"][0]["waypoint"]["placeId"],
            "home",
        )
        self.assertEqual(
            captured["body"]["destinations"][1]["waypoint"]["placeId"],
            "vail",
        )
        self.assertEqual(matrix[("home", "home")], 0)
        self.assertEqual(matrix[("home", "vail")], 600)
        self.assertEqual(matrix[("vail", "home")], 720)
        self.assertEqual(matrix[("vail", "vail")], 0)

    def test_build_google_ski_trip_clients_uses_maps_api_key_fallback(self) -> None:
        place_lookup, route_matrix = build_google_ski_trip_clients(
            maps_api_key="maps-key"
        )
        self.assertIsInstance(place_lookup, GooglePlaceLookupClient)
        self.assertIsInstance(route_matrix, GoogleRouteMatrixClient)


if __name__ == "__main__":
    unittest.main()
