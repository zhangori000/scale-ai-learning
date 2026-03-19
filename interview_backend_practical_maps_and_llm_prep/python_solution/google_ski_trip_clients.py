from __future__ import annotations

import json
import os
import urllib.request

from models import ResolvedPlace
from ports import PlaceLookupPort, RouteMatrixPort


class GooglePlaceLookupClient:
    """Resolves a free-text location query into a Google place ID.

    Uses Places API Text Search (New):
    POST https://places.googleapis.com/v1/places:searchText
    """

    def __init__(
        self,
        api_key: str,
        *,
        endpoint: str = "https://places.googleapis.com/v1/places:searchText",
        language_code: str | None = None,
        timeout_seconds: float = 20.0,
        field_mask: str = "places.id,places.displayName",
    ) -> None:
        self.api_key = api_key
        self.endpoint = endpoint
        self.language_code = language_code
        self.timeout_seconds = timeout_seconds
        self.field_mask = field_mask

    def resolve_place(self, query: str) -> ResolvedPlace:
        request_body = {"textQuery": query}
        if self.language_code is not None:
            request_body["languageCode"] = self.language_code

        request = urllib.request.Request(
            url=self.endpoint,
            data=json.dumps(request_body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.api_key,
                "X-Goog-FieldMask": self.field_mask,
            },
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))

        places = payload.get("places", [])
        if not places:
            raise ValueError(f"No place found for query: {query}")

        best_match = places[0]
        display_name = best_match.get("displayName") or {}
        return ResolvedPlace(
            query=query,
            place_id=str(best_match["id"]),
            display_name=str(display_name.get("text", query)),
        )


class GoogleRouteMatrixClient:
    """Builds pairwise driving durations from Google Routes computeRouteMatrix.

    Uses Routes API:
    POST https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix
    """

    def __init__(
        self,
        api_key: str,
        *,
        endpoint: str = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix",
        timeout_seconds: float = 30.0,
        travel_mode: str = "DRIVE",
        routing_preference: str = "TRAFFIC_AWARE",
        field_mask: str = "originIndex,destinationIndex,duration,condition,status",
    ) -> None:
        self.api_key = api_key
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self.travel_mode = travel_mode
        self.routing_preference = routing_preference
        self.field_mask = field_mask

    def build_drive_time_matrix(
        self,
        place_ids: list[str],
    ) -> dict[tuple[str, str], int]:
        request_body = {
            "origins": [self._place_waypoint(place_id) for place_id in place_ids],
            "destinations": [self._place_waypoint(place_id) for place_id in place_ids],
            "travelMode": self.travel_mode,
            "routingPreference": self.routing_preference,
        }

        request = urllib.request.Request(
            url=self.endpoint,
            data=json.dumps(request_body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.api_key,
                "X-Goog-FieldMask": self.field_mask,
            },
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))

        if not isinstance(payload, list):
            raise ValueError("Route matrix response must be a JSON array")

        matrix: dict[tuple[str, str], int] = {}
        for element in payload:
            status = element.get("status") or {}
            if status.get("code", 0) not in (0, None):
                raise ValueError(
                    f"Route matrix element failed: {status.get('message', status)}"
                )
            if element.get("condition") not in (None, "ROUTE_EXISTS"):
                raise ValueError(
                    f"Route matrix element missing route: {element.get('condition')}"
                )

            origin_index = int(element["originIndex"])
            destination_index = int(element["destinationIndex"])
            duration_seconds = _parse_duration_seconds(element.get("duration"))
            matrix[(place_ids[origin_index], place_ids[destination_index])] = (
                duration_seconds
            )

        for origin in place_ids:
            for destination in place_ids:
                key = (origin, destination)
                if origin == destination:
                    matrix[key] = 0
                elif key not in matrix:
                    raise ValueError(f"Missing route duration for pair {key}")

        return matrix

    def _place_waypoint(self, place_id: str) -> dict:
        return {
            "waypoint": {
                "placeId": place_id,
            }
        }


def build_google_ski_trip_clients(
    *,
    maps_api_key: str | None = None,
    places_api_key: str | None = None,
    routes_api_key: str | None = None,
) -> tuple[PlaceLookupPort, RouteMatrixPort]:
    resolved_places_key = (
        places_api_key
        or maps_api_key
        or os.getenv("GOOGLE_PLACES_API_KEY")
        or os.getenv("GOOGLE_MAPS_API_KEY")
    )
    resolved_routes_key = (
        routes_api_key
        or maps_api_key
        or os.getenv("GOOGLE_ROUTES_API_KEY")
        or os.getenv("GOOGLE_MAPS_API_KEY")
    )

    if resolved_places_key is None:
        raise ValueError("Missing Google Places API key")
    if resolved_routes_key is None:
        raise ValueError("Missing Google Routes API key")

    return (
        GooglePlaceLookupClient(api_key=resolved_places_key),
        GoogleRouteMatrixClient(api_key=resolved_routes_key),
    )


def _parse_duration_seconds(duration: str | None) -> int:
    if duration is None:
        raise ValueError("Matrix element missing duration")
    if not duration.endswith("s"):
        raise ValueError(f"Unsupported duration format: {duration}")
    return int(round(float(duration[:-1])))
