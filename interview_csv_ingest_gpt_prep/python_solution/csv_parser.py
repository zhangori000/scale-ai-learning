from __future__ import annotations

import csv
import io
from typing import Iterable

from models import TaskRecord, UserRecord


class CSVValidationError(ValueError):
    pass


def _require_headers(actual: Iterable[str], required: list[str], file_label: str) -> None:
    actual_set = {h.strip() for h in actual if h is not None}
    missing = [h for h in required if h not in actual_set]
    if missing:
        raise CSVValidationError(
            f"{file_label}: missing required columns: {', '.join(missing)}"
        )


def parse_users_csv(content: bytes, encoding: str = "utf-8") -> tuple[list[UserRecord], list[str]]:
    stream = io.StringIO(content.decode(encoding))
    reader = csv.DictReader(stream)
    if reader.fieldnames is None:
        raise CSVValidationError("users_file: CSV header missing")
    _require_headers(reader.fieldnames, ["user_id", "name", "email"], "users_file")

    users: list[UserRecord] = []
    errors: list[str] = []
    for row_num, row in enumerate(reader, start=2):
        user_id = (row.get("user_id") or "").strip()
        name = (row.get("name") or "").strip()
        email = (row.get("email") or "").strip()
        if not user_id:
            errors.append(f"users_file row {row_num}: user_id is empty")
            continue
        if not name:
            errors.append(f"users_file row {row_num}: name is empty")
            continue
        if "@" not in email:
            errors.append(f"users_file row {row_num}: email looks invalid")
            continue
        users.append(UserRecord(user_id=user_id, name=name, email=email))
    return users, errors


def parse_tasks_csv(
    content: bytes,
    encoding: str = "utf-8",
    max_description_len: int = 4000,
) -> tuple[list[TaskRecord], list[str]]:
    stream = io.StringIO(content.decode(encoding))
    reader = csv.DictReader(stream)
    if reader.fieldnames is None:
        raise CSVValidationError("tasks_file: CSV header missing")
    _require_headers(reader.fieldnames, ["task_id", "user_id", "description"], "tasks_file")

    tasks: list[TaskRecord] = []
    errors: list[str] = []
    for row_num, row in enumerate(reader, start=2):
        task_id = (row.get("task_id") or "").strip()
        user_id = (row.get("user_id") or "").strip()
        description = (row.get("description") or "").strip()
        if not task_id:
            errors.append(f"tasks_file row {row_num}: task_id is empty")
            continue
        if not user_id:
            errors.append(f"tasks_file row {row_num}: user_id is empty")
            continue
        if not description:
            errors.append(f"tasks_file row {row_num}: description is empty")
            continue
        if len(description) > max_description_len:
            errors.append(
                f"tasks_file row {row_num}: description too long ({len(description)} chars)"
            )
            continue
        tasks.append(TaskRecord(task_id=task_id, user_id=user_id, description=description))
    return tasks, errors
