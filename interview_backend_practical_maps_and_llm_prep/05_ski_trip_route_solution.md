# Ski Trip Route Solution

## Clean problem statement

Given Joey's home address and a set of ski resort names:

1. Resolve each location to a place ID using Places API (New)
2. Compute pairwise driving times using Routes API
3. Find the round trip with minimum total driving time

This is a classic routing optimization problem.

## Part 1: Resolve place IDs

Use Places API (New) Text Search with a field mask that includes `places.id` and `places.displayName`.

For each input string:

- send a Text Search request
- take the best match
- store both the raw query and resolved place ID
- optionally keep confidence metadata for manual review if the match is ambiguous

## Part 2: Build the drive-time matrix

Once you have all place IDs, call Routes API `computeRouteMatrix`.

For `N` locations, build an `N x N` duration matrix where:

- `matrix[i][j]` is the drive time from location `i` to location `j`
- diagonal entries are zero
- matrix may be asymmetric because traffic and road network are directional

## Part 3: Optimize the route

There are three levels of answer quality here:

1. brute force
2. exact dynamic programming
3. heuristic for larger `N`

## Brute-force baseline

The pure brute-force solution is:

- generate every permutation of the resorts
- evaluate `home -> permutation -> home`
- return the minimum total drive time

If there are `n` resorts, that is `O(n!)` time.

This is often a perfectly good first interview answer because it proves correctness and matches the actual problem statement exactly. Then you improve it.

## Better exact solution

For a small number of resorts, use exact dynamic programming for the round-trip traveling salesperson problem.

State:

- start at home
- visit each resort exactly once
- return home

Held-Karp dynamic programming works well for interview:

- time complexity: `O(n^2 * 2^n)`
- space complexity: `O(n * 2^n)`

That is much better than brute force and realistic for maybe 10 to 15 resorts depending on constraints.

## Exact algorithm sketch

```text
dp[mask][j] =
  minimum travel time to start at home,
  visit resorts in mask,
  and finish at resort j
```

Transition:

```text
dp[mask][j] =
  min over i in mask without j:
    dp[mask - {j}][i] + dist[i][j]
```

Final answer:

```text
min over j:
  dp[all_resorts][j] + dist[j][home]
```

## Large-N answer

If Joey wants dozens of resorts, exact DP stops being practical. Then I would say:

- use nearest neighbor or insertion heuristic to get an initial route
- improve it with 2-opt
- or mention Routes API waypoint optimization as a platform alternative for supported cases

## Important implementation details

- Keep the place resolution step separate from route optimization.
- Cache place IDs by normalized resort name.
- Cache route matrix entries because the same place pairs are expensive to recompute.
- Treat matrix lookup failures as partial errors and surface them clearly.
- Remember this is a round trip. Home is both the first and last node.

## What is in the code

`python_solution/ski_trip_service.py` now supports:

- `strategy="bruteforce"`
- `strategy="dp"`
- `strategy="nearest_neighbor"`
- `strategy="auto"` which chooses DP for small `N` and heuristic for larger `N`

## Real adapter boundary

In this prep pack, the production-style Google code lives in:

- `python_solution/google_ski_trip_clients.py`

That file shows exactly how to:

- call Places Text Search (New) to resolve a query into a place ID
- call Routes `computeRouteMatrix` to turn place IDs into pairwise durations
- translate those raw Google responses into the simpler port contracts used by `SkiTripPlanner`

## What I would say in interview

I would split the problem into place resolution, matrix construction, and route optimization. My first correct algorithm would be brute force over all resort permutations, which is `O(n!)`. Then I would improve that to Held-Karp dynamic programming, which gives an exact answer in `O(n^2 2^n)`. If the resort count gets too large, I would switch to a heuristic or rely on built-in waypoint optimization where it fits the product requirements.
