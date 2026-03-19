# Debugging Playbook

This is the way to attack the round if you are dropped into a half-broken codebase.

## First principle

Do not start by rewriting everything.

These rounds often hide only 2-4 logic bugs inside otherwise usable parsing and model code.

Read for invariants first.

## Invariants to write down immediately

- project order is descending priority
- contributor order is fixed input order
- one contributor can appear in at most one project
- project assignment count cannot exceed headcount
- prerequisites require full set inclusion
- each "most needed course" simulation must start from clean state

If any function violates one of those, it is probably the bug.

## Fast debug sequence

1. Find the function that loads contributors and projects from CSV.
2. Confirm row order is preserved and not converted into an unordered structure too early.
3. Find the main assignment loop.
4. Check where the "already assigned" state is stored.
5. Check the prerequisite predicate carefully.
6. Find the "most needed course" function and confirm it simulates from fresh copies.

## What usually goes wrong

### Bug 1: Wrong project sort direction

Broken:

```python
sorted(projects, key=lambda project: project.priority)
```

Correct:

```python
sorted(projects, key=lambda project: project.priority, reverse=True)
```

### Bug 2: Reinitializing assigned contributors per project

Broken pattern:

```python
for project in projects:
    assigned = set()
```

That allows the same contributor to get reused on later projects.

The assignment-tracking structure must live outside the project loop.

### Bug 3: Using `any` instead of `all`

Broken:

```python
any(course in contributor.completed_courses for course in project.required_courses)
```

Correct:

```python
all(course in contributor.completed_courses for course in project.required_courses)
```

Or more cleanly:

```python
project.required_courses.issubset(contributor.completed_courses)
```

### Bug 4: State leakage in course simulation

This is the most common hidden failure in Test 3.

If you simulate one candidate course and then reuse mutated contributor objects for the next candidate, later candidates inherit earlier fake courses and the answer becomes nonsense.

Each candidate course needs:

- a fresh contributor list
- a fresh assignment run
- a fresh score calculation

## Safe implementation strategy

Use a simple greedy pass. Do not over-optimize.

For each project in sorted order:

1. create an empty assignment list for that project
2. scan contributors from first to last
3. skip anyone already assigned
4. skip anyone missing required courses
5. assign until headcount is reached

That matches the hidden test language exactly.

## What to say if asked why your solution is correct

Use this script:

1. "I preserved the two ordering constraints explicitly: project priority order and contributor input order."
2. "I track assigned contributors globally so nobody is reused."
3. "Eligibility is set inclusion: a contributor must satisfy all prerequisite courses."
4. "For the most-needed-course calculation I re-simulate from clean state per candidate to avoid leakage between runs."

## What not to do in interview

- do not optimize before the logic is correct
- do not replace ordered lists with sets where order matters
- do not mutate input objects in-place unless the codebase already depends on that
- do not guess that partially matching prerequisites are acceptable

## Practical fallback if the codebase is messy

If imports and CSV plumbing are noisy, isolate the core:

- extract `assign_projects(contributors, projects)`
- write one tiny local test fixture in memory
- make that pass first
- then reconnect it to the CSV layer

That usually wins these debugging rounds faster than trying to reason about the whole repository at once.
