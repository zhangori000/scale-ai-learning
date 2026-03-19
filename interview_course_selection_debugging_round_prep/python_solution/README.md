# Python Reference Implementation

This folder contains a runnable practice version of the reconstructed debugging round.

## Files

- `models.py`
  - data classes for contributors and projects
- `csv_loader.py`
  - loads normalized CSV files from `sample_data/`
- `assignment_service.py`
  - fixed reference implementation
- `starter_buggy.py`
  - intentionally broken practice version
- `test_assignment_service.py`
  - unit tests, including the 3 reconstructed behaviors
- `demo.py`
  - prints assignments and the most needed course

## Sample CSV layout

- `contributors.csv`
- `contributor_courses.csv`
- `projects.csv`
- `project_prerequisites.csv`

This mirrors the "multiple python files and csv files" shape you described.

## Run

```bash
python demo.py
python -m unittest test_assignment_service.py -v
```

## Practice flow

1. Read `starter_buggy.py` first.
2. Try to predict which tests fail and why.
3. Compare against `assignment_service.py`.
4. Run the tests until you can explain each invariant from memory.
