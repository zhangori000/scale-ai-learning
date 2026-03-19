from __future__ import annotations

import unittest

from fake_adapters import StaticPlaceLookup, StaticRouteMatrix
from models import ResolvedPlace
from ski_trip_service import SkiTripPlanner


class SkiTripPlannerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.home = ResolvedPlace("Home", "home", "Joey's Home")
        self.resort_a = ResolvedPlace("Resort A", "a", "Resort A")
        self.resort_b = ResolvedPlace("Resort B", "b", "Resort B")
        self.resort_c = ResolvedPlace("Resort C", "c", "Resort C")

        self.lookup = StaticPlaceLookup(
            {
                "Home": self.home,
                "Resort A": self.resort_a,
                "Resort B": self.resort_b,
                "Resort C": self.resort_c,
            }
        )
        self.matrix = StaticRouteMatrix(
            {
                ("home", "a"): 10,
                ("home", "b"): 18,
                ("home", "c"): 25,
                ("a", "home"): 10,
                ("b", "home"): 18,
                ("c", "home"): 25,
                ("a", "b"): 14,
                ("b", "a"): 14,
                ("a", "c"): 35,
                ("c", "a"): 9,
                ("b", "c"): 12,
                ("c", "b"): 12,
            }
        )

    def test_plan_trip_uses_exact_dynamic_programming(self) -> None:
        planner = SkiTripPlanner(self.lookup, self.matrix)
        plan = planner.plan_trip("Home", ["Resort A", "Resort B", "Resort C"])

        self.assertEqual(plan.algorithm, "exact_dp")
        self.assertEqual(
            plan.display_route(),
            ["Joey's Home", "Resort B", "Resort C", "Resort A", "Joey's Home"],
        )
        self.assertEqual(plan.total_drive_seconds, 49)

    def test_plan_trip_can_use_bruteforce(self) -> None:
        planner = SkiTripPlanner(self.lookup, self.matrix)
        plan = planner.plan_trip(
            "Home",
            ["Resort A", "Resort B", "Resort C"],
            strategy="bruteforce",
        )

        self.assertEqual(plan.algorithm, "exact_bruteforce")
        self.assertEqual(
            plan.display_route(),
            ["Joey's Home", "Resort B", "Resort C", "Resort A", "Joey's Home"],
        )
        self.assertEqual(plan.total_drive_seconds, 49)

    def test_plan_trip_uses_nearest_neighbor_after_limit(self) -> None:
        planner = SkiTripPlanner(self.lookup, self.matrix, exact_solver_limit=2)
        plan = planner.plan_trip("Home", ["Resort A", "Resort B", "Resort C"])

        self.assertEqual(plan.algorithm, "nearest_neighbor")
        self.assertEqual(
            plan.display_route(),
            ["Joey's Home", "Resort A", "Resort B", "Resort C", "Joey's Home"],
        )
        self.assertEqual(plan.total_drive_seconds, 61)

    def test_empty_resort_list_returns_home_to_home(self) -> None:
        planner = SkiTripPlanner(self.lookup, self.matrix)
        plan = planner.plan_trip("Home", [])

        self.assertEqual(plan.display_route(), ["Joey's Home", "Joey's Home"])
        self.assertEqual(plan.total_drive_seconds, 0)


if __name__ == "__main__":
    unittest.main()
