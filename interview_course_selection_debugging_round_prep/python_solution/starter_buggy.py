from __future__ import annotations

from models import Contributor, Project


def contributor_meets_requirements(contributor: Contributor, project: Project) -> bool:
    if not project.required_courses:
        return True
    return any(course in contributor.completed_courses for course in project.required_courses)


def assign_projects(
    contributors: list[Contributor],
    projects: list[Project],
    *,
    simple_only: bool = False,
) -> dict[str, dict[str, list[str]]]:
    project_assignments: dict[str, list[str]] = {}

    for project in sorted(projects, key=lambda project: project.priority):
        if simple_only and not project.is_simple:
            continue

        assigned_contributor_indexes: set[int] = set()
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

    augmented_contributors = contributors
    best_course = candidate_courses[0]
    best_assigned_count = -1

    for course_name in candidate_courses:
        augmented_contributors = [
            Contributor(
                name=contributor.name,
                completed_courses=frozenset(set(contributor.completed_courses) | {course_name}),
            )
            for contributor in augmented_contributors
        ]
        assignments = assign_all_projects(augmented_contributors, projects)["project_assignments"]
        assigned_count = sum(len(members) for members in assignments.values())
        if assigned_count > best_assigned_count:
            best_assigned_count = assigned_count
            best_course = course_name

    return best_course
