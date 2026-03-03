# Exercise 1: Build Complete Type Atlas

## Difficulty
Medium

## Why this exercise exists
You cannot reason about Agentex behavior if you only know a few models (`Task`, `Event`, `TextContent`).
This exercise forces complete coverage of `agentex.types` so you have a reliable mental model.

## Target files
- `scale-agentex-python/src/agentex/types/`
- `scale-agentex-python/src/agentex/types/messages/`
- `scale-agentex-python/src/agentex/types/shared/`
- `scale-agentex-python/api.md`

## Your task
Create a full atlas of the `agentex.types` surface.

### Requirements
1. Classify every file in `src/agentex/types` into one of:
   - core entity
   - content/delta/streaming
   - rpc
   - params
   - response wrappers
   - enum/literal
2. For each file, label its model style:
   - `BaseModel`
   - `TypedDict`
   - `TypeAlias`
3. Identify all discriminated unions and record their discriminator field(s).
4. Identify at least 5 places where a model from `agentex.types` is reused by another model.

## Hints
- Start from `src/agentex/types/__init__.py` to get the exported surface.
- Search for:
  - `class .*\\(BaseModel\\)`
  - `class .*\\(TypedDict`
  - `TypeAlias =`
  - `PropertyInfo(discriminator=`
- Use `api.md` to connect params and responses to real endpoints.

## Expected deliverables
1. `atlas.md` with your final classification table.
2. `reuse_map.md` with at least 5 dependency chains (example: `TaskMessage -> TaskMessageContent -> TextContent`).

## Success criteria
- No files missed.
- Discriminated unions correctly identified.
- You can explain when to use `*_param` vs non-`_param` model variants.
