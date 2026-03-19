from __future__ import annotations

from models import Contributor, Project


def contributor_meets_requirements(contributor: Contributor, project: Project) -> bool:
    return project.required_courses.issubset(contributor.completed_courses)


def _ordered_projects(projects: list[Project]) -> list[Project]:
    indexed_projects = list(enumerate(projects))
    indexed_projects.sort(key=lambda item: (-item[1].priority, item[0]))
    return [project for _, project in indexed_projects]


def assign_projects(
    contributors: list[Contributor],
    projects: list[Project],
    *,
    simple_only: bool = False,
) -> dict[str, dict[str, list[str]]]:
    assigned_contributor_indexes: set[int] = set()
    project_assignments: dict[str, list[str]] = {}

    for project in _ordered_projects(projects):
        if simple_only and not project.is_simple:
            continue

        members: list[str] = []
        for contributor_index, contributor in enumerate(contributors):
            if contributor_index in assigned_contributor_indexes:
                continue
            if not contributor_meets_requirements(contributor, project):
                continue

            members.append(contributor.name)
            assigned_contributor_indexes.add(contributor_index)

            if len(members) == project.headcount:
                break

        project_assignments[project.name] = members

    return {"project_assignments": project_assignments}


def assign_simple_projects(
    contributors: list[Contributor],
    projects: list[Project],
) -> dict[str, dict[str, list[str]]]:
    return assign_projects(contributors, projects, simple_only=True)


def assign_all_projects(
    contributors: list[Contributor],
    projects: list[Project],
) -> dict[str, dict[str, list[str]]]:
    return assign_projects(contributors, projects, simple_only=False)


def _score_assignments(
    assignments: dict[str, list[str]],
    projects: list[Project],
) -> tuple[int, int]:
    projects_by_name = {project.name: project for project in projects}
    fully_filled_projects = 0
    assigned_contributors = 0

    for project_name, members in assignments.items():
        assigned_contributors += len(members)
        project = projects_by_name[project_name]
        if len(members) == project.headcount:
            fully_filled_projects += 1

    return fully_filled_projects, assigned_contributors


def most_needed_course(
    contributors: list[Contributor],
    projects: list[Project],
) -> str:
    candidate_courses = sorted(
        {
            course_name
            for project in projects
            for course_name in project.required_courses
        }
    )
    if not candidate_courses:
        return ""

    best_course = candidate_courses[0]
    best_score = (-1, -1)

    for course_name in candidate_courses:
        simulated_contributors = [
            Contributor(
                name=contributor.name,
                completed_courses=frozenset(set(contributor.completed_courses) | {course_name}),
            )
            for contributor in contributors
        ]
        simulated_assignments = assign_all_projects(simulated_contributors, projects)["project_assignments"]
        score = _score_assignments(simulated_assignments, projects)
        if score > best_score:
            best_course = course_name
            best_score = score

    return best_course
