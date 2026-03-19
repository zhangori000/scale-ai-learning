# Course Selection Debugging Round Prep

This folder is a reconstructed practice pack for the CSV-driven "debugging round" you described.

It is not a verbatim copy of the original prompt. It is a best-effort reconstruction from the test behavior you posted:

- assign contributors to projects
- respect prerequisite courses
- enforce one-project-per-contributor
- process projects by descending priority
- keep contributor order fixed
- identify the most needed course by simulation

## Files

- `01_reconstructed_prompt.md`
  - likely problem statement, hidden-test contract, and assumptions
- `02_debugging_playbook.md`
  - how to reason through the round under interview pressure
- `python_solution/`
  - runnable reference implementation
  - sample CSV files
  - a deliberately buggy starter for practice
  - unit tests mirroring the 3 behaviors you described

## Suggested study order

1. Read `01_reconstructed_prompt.md`
2. Read `02_debugging_playbook.md`
3. Open `python_solution/starter_buggy.py`
4. Compare it with `python_solution/assignment_service.py`
5. Run `python -m unittest test_assignment_service.py -v`

## Quick run

From `python_solution/`:

```bash
python demo.py
python -m unittest test_assignment_service.py -v
```
