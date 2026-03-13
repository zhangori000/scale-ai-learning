from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Protocol

from domain_models import NeighborhoodWindow, PartyOccurrence, TownDeadzoneStats


class PartyRepository(Protocol):
    """Read normalized parties for a given service day."""

    def list_parties_for_day(self, service_day: date) -> list[PartyOccurrence]:
        ...


class StatsRepository(Protocol):
    """Store and read precomputed analytics so APIs do not recompute on request."""

    def upsert_neighborhood_windows(
        self,
        service_day: date,
        windows: list[NeighborhoodWindow],
    ) -> None:
        ...

    def upsert_town_deadzone_stats(
        self,
        service_day: date,
        stats: list[TownDeadzoneStats],
    ) -> None:
        ...

    def get_neighborhood_windows(self, service_day: date) -> list[NeighborhoodWindow]:
        ...

    def get_town_deadzone_stats(
        self,
        service_day: date,
        town_name: str,
    ) -> TownDeadzoneStats | None:
        ...


@dataclass
class InMemoryPartyRepository:
    """
    Test-friendly stand-in for the production party table.

    The real implementation would read from a database with filters on day and
    neighborhood/town joins.
    """

    parties: list[PartyOccurrence]

    def list_parties_for_day(self, service_day: date) -> list[PartyOccurrence]:
        return [party for party in self.parties if party.service_day == service_day]


@dataclass
class InMemoryStatsRepository:
    """
    Stores daily neighborhood and town stats keyed by service day.

    This mimics the read path you would later serve from an API.
    """

    neighborhood_windows_by_day: dict[date, dict[str, NeighborhoodWindow]] = field(
        default_factory=dict
    )
    town_stats_by_day: dict[date, dict[str, TownDeadzoneStats]] = field(
        default_factory=dict
    )

    def upsert_neighborhood_windows(
        self,
        service_day: date,
        windows: list[NeighborhoodWindow],
    ) -> None:
        self.neighborhood_windows_by_day[service_day] = {
            window.neighborhood_name: window for window in windows
        }

    def upsert_town_deadzone_stats(
        self,
        service_day: date,
        stats: list[TownDeadzoneStats],
    ) -> None:
        self.town_stats_by_day[service_day] = {
            stat.town_name: stat for stat in stats
        }

    def get_neighborhood_windows(self, service_day: date) -> list[NeighborhoodWindow]:
        return list(self.neighborhood_windows_by_day.get(service_day, {}).values())

    def get_town_deadzone_stats(
        self,
        service_day: date,
        town_name: str,
    ) -> TownDeadzoneStats | None:
        return self.town_stats_by_day.get(service_day, {}).get(town_name)
