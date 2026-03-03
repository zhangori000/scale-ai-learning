# Exercise 3: Build a Mini `workflow` Decorator System

Goal: reproduce the core decorator behavior to confirm your mental model.

## Files

- Starter: `2_codex/code/mini_temporal_starter.py`
- Checker: `2_codex/code/mini_temporal_check.py`
- Solution: `2_codex/code/mini_temporal_solution.py` (open only after trying)

## Tasks

1. In `mini_temporal_starter.py`, implement:
- `defn(name=None)`
- `run(fn)`
- `signal(name=None)`

2. Required behavior:
- `@run` marks exactly one method in a class as the run entrypoint.
- `@signal(name=...)` marks methods as signal handlers.
- `@defn(name=...)` attaches class metadata:
  - `__mini_workflow_name__`
  - `__mini_run_method__`
  - `__mini_signal_methods__` (dict of signal name -> method name)

3. Run:

```powershell
python .\2_codex\code\mini_temporal_check.py
```

4. Pass criteria:
- checker prints `all checks passed`

## Reflection

After passing, answer:

1. What job is done by decorators vs by worker runtime?
2. Why can decorators exist without running Temporal itself?
