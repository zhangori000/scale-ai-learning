# Large Area Tiling Follow-Up

This is the missing practical follow-up for the restaurant question.

## Why tiling is needed

Google Places Text Search (New):

- returns at most 20 results per page
- can return at most about 60 results across all pages for one search, according to the docs as of 2026-03-15

That means a single very large rectangle can under-sample dense regions. Even if there are hundreds of restaurants in the box, the API will not give you all of them from one query.

## Core idea

If a tile looks saturated, split it into smaller rectangles and query each one separately.

In code, the useful signal is:

- if `nextPageToken` still exists after you have fetched your allowed pages for that tile, the tile is saturated

This is the key distinction:

- the question is not only "is the rectangle geographically big?"
- the more important question is "is this search likely under-sampled because there are too many matching places in this box?"

So in practice, you split when one or more of these are true:

- the tile is saturated because more pages still exist
- the tile is physically wide enough that you expect result density to vary a lot
- you have already hit your per-tile page budget
- you want higher recall in dense urban areas

Then:

1. split the tile into 4 quadrants
2. query each child tile
3. dedupe globally by place ID
4. sort globally at the end

## DFS vs BFS

Both traversal strategies are valid.

- DFS:
  - uses a stack
  - goes deep into one hot tile first
  - can be useful if you want to quickly drill into the densest area
- BFS:
  - uses a queue
  - explores all tiles level by level
  - can be easier to reason about when you want broad coverage first

The split decision is the same in both cases. The only difference is the order in which you explore the tiles.

## Files to read

- `python_solution/restaurant_service.py`
  - now exposes `scan_restaurants(...)` so you can tell whether a tile saturated
- `python_solution/large_area_restaurant_service.py`
  - quadtree-style tiling solution with both DFS and BFS traversal methods
- `python_solution/test_large_area_restaurant_service.py`
  - shows why tiling can recover high-rated restaurants that a single wide query misses, and includes a BFS variant

## Interview explanation

I would say that one large rectangle is not enough because Places Text Search is paginated and capped. So for dense areas, I would tile the bounding box whenever a tile still looks saturated after my per-tile page budget. That split can be explored with DFS or BFS. In either case I union all results, dedupe by place ID, and do the final ranking globally.
