# 01 Problem Statement

## The real problem

A large org has many teams and many internal APIs. Different teams hit roughly
the same core endpoints, but each team has a slightly different test setup and a
slightly different question:

- "How fast is `POST /post` after I provision accounts?"
- "How does end-of-day behave after a large batch of writes?"
- "What happens if I preload state first, then measure a read-heavy phase?"

Without a shared platform, every team builds one-off load tests. That leads to:

- duplicated scripts
- inconsistent test methodology
- poor comparability across teams
- unsafe tests that hammer shared staging resources
- unclear ownership for cost spikes and congestion

## Product goal

Build a shared performance-testing platform where teams can define reusable,
governed scenarios instead of hand-writing raw load tests.

## Functional requirements

1. Register endpoints, environments, and scenario templates.
2. Support ordered multi-step flows such as `Provision -> Post -> EndOfDay`.
3. Support an optional `setup` phase before the measured phase.
4. Allow multiple measured endpoints in one run.
5. Let users configure request count, concurrency, arrival model, and limits.
6. Produce reports per endpoint and per scenario phase.

## Non-functional requirements

1. Do not let the test platform become the bottleneck.
2. Do not let one team's run congest the entire shared org environment.
3. Bound downstream write amplification and cloud cost.
4. Make runs reproducible and comparable.
5. Make the model simple enough for non-experts to use safely.

## The key conceptual split

This system has three separate jobs:

1. Describe the test plan.
2. Execute the load accurately.
3. Protect shared infrastructure from unsafe tests.

Teams often focus only on job 2. In practice, jobs 1 and 3 are the harder
system design problems.

## The first important opinion

For stateful internal APIs, performance testing is usually closer to
"business-transaction simulation" than to "blind packet spraying."

That means the unit of design should often be:

- a business step
- with ordering
- with state dependencies
- with measurement rules

not just:

- a URL
- a thread count
- a duration

That distinction explains why your old team cared so much about exact request
counts.
