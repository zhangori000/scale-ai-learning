from __future__ import annotations

import json
from pathlib import Path

from assignment_service import assign_all_projects, assign_simple_projects, most_needed_course
from csv_loader import load_dataset


def main() -> None:
    data_dir = Path(__file__).parent / "sample_data"
    contributors, projects = load_dataset(data_dir)

    print("Simple projects:")
    print(json.dumps(assign_simple_projects(contributors, projects), indent=2))
    print()

    print("All projects:")
    print(json.dumps(assign_all_projects(contributors, projects), indent=2))
    print()

    print("Most needed course:")
    print(most_needed_course(contributors, projects))


if __name__ == "__main__":
    main()
