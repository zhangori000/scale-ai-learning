from __future__ import annotations

import json
import urllib.request

from models import Bounds, RestaurantRecord, RestaurantSearchPage


PRICE_LEVEL_TO_INT: dict[str, int] = {
    "PRICE_LEVEL_FREE": 0,
    "PRICE_LEVEL_INEXPENSIVE": 1,
    "PRICE_LEVEL_MODERATE": 2,
    "PRICE_LEVEL_EXPENSIVE": 3,
    "PRICE_LEVEL_VERY_EXPENSIVE": 4,
}


class GooglePlacesSearchClient:
    """Places API (New) Text Search adapter.

    This adapter translates Google's nested `places` response into the flat
    domain objects used by `RestaurantService`.
    """

    def __init__(
        self,
        api_key: str,
        *,
        endpoint: str = "https://places.googleapis.com/v1/places:searchText",
        text_query: str = "restaurant",
        included_type: str = "restaurant",
        strict_type_filtering: bool = True,
        language_code: str | None = None,
        timeout_seconds: float = 20.0,
        field_mask: str | None = None,
    ) -> None:
        self.api_key = api_key
        self.endpoint = endpoint
        self.text_query = text_query
        self.included_type = included_type
        self.strict_type_filtering = strict_type_filtering
        self.language_code = language_code
        self.timeout_seconds = timeout_seconds
        self.field_mask = field_mask or ",".join(
            [
                "places.id",
                "places.displayName",
                "places.location",
                "places.rating",
                "places.userRatingCount",
                "places.priceLevel",
                "places.primaryType",
                "places.types",
                "nextPageToken",
            ]
        )

    def search_restaurants(
        self,
        bounds: Bounds,
        *,
        page_token: str | None = None,
        page_size: int = 20,
    ) -> RestaurantSearchPage:
        request_body = self._build_request_body(
            bounds=bounds,
            page_token=page_token,
            page_size=page_size,
        )
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
        return self._parse_search_response(payload)

    def _build_request_body(
        self,
        *,
        bounds: Bounds,
        page_token: str | None,
        page_size: int,
    ) -> dict:
        normalized_page_size = max(1, min(page_size, 20))
        (lat1, lng1), (lat2, lng2) = bounds
        low_lat = min(lat1, lat2)
        high_lat = max(lat1, lat2)
        low_lng = min(lng1, lng2)
        high_lng = max(lng1, lng2)

        body = {
            "textQuery": self.text_query,
            "pageSize": normalized_page_size,
            "locationRestriction": {
                "rectangle": {
                    "low": {
                        "latitude": low_lat,
                        "longitude": low_lng,
                    },
                    "high": {
                        "latitude": high_lat,
                        "longitude": high_lng,
                    },
                }
            },
            "includedType": self.included_type,
            "strictTypeFiltering": self.strict_type_filtering,
        }
        if self.language_code:
            body["languageCode"] = self.language_code
        if page_token:
            body["pageToken"] = page_token
        return body

    def _parse_search_response(self, payload: dict) -> RestaurantSearchPage:
        restaurants = [
            self._parse_place(place_payload)
            for place_payload in payload.get("places", [])
        ]
        return RestaurantSearchPage(
            restaurants=restaurants,
            next_page_token=payload.get("nextPageToken"),
        )

    def _parse_place(self, place_payload: dict) -> RestaurantRecord:
        display_name = place_payload.get("displayName") or {}
        location = place_payload.get("location") or {}
        return RestaurantRecord(
            place_id=str(place_payload["id"]),
            name=str(display_name.get("text", "")),
            lat=float(location.get("latitude", 0.0)),
            lng=float(location.get("longitude", 0.0)),
            rating=_optional_float(place_payload.get("rating")),
            user_rating_count=int(place_payload.get("userRatingCount", 0) or 0),
            price_level=self._parse_price_level(place_payload.get("priceLevel")),
            primary_type=place_payload.get("primaryType"),
            types=tuple(place_payload.get("types", [])),
        )

    def _parse_price_level(self, price_level: str | None) -> int | None:
        if price_level is None:
            return None
        return PRICE_LEVEL_TO_INT.get(price_level)


def _optional_float(value) -> float | None:
    if value is None:
        return None
    return float(value)
