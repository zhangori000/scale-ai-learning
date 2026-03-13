from __future__ import annotations

import json
from datetime import date

from batch_job import PartyAnalyticsBatchJob
from party_analytics import compute_deadzones, compute_party_windows, join_party_records
from repositories import InMemoryPartyRepository, InMemoryStatsRepository


PARTY_DATA_EXAMPLE = {
    "metadata": {"source": "demo"},
    "submissions": {
        "submissionData": [
            {
                "party_id": "p1",
                "start_time": "2024-01-01T10:00:00Z",
                "end_time": "2024-01-01T13:00:00Z",
            },
            {
                "party_id": "p2",
                "start_time": "2024-01-01T11:00:00Z",
                "end_time": "2024-01-01T12:00:00Z",
            },
            {
                "party_id": "p3",
                "start_time": "2024-01-01T17:00:00Z",
                "end_time": "2024-01-01T20:00:00Z",
            },
            {
                "party_id": "p4",
                "start_time": "2024-01-01T12:00:00Z",
                "end_time": "2024-01-01T15:00:00Z",
            },
            {
                "party_id": "p5",
                "start_time": "2024-01-01T14:00:00Z",
                "end_time": "2024-01-01T18:00:00Z",
            },
        ]
    },
}


GEO_DATA_EXAMPLE = {
    "geoData": [
        {
            "party_id": "p1",
            "neighborhood": "North Beach",
            "town": "Downtown",
            "city": "San Francisco",
            "state": "CA",
        },
        {
            "party_id": "p2",
            "neighborhood": "North Beach",
            "town": "Downtown",
            "city": "San Francisco",
            "state": "CA",
        },
        {
            "party_id": "p3",
            "neighborhood": "Mission",
            "town": "Downtown",
            "city": "San Francisco",
            "state": "CA",
        },
        {
            "party_id": "p4",
            "neighborhood": "Wharf",
            "town": "Harbor",
            "city": "San Francisco",
            "state": "CA",
        },
        {
            "party_id": "p5",
            "neighborhood": "Marina",
            "town": "Harbor",
            "city": "San Francisco",
            "state": "CA",
        },
    ]
}


def main() -> None:
    print("=== Exact interview functions ===")
    prompt_windows = compute_party_windows(PARTY_DATA_EXAMPLE, GEO_DATA_EXAMPLE)
    prompt_deadzones = compute_deadzones(prompt_windows)

    print("Party windows per neighborhood:")
    print(json.dumps(prompt_windows, indent=2, sort_keys=True))
    print()

    print("Deadzone hours per town:")
    print(json.dumps(prompt_deadzones, indent=2, sort_keys=True))
    print()

    print("=== Production-style batch job ===")
    normalized_parties = join_party_records(PARTY_DATA_EXAMPLE, GEO_DATA_EXAMPLE)
    party_repository = InMemoryPartyRepository(parties=normalized_parties)
    stats_repository = InMemoryStatsRepository()
    batch_job = PartyAnalyticsBatchJob(party_repository, stats_repository)

    result = batch_job.run_for_day(date(2024, 1, 1))

    print("Persisted neighborhood windows:")
    print(json.dumps([window.as_prompt_dict() for window in result.neighborhood_windows], indent=2))
    print()

    print("Persisted town stats:")
    print(json.dumps([stat.as_dict() for stat in result.town_stats], indent=2))


if __name__ == "__main__":
    main()
