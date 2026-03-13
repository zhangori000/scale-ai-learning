from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone


class PartyDataError(ValueError):
    """Raised when the raw payload cannot be normalized safely."""


def parse_timestamp(timestamp_text: str) -> datetime:
    """
    Parse ISO-8601 timestamps such as '2024-01-01T10:00:00Z'.

    The interview prompt treats all parties as same-day hourly intervals. We keep
    timestamps timezone-aware in UTC so downstream grouping stays deterministic.
    """

    normalized = timestamp_text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise PartyDataError(f"Invalid timestamp: {timestamp_text!r}") from exc

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class GeoRecord:
    """
    Denormalized location data from the interview payload.

    In production, `neighborhood` and `town` would usually be separate tables with
    stable IDs. The interview payload repeats both names on every party row.
    """

    party_id: str
    neighborhood_name: str
    town_name: str
    city: str
    state: str


@dataclass(frozen=True, slots=True)
class PartyOccurrence:
    """
    A normalized party record joined with its geographic hierarchy.

    A party belongs to exactly one neighborhood. A neighborhood belongs to exactly
    one town. That is why each party carries both names after normalization.
    """

    party_id: str
    neighborhood_name: str
    town_name: str
    city: str
    state: str
    start_time: datetime
    end_time: datetime

    @property
    def service_day(self) -> date:
        return self.start_time.date()

    @property
    def start_hour(self) -> int:
        return self.start_time.hour

    @property
    def end_hour(self) -> int:
        return self.end_time.hour


@dataclass(frozen=True, slots=True)
class NeighborhoodWindow:
    """
    Part 1 output at neighborhood granularity.

    This is the smallest aggregated unit in the exercise. The window belongs to a
    neighborhood, and the neighborhood also carries its parent town.
    """

    neighborhood_name: str
    town_name: str
    start_hour: int
    end_hour: int

    def as_prompt_dict(self) -> dict[str, object]:
        return {
            "start_hr": self.start_hour,
            "end_hr": self.end_hour,
            "town": self.town_name,
        }


@dataclass(frozen=True, slots=True)
class TownDeadzoneStats:
    """
    Part 2 output at town granularity.

    A town contains multiple neighborhood windows. We merge those windows and only
    count the gaps between merged blocks as dead-zone hours.
    """

    town_name: str
    deadzone_hours: int
    merged_intervals: tuple[tuple[int, int], ...]
    first_party_hour: int | None
    last_party_hour: int | None

    def as_dict(self) -> dict[str, object]:
        return {
            "town": self.town_name,
            "deadzone_hours": self.deadzone_hours,
            "merged_intervals": list(self.merged_intervals),
            "first_party_hour": self.first_party_hour,
            "last_party_hour": self.last_party_hour,
        }
