from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from models import Bounds, RestaurantRecord
from restaurant_service import RestaurantService


@dataclass(frozen=True)
class Tile:
    bounds: Bounds
    depth: int


class LargeAreaRestaurantService:
    """Handles dense or wide queries by recursively splitting the rectangle.

    This is useful because Places Text Search pages are limited and large
    categorical queries can under-sample dense areas if you only scan a single
    rectangle.
    """

    def __init__(
        self,
        restaurant_service: RestaurantService,
    ) -> None:
        self.restaurant_service = restaurant_service

    def fetch_top_restaurants_large_area(
        self,
        bounds: Bounds,
        *,
        cuisine_types: list[str] | None = None,
        limit: int = 20,
        page_size: int = 20,
        max_pages_per_tile: int = 3,
        max_tile_depth: int = 2,
        min_lat_span: float = 0.01,
        min_lng_span: float = 0.01,
    ) -> list[RestaurantRecord]:
        return self._fetch_top_restaurants_large_area(
            bounds,
            cuisine_types=cuisine_types,
            limit=limit,
            page_size=page_size,
            max_pages_per_tile=max_pages_per_tile,
            max_tile_depth=max_tile_depth,
            min_lat_span=min_lat_span,
            min_lng_span=min_lng_span,
            traversal="dfs",
        )

    def fetch_top_restaurants_large_area_bfs(
        self,
        bounds: Bounds,
        *,
        cuisine_types: list[str] | None = None,
        limit: int = 20,
        page_size: int = 20,
        max_pages_per_tile: int = 3,
        max_tile_depth: int = 2,
        min_lat_span: float = 0.01,
        min_lng_span: float = 0.01,
    ) -> list[RestaurantRecord]:
        return self._fetch_top_restaurants_large_area(
            bounds,
            cuisine_types=cuisine_types,
            limit=limit,
            page_size=page_size,
            max_pages_per_tile=max_pages_per_tile,
            max_tile_depth=max_tile_depth,
            min_lat_span=min_lat_span,
            min_lng_span=min_lng_span,
            traversal="bfs",
        )

    def _fetch_top_restaurants_large_area(
        self,
        bounds: Bounds,
        *,
        cuisine_types: list[str] | None,
        limit: int,
        page_size: int,
        max_pages_per_tile: int,
        max_tile_depth: int,
        min_lat_span: float,
        min_lng_span: float,
        traversal: str,
    ) -> list[RestaurantRecord]:
        deduped: dict[str, RestaurantRecord] = {}
        pending = deque([Tile(bounds=bounds, depth=0)])

        while pending:
            if traversal == "bfs":
                tile = pending.popleft()
            else:
                tile = pending.pop()
            scan_result = self.restaurant_service.scan_restaurants(
                tile.bounds,
                cuisine_types=cuisine_types,
                page_size=page_size,
                max_pages=max_pages_per_tile,
            )
            for restaurant in scan_result.restaurants:
                deduped[restaurant.place_id] = restaurant

            if (
                scan_result.saturated
                and tile.depth < max_tile_depth
                and self._can_split(
                    tile.bounds,
                    min_lat_span=min_lat_span,
                    min_lng_span=min_lng_span,
                )
            ):
                pending.extend(self._split_into_quadrants(tile))

        restaurants = sorted(
            deduped.values(),
            key=self.restaurant_service._sort_key,
        )
        return restaurants[:limit]

    def _can_split(
        self,
        bounds: Bounds,
        *,
        min_lat_span: float,
        min_lng_span: float,
    ) -> bool:
        (lat1, lng1), (lat2, lng2) = _normalize_bounds(bounds)
        return (lat2 - lat1) > min_lat_span or (lng2 - lng1) > min_lng_span

    def _split_into_quadrants(self, tile: Tile) -> list[Tile]:
        (low_lat, low_lng), (high_lat, high_lng) = _normalize_bounds(tile.bounds)
        mid_lat = (low_lat + high_lat) / 2.0
        mid_lng = (low_lng + high_lng) / 2.0
        next_depth = tile.depth + 1

        return [
            Tile(bounds=((low_lat, low_lng), (mid_lat, mid_lng)), depth=next_depth),
            Tile(bounds=((low_lat, mid_lng), (mid_lat, high_lng)), depth=next_depth),
            Tile(bounds=((mid_lat, low_lng), (high_lat, mid_lng)), depth=next_depth),
            Tile(bounds=((mid_lat, mid_lng), (high_lat, high_lng)), depth=next_depth),
        ]


def _normalize_bounds(bounds: Bounds) -> Bounds:
    (lat1, lng1), (lat2, lng2) = bounds
    return (
        (min(lat1, lat2), min(lng1, lng2)),
        (max(lat1, lat2), max(lng1, lng2)),
    )
