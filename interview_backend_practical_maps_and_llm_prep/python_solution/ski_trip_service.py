from __future__ import annotations

import itertools

from google_ski_trip_clients import build_google_ski_trip_clients
from models import ResolvedPlace, TripPlan
from ports import PlaceLookupPort, RouteMatrixPort


class SkiTripPlanner:
    def __init__(
        self,
        place_lookup: PlaceLookupPort,
        route_matrix: RouteMatrixPort,
        *,
        exact_solver_limit: int = 12,
    ) -> None:
        self.place_lookup = place_lookup
        self.route_matrix = route_matrix
        self.exact_solver_limit = exact_solver_limit

    def plan_trip(
        self,
        home_query: str,
        resort_queries: list[str],
        *,
        strategy: str = "auto",
    ) -> TripPlan:
        home = self.place_lookup.resolve_place(home_query)
        resorts = [self.place_lookup.resolve_place(query) for query in resort_queries]

        if not resorts:
            if strategy == "bruteforce":
                algorithm = "exact_bruteforce"
            else:
                algorithm = "exact_dp"
            return TripPlan(
                ordered_stops=[home, home],
                total_drive_seconds=0,
                algorithm=algorithm,
            )

        nodes = [home, *resorts]
        matrix = self.route_matrix.build_drive_time_matrix(
            [node.place_id for node in nodes]
        )

        if strategy == "auto":
            if len(resorts) <= self.exact_solver_limit:
                ordered_indices, total_seconds = self._solve_exact(nodes, matrix)
                algorithm = "exact_dp"
            else:
                ordered_indices, total_seconds = self._solve_nearest_neighbor(nodes, matrix)
                algorithm = "nearest_neighbor"
        elif strategy == "dp":
            ordered_indices, total_seconds = self._solve_exact(nodes, matrix)
            algorithm = "exact_dp"
        elif strategy == "bruteforce":
            ordered_indices, total_seconds = self._solve_bruteforce(nodes, matrix)
            algorithm = "exact_bruteforce"
        elif strategy == "nearest_neighbor":
            ordered_indices, total_seconds = self._solve_nearest_neighbor(nodes, matrix)
            algorithm = "nearest_neighbor"
        else:
            raise ValueError(
                "strategy must be one of: auto, dp, bruteforce, nearest_neighbor"
            )

        ordered_stops = [nodes[index] for index in ordered_indices]
        return TripPlan(
            ordered_stops=ordered_stops,
            total_drive_seconds=total_seconds,
            algorithm=algorithm,
        )

    def _solve_bruteforce(
        self,
        nodes: list[ResolvedPlace],
        matrix: dict[tuple[str, str], int],
    ) -> tuple[list[int], int]:
        resort_indices = list(range(1, len(nodes)))
        best_route = None
        best_total = None

        for permutation in itertools.permutations(resort_indices):
            route = [0, *permutation, 0]
            total_seconds = 0
            for index in range(len(route) - 1):
                total_seconds += self._distance(
                    route[index],
                    route[index + 1],
                    nodes,
                    matrix,
                )
            if best_total is None or total_seconds < best_total:
                best_total = total_seconds
                best_route = route

        return best_route, best_total

    def _solve_exact(
        self,
        nodes: list[ResolvedPlace],
        matrix: dict[tuple[str, str], int],
    ) -> tuple[list[int], int]:
        resort_count = len(nodes) - 1
        full_mask = (1 << resort_count) - 1
        dp: dict[tuple[int, int], int] = {}
        parent: dict[tuple[int, int], int] = {}

        for resort_index in range(1, resort_count + 1):
            mask = 1 << (resort_index - 1)
            dp[(mask, resort_index)] = self._distance(0, resort_index, nodes, matrix)
            parent[(mask, resort_index)] = 0

        for mask in range(1, full_mask + 1):
            for end_index in range(1, resort_count + 1):
                if not self._contains(mask, end_index):
                    continue
                previous_mask = mask ^ (1 << (end_index - 1))
                if previous_mask == 0:
                    continue

                best_cost = None
                best_prev = None
                for previous_index in range(1, resort_count + 1):
                    if not self._contains(previous_mask, previous_index):
                        continue
                    candidate_cost = (
                        dp[(previous_mask, previous_index)]
                        + self._distance(previous_index, end_index, nodes, matrix)
                    )
                    if best_cost is None or candidate_cost < best_cost:
                        best_cost = candidate_cost
                        best_prev = previous_index

                dp[(mask, end_index)] = best_cost
                parent[(mask, end_index)] = best_prev

        best_total = None
        best_last = None
        for end_index in range(1, resort_count + 1):
            candidate_total = (
                dp[(full_mask, end_index)]
                + self._distance(end_index, 0, nodes, matrix)
            )
            if best_total is None or candidate_total < best_total:
                best_total = candidate_total
                best_last = end_index

        route = [0]
        reverse_resorts: list[int] = []
        mask = full_mask
        current = best_last
        while current is not None and current != 0:
            reverse_resorts.append(current)
            previous = parent[(mask, current)]
            mask ^= 1 << (current - 1)
            current = previous

        route.extend(reversed(reverse_resorts))
        route.append(0)
        return route, best_total

    def _solve_nearest_neighbor(
        self,
        nodes: list[ResolvedPlace],
        matrix: dict[tuple[str, str], int],
    ) -> tuple[list[int], int]:
        remaining = set(range(1, len(nodes)))
        current = 0
        route = [0]
        total_seconds = 0

        while remaining:
            next_index = min(
                remaining,
                key=lambda candidate: self._distance(current, candidate, nodes, matrix),
            )
            total_seconds += self._distance(current, next_index, nodes, matrix)
            route.append(next_index)
            current = next_index
            remaining.remove(next_index)

        total_seconds += self._distance(current, 0, nodes, matrix)
        route.append(0)
        return route, total_seconds

    def _contains(self, mask: int, resort_index: int) -> bool:
        return bool(mask & (1 << (resort_index - 1)))

    def _distance(
        self,
        from_index: int,
        to_index: int,
        nodes: list[ResolvedPlace],
        matrix: dict[tuple[str, str], int],
    ) -> int:
        key = (nodes[from_index].place_id, nodes[to_index].place_id)
        if key not in matrix:
            raise ValueError(f"Missing route duration for pair {key}")
        return matrix[key]


def build_ski_trip_planner(
    *,
    maps_api_key: str | None = None,
    places_api_key: str | None = None,
    routes_api_key: str | None = None,
    exact_solver_limit: int = 12,
) -> SkiTripPlanner:
    place_lookup, route_matrix = build_google_ski_trip_clients(
        maps_api_key=maps_api_key,
        places_api_key=places_api_key,
        routes_api_key=routes_api_key,
    )
    return SkiTripPlanner(
        place_lookup=place_lookup,
        route_matrix=route_matrix,
        exact_solver_limit=exact_solver_limit,
    )
