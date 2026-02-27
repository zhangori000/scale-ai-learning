# Exercise 44 Comments

## Verdict
This exercise is close to the real SDK pattern. Treat it as a correct mental model for client resource hierarchy and lazy loading.

## Reference implementation
- `scale-agentex-python/src/agentex/_client.py`
  - `Agentex.tasks`, `Agentex.agents`, and many other resources use `@cached_property`.
  - The same lazy-resource pattern is repeated for async, raw-response, and streamed-response client wrappers.

## Definitive statements
1. In the real SDK, resource objects are created lazily on first property access, not in client `__init__`.
2. Each resource is a per-client singleton: repeated access returns the same object for that client instance.
3. This pattern exists across multiple client surfaces (`Agentex`, `AsyncAgentex`, raw-response wrappers, streamed-response wrappers).
4. `functools.cached_property` is the production-grade primitive here; `@property` plus `@lru_cache` is a teaching approximation.
5. The `@lru_cache` approach can retain references to many client instances over time; `cached_property` avoids that global-cache behavior.

## How the Gemini exercise adheres
- Adheres strongly on the core idea: lazy creation + stable instance reuse.
- Deviates in implementation detail: it uses `@property` with `@lru_cache` instead of `@cached_property`.
