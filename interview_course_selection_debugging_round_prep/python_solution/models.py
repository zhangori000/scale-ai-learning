from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Contributor:
    name: str
    completed_courses: frozenset[str]


@dataclass(frozen=True)
class Project:
    name: str
    priority: int
    headcount: int
    required_courses: frozenset[str]

    @property
    def is_simple(self) -> bool:
        return not self.required_courses
