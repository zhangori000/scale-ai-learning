# Exercise 2: Discriminated Unions and Streaming Shapes

## Difficulty
High

## Why this exercise exists
Most runtime bugs in agent flows happen at polymorphic boundaries:
- content unions (`TaskMessageContent`)
- delta unions (`TaskMessageDelta`)
- stream update unions (`TaskMessageUpdate`)

If you can validate these confidently, you can debug most message-shape issues quickly.

## Target files
- `scale-agentex-python/src/agentex/types/task_message_content.py`
- `scale-agentex-python/src/agentex/types/task_message_delta.py`
- `scale-agentex-python/src/agentex/types/task_message_update.py`
- Variant files under `scale-agentex-python/src/agentex/types/*content*.py` and `*delta*.py`

## Your task
Write a small validation script that exercises all union variants.

### Requirements
1. Validate at least one payload for each `TaskMessageContent` variant:
   - `text`
   - `reasoning`
   - `data`
   - `tool_request`
   - `tool_response`
2. Validate at least one payload for each `TaskMessageDelta` variant:
   - `text`
   - `data`
   - `tool_request`
   - `tool_response`
   - `reasoning_summary`
   - `reasoning_content`
3. Validate all four `TaskMessageUpdate` variants:
   - `start`
   - `delta`
   - `full`
   - `done`
4. Add at least 3 invalid payloads and confirm they fail with useful validation errors.

## Hints
- Use `pydantic.TypeAdapter(...).validate_python(...)`.
- `TaskMessageUpdate` and `TaskMessageContent` use discriminator `type`.
- Start with minimal valid payloads, then add optional fields.

## Expected deliverables
1. `union_validation.py` script.
2. `union_validation_output.md` containing:
   - successful parses
   - failure cases and error summaries

## Success criteria
- Every union variant is tested.
- Invalid payloads fail deterministically.
- You can explain the difference between content-level and update-level polymorphism.
