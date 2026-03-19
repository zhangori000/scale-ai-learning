from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from models import Contributor, Project


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]


def load_contributors(data_dir: str | Path) -> list[Contributor]:
    data_path = Path(data_dir)
    contributors_rows = _read_csv_rows(data_path / "contributors.csv")
    course_rows = _read_csv_rows(data_path / "contributor_courses.csv")

    courses_by_contributor_id: dict[str, set[str]] = defaultdict(set)
    for row in course_rows:
        contributor_id = row["contributor_id"]
        course_name = row["course_name"]
        if contributor_id and course_name:
            courses_by_contributor_id[contributor_id].add(course_name)

    contributors: list[Contributor] = []
    for row in contributors_rows:
        contributor_id = row["contributor_id"]
        name = row["name"]
        contributors.append(
            Contributor(
                name=name,
                completed_courses=frozenset(courses_by_contributor_id.get(contributor_id, set())),
            )
        )
    return contributors


def load_projects(data_dir: str | Path) -> list[Project]:
    data_path = Path(data_dir)
    project_rows = _read_csv_rows(data_path / "projects.csv")
    prerequisite_rows = _read_csv_rows(data_path / "project_prerequisites.csv")

    prerequisites_by_project_id: dict[str, set[str]] = defaultdict(set)
    for row in prerequisite_rows:
        project_id = row["project_id"]
        course_name = row["course_name"]
        if project_id and course_name:
            prerequisites_by_project_id[project_id].add(course_name)

    projects: list[Project] = []
    for row in project_rows:
        project_id = row["project_id"]
        projects.append(
            Project(
                name=row["name"],
                priority=int(row["priority"]),
                headcount=int(row["headcount"]),
                required_courses=frozenset(prerequisites_by_project_id.get(project_id, set())),
            )
        )
    return projects


def load_dataset(data_dir: str | Path) -> tuple[list[Contributor], list[Project]]:
    return load_contributors(data_dir), load_projects(data_dir)
