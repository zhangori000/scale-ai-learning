# Context 04: Cursor Pagination Primer

Offset pagination is easy to implement and often wrong for rapidly changing datasets. Cursor pagination is harder to implement and usually correct for activity feeds, message timelines, and high-write collections.

The core issue is window instability. With offset pagination, rows can shift between page requests due to new inserts or deletes. This causes duplicates or misses. Cursor pagination avoids this by anchoring page boundaries to an ordering key.

A correct cursor design requires stable ordering. If ordering by `created_at` alone is not unique, include a tie-breaker key such as `id`. The query should then compare tuples like `(created_at, id)`.

Good cursors are opaque to clients. Internally they can encode structured data, but externally they should be treated as an opaque token. Versioning the internal payload is useful for backward compatibility when cursor format evolves.

Cursor validation should be strict enough to prevent undefined behavior. Invalid or tampered cursors should return a clear client error. Silent fallback to first page can hide bugs and confuse clients.

For interviews, do not stop at encoding details. Emphasize contract consistency: the cursor payload, sort key, and query predicate must stay aligned over time or pagination correctness collapses.
