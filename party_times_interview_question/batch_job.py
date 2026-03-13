from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from domain_models import NeighborhoodWindow, TownDeadzoneStats
from party_analytics import compute_neighborhood_party_windows, compute_town_deadzone_stats
from repositories import PartyRepository, StatsRepository


@dataclass(frozen=True, slots=True)
class BatchJobResult:
    """
    Snapshot returned by one successful batch run.

    Returning the computed data makes the job easy to inspect in tests and demos.
    """

    service_day: date
    neighborhood_windows: tuple[NeighborhoodWindow, ...]
    town_stats: tuple[TownDeadzoneStats, ...]


class PartyAnalyticsBatchJob:
    """
    Production-style orchestration for precomputing daily analytics.

    Typical schedule:
    - near-real-time runs every 5 to 15 minutes for the current day, or
    - a nightly run for the previous day, or
    - both, if the product wants fresh stats and a final daily correction pass.
    """

    def __init__(
        self,
        party_repository: PartyRepository,
        stats_repository: StatsRepository,
    ) -> None:
        self.party_repository = party_repository
        self.stats_repository = stats_repository

    def run_for_day(self, service_day: date) -> BatchJobResult:
        """
        Compute and persist neighborhood windows and town dead zones for one day.

        The write path is intentionally idempotent: rerunning the same day simply
        replaces the precomputed stats for that day.
        """

        parties = self.party_repository.list_parties_for_day(service_day)
        neighborhood_windows_by_name = compute_neighborhood_party_windows(parties)
        town_stats_by_name = compute_town_deadzone_stats(
            neighborhood_windows_by_name.values()
        )

        sorted_windows = tuple(
            sorted(
                neighborhood_windows_by_name.values(),
                key=lambda window: (window.town_name, window.neighborhood_name),
            )
        )
        sorted_town_stats = tuple(
            sorted(town_stats_by_name.values(), key=lambda stat: stat.town_name)
        )

        self.stats_repository.upsert_neighborhood_windows(service_day, list(sorted_windows))
        self.stats_repository.upsert_town_deadzone_stats(service_day, list(sorted_town_stats))

        return BatchJobResult(
            service_day=service_day,
            neighborhood_windows=sorted_windows,
            town_stats=sorted_town_stats,
        )
