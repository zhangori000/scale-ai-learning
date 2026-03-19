from __future__ import annotations

import csv
import io

from models import TaskRecord, UserRecord


class CSVValidationError(ValueError):
    pass


def parse_users_csv(csv_bytes: bytes) -> list[UserRecord]:
    rows = _parse_rows(csv_bytes, required_columns={"id", "name"})
    records: list[UserRecord] = []
    for index, row in enumerate(rows):
        records.append(
            UserRecord(
                row_index=index,
                id=row["id"].strip(),
                name=row["name"].strip(),
            )
        )
    return records


def parse_tasks_csv(csv_bytes: bytes) -> list[TaskRecord]:
    rows = _parse_rows(csv_bytes, required_columns={"id", "task"})
    records: list[TaskRecord] = []
    for index, row in enumerate(rows):
        records.append(
            TaskRecord(
                row_index=index,
                id=row["id"].strip(),
                task=row["task"].strip(),
            )
        )
    return records


def _parse_rows(
    csv_bytes: bytes,
    *,
    required_columns: set[str],
) -> list[dict[str, str]]:
    text = csv_bytes.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise CSVValidationError("CSV is missing a header row")

    observed_columns = {name.strip() for name in reader.fieldnames if name is not None}
    missing = sorted(required_columns - observed_columns)
    if missing:
        raise CSVValidationError(
            f"CSV is missing required columns: {', '.join(missing)}"
        )

    rows: list[dict[str, str]] = []
    for row in reader:
        normalized: dict[str, str] = {}
        for key, value in row.items():
            if key is None:
                continue
            normalized[key.strip()] = value or ""
        rows.append(normalized)
    return rows
