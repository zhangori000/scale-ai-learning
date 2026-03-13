from __future__ import annotations

import unittest
from datetime import date

from batch_job import PartyAnalyticsBatchJob
from domain_models import PartyDataError
from party_analytics import (
    compute_deadzones,
    compute_party_windows,
    join_party_records,
    merge_hour_intervals,
)
from repositories import InMemoryPartyRepository, InMemoryStatsRepository


def build_party_data() -> dict:
    return {
        "metadata": {},
        "submissions": {
            "submissionData": [
                {
                    "party_id": "p1",
                    "start_time": "2024-01-01T10:00:00Z",
                    "end_time": "2024-01-01T13:00:00Z",
                },
                {
                    "party_id": "p2",
                    "start_time": "2024-01-01T16:00:00Z",
                    "end_time": "2024-01-01T20:00:00Z",
                },
                {
                    "party_id": "p3",
                    "start_time": "2024-01-01T09:00:00Z",
                    "end_time": "2024-01-01T12:00:00Z",
                },
                {
                    "party_id": "p4",
                    "start_time": "2024-01-01T14:00:00Z",
                    "end_time": "2024-01-01T17:00:00Z",
                },
                {
                    "party_id": "p5",
                    "start_time": "2024-01-01T18:00:00Z",
                    "end_time": "2024-01-01T22:00:00Z",
                },
            ]
        },
    }


def build_geo_data() -> dict:
    return {
        "geoData": [
            {
                "party_id": "p1",
                "neighborhood": "SOMA",
                "town": "SF Downtown",
                "city": "San Francisco",
                "state": "CA",
            },
            {
                "party_id": "p2",
                "neighborhood": "SOMA",
                "town": "SF Downtown",
                "city": "San Francisco",
                "state": "CA",
            },
            {
                "party_id": "p3",
                "neighborhood": "Mission",
                "town": "SF Downtown",
                "city": "San Francisco",
                "state": "CA",
            },
            {
                "party_id": "p4",
                "neighborhood": "Mission",
                "town": "SF Downtown",
                "city": "San Francisco",
                "state": "CA",
            },
            {
                "party_id": "p5",
                "neighborhood": "Sunset",
                "town": "SF West",
                "city": "San Francisco",
                "state": "CA",
            },
        ]
    }


class PartyAnalyticsTests(unittest.TestCase):
    def test_compute_party_windows_keeps_neighborhood_and_town_distinct(self) -> None:
        windows = compute_party_windows(build_party_data(), build_geo_data())

        self.assertEqual(
            windows,
            {
                "SOMA": {"start_hr": 10, "end_hr": 20, "town": "SF Downtown"},
                "Mission": {"start_hr": 9, "end_hr": 17, "town": "SF Downtown"},
                "Sunset": {"start_hr": 18, "end_hr": 22, "town": "SF West"},
            },
        )

    def test_merge_hour_intervals_merges_overlap_and_touching(self) -> None:
        merged = merge_hour_intervals([(3, 8), (5, 7), (8, 10), (13, 15)])
        self.assertEqual(merged, [(3, 10), (13, 15)])

    def test_compute_deadzones_sums_only_gaps_between_merged_blocks(self) -> None:
        party_windows = {
            "North Beach": {"start_hr": 10, "end_hr": 13, "town": "Downtown"},
            "Mission": {"start_hr": 17, "end_hr": 20, "town": "Downtown"},
            "Wharf": {"start_hr": 12, "end_hr": 15, "town": "Harbor"},
            "Marina": {"start_hr": 14, "end_hr": 18, "town": "Harbor"},
        }

        self.assertEqual(
            compute_deadzones(party_windows),
            {
                "Downtown": 4,
                "Harbor": 0,
            },
        )

    def test_batch_job_persists_precomputed_stats_for_a_day(self) -> None:
        normalized_parties = join_party_records(build_party_data(), build_geo_data())
        party_repository = InMemoryPartyRepository(parties=normalized_parties)
        stats_repository = InMemoryStatsRepository()
        batch_job = PartyAnalyticsBatchJob(party_repository, stats_repository)

        result = batch_job.run_for_day(date(2024, 1, 1))

        self.assertEqual(len(result.neighborhood_windows), 3)
        self.assertEqual(len(result.town_stats), 2)

        sf_downtown_stats = stats_repository.get_town_deadzone_stats(
            date(2024, 1, 1), "SF Downtown"
        )
        sf_west_stats = stats_repository.get_town_deadzone_stats(
            date(2024, 1, 1), "SF West"
        )

        self.assertIsNotNone(sf_downtown_stats)
        self.assertIsNotNone(sf_west_stats)
        self.assertEqual(sf_downtown_stats.deadzone_hours, 0)
        self.assertEqual(sf_downtown_stats.merged_intervals, ((9, 20),))
        self.assertEqual(sf_west_stats.deadzone_hours, 0)
        self.assertEqual(sf_west_stats.merged_intervals, ((18, 22),))

    def test_same_neighborhood_name_in_two_towns_raises(self) -> None:
        geo_data = build_geo_data()
        geo_data["geoData"][1] = {
            "party_id": "p2",
            "neighborhood": "SOMA",
            "town": "Different Town",
            "city": "San Francisco",
            "state": "CA",
        }

        with self.assertRaises(PartyDataError):
            compute_party_windows(build_party_data(), geo_data)


if __name__ == "__main__":
    unittest.main()
