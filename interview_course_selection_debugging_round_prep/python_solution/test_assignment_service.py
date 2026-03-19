from __future__ import annotations

import unittest
from pathlib import Path

from assignment_service import (
    assign_all_projects,
    assign_simple_projects,
    contributor_meets_requirements,
    most_needed_course,
)
from csv_loader import load_dataset
from models import Contributor, Project


class AssignmentServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        data_dir = Path(__file__).parent / "sample_data"
        cls.contributors, cls.projects = load_dataset(data_dir)

    def test_simple_projects_assignment(self) -> None:
        result = assign_simple_projects(self.contributors, self.projects)
        self.assertEqual(
            result,
            {
                "project_assignments": {
                    "Tangerine Jubilant": ["Ava Stone", "Ben Park"],
                    "Galaxy Velvet": ["Chloe Ng", "Diego Ruiz"],
                }
            },
        )

    def test_all_projects_assignment(self) -> None:
        result = assign_all_projects(self.contributors, self.projects)
        self.assertEqual(
            result,
            {
                "project_assignments": {
                    "Tangerine Jubilant": ["Ava Stone", "Ben Park"],
                    "Galaxy Velvet": ["Chloe Ng", "Diego Ruiz"],
                    "Coral Nimbus": ["Eva Li", "Gia Tran"],
                    "Mint Aurora": [],
                    "Ivory Summit": [],
                }
            },
        )

    def test_most_needed_course(self) -> None:
        self.assertEqual(
            most_needed_course(self.contributors, self.projects),
            "Native Thai Conversation",
        )

    def test_prerequisite_check_requires_full_match(self) -> None:
        project = Project(
            name="Dual Requirement",
            priority=10,
            headcount=1,
            required_courses=frozenset({"Native Thai Conversation", "Data Ethics"}),
        )
        contributor = Contributor(
            name="Partial Match",
            completed_courses=frozenset({"Native Thai Conversation"}),
        )
        self.assertFalse(contributor_meets_requirements(contributor, project))

    def test_contributor_can_only_be_assigned_once(self) -> None:
        contributors = [
            Contributor(name="Only Candidate", completed_courses=frozenset()),
            Contributor(name="Second Candidate", completed_courses=frozenset()),
        ]
        projects = [
            Project(name="High Priority", priority=20, headcount=1, required_courses=frozenset()),
            Project(name="Lower Priority", priority=10, headcount=1, required_courses=frozenset()),
        ]

        result = assign_all_projects(contributors, projects)
        self.assertEqual(
            result["project_assignments"],
            {
                "High Priority": ["Only Candidate"],
                "Lower Priority": ["Second Candidate"],
            },
        )


if __name__ == "__main__":
    unittest.main()
