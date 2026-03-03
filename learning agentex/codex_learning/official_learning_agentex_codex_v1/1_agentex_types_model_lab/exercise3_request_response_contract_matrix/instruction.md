# Exercise 3: Request/Response Contract Matrix

## Difficulty
High

## Why this exercise exists
A type list by itself is static knowledge.
This exercise makes it operational: which `*_params` and response model each endpoint actually uses.

## Target files
- `scale-agentex-python/api.md`
- `scale-agentex-python/src/agentex/resources/`
- `scale-agentex-python/src/agentex/types/`
- `scale-agentex-python/src/agentex/types/messages/`

## Your task
Build a complete endpoint-to-type matrix.

### Requirements
1. Cover these resource groups:
   - `agents`
   - `tasks`
   - `messages`
   - `messages.batch`
   - `spans`
   - `states`
   - `events`
   - `tracker`
   - `deployment_history`
2. For each endpoint, document:
   - params model type
   - response model type
   - whether the response is entity, list alias, or wrapper object
3. Pick 3 params models and list required fields (`Required[...]`).
4. Pick 3 response models and explain nested/reused types.
5. Add one section describing where polymorphic unions appear in endpoint outputs.

## Hints
- `api.md` already maps each endpoint method to specific type files.
- Use `src/agentex/types/__init__.py` to verify exported names.
- The `messages` and `shared` subpackages are easy to miss; include them.

## Expected deliverables
1. `contract_matrix.md`
2. `required_fields_notes.md`

## Success criteria
- Matrix is complete for all listed resource groups.
- Params/response typing is accurate.
- You can trace a request from `TypedDict` params to `BaseModel`/alias response.
