# Reconstructed Prompt

Below is the most likely version of the round based on the test descriptions you posted.

## Problem shape

You are given multiple Python files and multiple CSV files.

The system models:

- contributors (or students)
- projects (or course opportunities)
- courses each contributor has completed
- prerequisite courses required by each project

Some helper functions may already be marked as correct. Your job is to debug the remaining logic so the hidden tests pass.

## Core rules inferred from the tests

### Assignment rules

- A contributor can be assigned to at most one project.
- A project cannot exceed its headcount.
- Contributors are considered in the exact order they appear in the input.
- Projects are processed in descending priority order.
- A contributor can join a project only if they have completed all required prerequisite courses.

### Test 1: Simple Projects Assignment

Only assign contributors to simple projects:

- simple project = a project with no required prerequisite courses
- projects still follow descending priority order
- contributors still follow fixed input order
- each contributor can only appear once

Expected output shape is likely:

```python
{
    "project_assignments": {
        "Tangerine Jubilant": ["..."],
        "Galaxy Velvet": ["..."],
    }
}
```

### Test 2: All Projects Assignment

Assign contributors across all projects:

- same project ordering
- same contributor ordering
- same single-assignment rule
- prerequisite check must require all courses, not any course

The hidden test likely compares your final dictionary exactly against an expected value.

### Test 3: Most Needed Course

Find the course name such that:

- if every contributor were assumed to have completed that single course
- then, after re-running assignment across all projects
- the result would maximize project fill and contributor placement

## Important inference for Test 3

The prompt wording is slightly ambiguous.

The safest interpretation is:

1. simulate each candidate course independently
2. re-run assignment from a fresh state each time
3. score the result by:
   - number of fully filled projects
   - then number of assigned contributors
4. return the best course name

If there is a tie, use a deterministic rule such as alphabetical order.

## Likely hidden bug categories

- sorting priorities ascending instead of descending
- forgetting contributor order must remain fixed
- reusing contributors across projects
- ignoring headcount
- checking prerequisite overlap with `any(...)` instead of `all(...)`
- mutating state between repeated simulations in the "most needed course" function
- including the wrong candidate course set for simulation

## Mental translation if entity names differ

The original round may talk about students and course selection.

The tests you posted talk about contributors and projects.

Treat them as the same shape:

- student == contributor
- project/opportunity == course selection target
- completed classes == completed prerequisite courses

The algorithmic core is unchanged.
