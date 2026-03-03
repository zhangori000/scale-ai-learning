# Agentex Types Model Lab

This module answers one concrete question:

How is **all** of `agentex.types` organized, and how do those models drive API and agent RPC contracts?

## Scope snapshot (current repo)

- `scale-agentex-python/src/agentex/types`: 65 top-level files (excluding `__init__.py`)
- `scale-agentex-python/src/agentex/types/messages`: 4 files
- `scale-agentex-python/src/agentex/types/shared`: 1 file
- Style mix across top-level files:
  - 26 files defining `BaseModel` classes
  - 25 files defining `TypedDict` request params
  - 19 files defining `TypeAlias` unions/literals/list wrappers

## Data model map (full top-level coverage)

### 1) Core entity models (`BaseModel`)
- `agent.py`
- `task.py`
- `event.py`
- `state.py`
- `task_message.py`
- `span.py`
- `agent_task_tracker.py`
- `deployment_history.py`

### 2) Message content models + union
- `text_content.py`
- `data_content.py`
- `reasoning_content.py`
- `tool_request_content.py`
- `tool_response_content.py`
- `task_message_content.py`

### 3) Message content param models + union (`TypedDict` + `TypeAlias`)
- `text_content_param.py`
- `data_content_param.py`
- `reasoning_content_param.py`
- `tool_request_content_param.py`
- `tool_response_content_param.py`
- `task_message_content_param.py`

### 4) Streaming update/delta models
- `task_message_update.py`
- `task_message_delta.py`
- `text_delta.py`
- `data_delta.py`
- `tool_request_delta.py`
- `tool_response_delta.py`
- `reasoning_content_delta.py`
- `reasoning_summary_delta.py`

### 5) RPC envelope/result models
- `acp_type.py`
- `agent_rpc_params.py`
- `agent_rpc_by_name_params.py`
- `agent_rpc_result.py`
- `agent_rpc_response.py`

### 6) Enums/literals used across the model layer
- `message_author.py`
- `message_style.py`
- `text_format.py`

### 7) Request parameter models (`*_params.py`)
- `agent_list_params.py`
- `deployment_history_list_params.py`
- `event_list_params.py`
- `message_create_params.py`
- `message_list_params.py`
- `message_list_paginated_params.py`
- `message_update_params.py`
- `span_create_params.py`
- `span_list_params.py`
- `span_update_params.py`
- `state_create_params.py`
- `state_list_params.py`
- `state_update_params.py`
- `task_list_params.py`
- `task_retrieve_params.py`
- `task_retrieve_by_name_params.py`
- `tracker_list_params.py`
- `tracker_update_params.py`

### 8) Response wrapper models (`*_response.py` and list aliases)
- `agent_list_response.py`
- `deployment_history_list_response.py`
- `event_list_response.py`
- `message_list_response.py`
- `message_list_paginated_response.py`
- `span_list_response.py`
- `state_list_response.py`
- `task_list_response.py`
- `task_retrieve_response.py`
- `task_retrieve_by_name_response.py`
- `tracker_list_response.py`

### 9) Subpackages under `types`
- `messages/batch_create_params.py`
- `messages/batch_create_response.py`
- `messages/batch_update_params.py`
- `messages/batch_update_response.py`
- `shared/delete_response.py`

## Boundary note: `agentex.types` vs `agentex.lib.types`

- `agentex.types` is the generated REST client data model layer.
- `agentex.lib.types` is ADK/ACP runtime contract surface (for example ACP handler params in `scale-agentex-python/src/agentex/lib/types/acp.py`).
- They are intentionally connected: `agentex.lib.types.acp` composes `Agent`, `Task`, `Event`, and `TaskMessageContent` from `agentex.types`.

## Exercise order

1. `exercise1_build_complete_type_atlas`
2. `exercise2_discriminated_unions_and_streaming_shapes`
3. `exercise3_request_response_contract_matrix`

Do them in order. Each exercise depends on the previous one.
