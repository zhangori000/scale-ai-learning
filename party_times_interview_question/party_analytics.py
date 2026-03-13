from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping

from domain_models import (
    GeoRecord,
    NeighborhoodWindow,
    PartyDataError,
    PartyOccurrence,
    TownDeadzoneStats,
    parse_timestamp,
)


def _build_geo_index(geo_data: Mapping[str, Any], *, strict: bool) -> dict[str, GeoRecord]:
    """
    Build `party_id -> GeoRecord` so the time payload can be joined with location.

    The prompt gives us two separate JSON blobs. This is the join step that turns
    them into one normalized party stream.
    """

    party_id_to_geo: dict[str, GeoRecord] = {}

    for raw_geo in geo_data.get("geoData", []):
        try:
            geo = GeoRecord(
                party_id=raw_geo["party_id"],
                neighborhood_name=raw_geo["neighborhood"],
                town_name=raw_geo["town"],
                city=raw_geo["city"],
                state=raw_geo["state"],
            )
        except KeyError as exc:
            raise PartyDataError(f"Geo record is missing required field: {exc.args[0]}") from exc

        if geo.party_id in party_id_to_geo and strict:
            raise PartyDataError(f"Duplicate geo record for party_id={geo.party_id!r}")

        party_id_to_geo[geo.party_id] = geo

    return party_id_to_geo


def join_party_records(
    party_data: Mapping[str, Any],
    geo_data: Mapping[str, Any],
    *,
    strict: bool = True,
) -> list[PartyOccurrence]:
    """
    Normalize the two prompt payloads into typed party records.

    `strict=True` is the production-safe default:
    - missing geo rows raise
    - duplicate geo rows raise
    - negative-duration or cross-day rows raise

    If you want a more forgiving interview-style version, pass `strict=False` and
    malformed rows will be skipped when possible.
    """

    geo_index = _build_geo_index(geo_data, strict=strict)
    parties: list[PartyOccurrence] = []

    raw_submissions = party_data.get("submissions", {}).get("submissionData", [])
    for raw_submission in raw_submissions:
        try:
            party_id = raw_submission["party_id"]
            start_time = parse_timestamp(raw_submission["start_time"])
            end_time = parse_timestamp(raw_submission["end_time"])
        except KeyError as exc:
            raise PartyDataError(
                f"Submission record is missing required field: {exc.args[0]}"
            ) from exc

        geo = geo_index.get(party_id)
        if geo is None:
            if strict:
                raise PartyDataError(f"Missing geo record for party_id={party_id!r}")
            continue

        if end_time < start_time:
            raise PartyDataError(
                f"Party {party_id!r} ends before it starts: {start_time} -> {end_time}"
            )

        # The interview problem treats each party as a same-day hourly interval.
        # In a real pipeline, a cross-day party would be split into per-day slices
        # before aggregation.
        if start_time.date() != end_time.date():
            raise PartyDataError(
                f"Party {party_id!r} crosses a day boundary and must be split upstream"
            )

        parties.append(
            PartyOccurrence(
                party_id=party_id,
                neighborhood_name=geo.neighborhood_name,
                town_name=geo.town_name,
                city=geo.city,
                state=geo.state,
                start_time=start_time,
                end_time=end_time,
            )
        )

    return parties


def compute_neighborhood_party_windows(
    parties: Iterable[PartyOccurrence],
) -> dict[str, NeighborhoodWindow]:
    """
    Aggregate normalized parties into one window per neighborhood.

    Important hierarchy rule:
    - many parties -> one neighborhood window
    - many neighborhood windows -> one town dead-zone result
    """

    windows: dict[str, NeighborhoodWindow] = {}

    for party in parties:
        existing = windows.get(party.neighborhood_name)
        if existing is None:
            windows[party.neighborhood_name] = NeighborhoodWindow(
                neighborhood_name=party.neighborhood_name,
                town_name=party.town_name,
                start_hour=party.start_hour,
                end_hour=party.end_hour,
            )
            continue

        if existing.town_name != party.town_name:
            raise PartyDataError(
                "Neighborhood name maps to multiple towns; use stable neighborhood IDs "
                "in production if duplicate names are possible."
            )

        windows[party.neighborhood_name] = NeighborhoodWindow(
            neighborhood_name=existing.neighborhood_name,
            town_name=existing.town_name,
            start_hour=min(existing.start_hour, party.start_hour),
            end_hour=max(existing.end_hour, party.end_hour),
        )

    return windows


def compute_party_windows(
    party_data: Mapping[str, Any],
    geo_data: Mapping[str, Any],
    *,
    strict: bool = True,
) -> dict[str, dict[str, object]]:
    """
    Exact prompt-friendly Part 1 function.

    Return shape:
    {
        "<neighborhood>": {
            "start_hr": <int>,
            "end_hr": <int>,
            "town": "<town>"
        }
    }
    """

    parties = join_party_records(party_data, geo_data, strict=strict)
    windows = compute_neighborhood_party_windows(parties)
    return {
        neighborhood_name: window.as_prompt_dict()
        for neighborhood_name, window in windows.items()
    }


def merge_hour_intervals(intervals: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    """
    Merge overlapping or touching hour intervals.

    Touching intervals such as `(10, 12)` and `(12, 14)` are treated as one
    continuous block, so they do not create a dead zone.
    """

    ordered = sorted(intervals, key=lambda interval: interval[0])
    if not ordered:
        return []

    for start_hour, end_hour in ordered:
        if start_hour > end_hour:
            raise PartyDataError(
                f"Invalid interval with start after end: ({start_hour}, {end_hour})"
            )

    merged: list[tuple[int, int]] = [ordered[0]]

    for current_start, current_end in ordered[1:]:
        last_start, last_end = merged[-1]
        if current_start <= last_end:
            merged[-1] = (last_start, max(last_end, current_end))
        else:
            merged.append((current_start, current_end))

    return merged


def compute_town_deadzone_stats(
    windows: Iterable[NeighborhoodWindow],
) -> dict[str, TownDeadzoneStats]:
    """
    Compute town-level dead-zone statistics from neighborhood windows.

    Town logic:
    - collect all neighborhood windows in the same town
    - merge the intervals
    - sum gaps between consecutive merged blocks
    """

    town_to_intervals: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for window in windows:
        town_to_intervals[window.town_name].append((window.start_hour, window.end_hour))

    results: dict[str, TownDeadzoneStats] = {}
    for town_name, intervals in town_to_intervals.items():
        merged = merge_hour_intervals(intervals)
        deadzone_hours = 0

        for index in range(1, len(merged)):
            previous_end = merged[index - 1][1]
            current_start = merged[index][0]
            deadzone_hours += current_start - previous_end

        first_party_hour = merged[0][0] if merged else None
        last_party_hour = merged[-1][1] if merged else None

        results[town_name] = TownDeadzoneStats(
            town_name=town_name,
            deadzone_hours=deadzone_hours,
            merged_intervals=tuple(merged),
            first_party_hour=first_party_hour,
            last_party_hour=last_party_hour,
        )

    return results


def compute_deadzones(
    party_windows: Mapping[str, Mapping[str, Any]],
) -> dict[str, int]:
    """
    Exact prompt-friendly Part 2 function.

    Input:
    {
        "<neighborhood>": {"start_hr": 10, "end_hr": 20, "town": "SF Downtown"},
        ...
    }

    Output:
    {
        "<town>": <deadzone_hours>,
        ...
    }
    """

    windows: list[NeighborhoodWindow] = []

    for neighborhood_name, info in party_windows.items():
        try:
            windows.append(
                NeighborhoodWindow(
                    neighborhood_name=neighborhood_name,
                    town_name=str(info["town"]),
                    start_hour=int(info["start_hr"]),
                    end_hour=int(info["end_hr"]),
                )
            )
        except KeyError as exc:
            raise PartyDataError(
                f"Party window is missing required field: {exc.args[0]}"
            ) from exc

    town_stats = compute_town_deadzone_stats(windows)
    return {
        town_name: stats.deadzone_hours
        for town_name, stats in town_stats.items()
    }
