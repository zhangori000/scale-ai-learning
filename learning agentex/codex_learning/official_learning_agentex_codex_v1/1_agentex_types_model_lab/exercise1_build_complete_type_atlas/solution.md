# Solution: Build Complete Type Atlas

## Reference classification

### Core entities (`BaseModel`)
- `agent.py`
- `task.py`
- `event.py`
- `state.py`
- `task_message.py`
- `span.py`
- `agent_task_tracker.py`
- `deployment_history.py`

### Content/streaming models
- Content models:
  - `text_content.py`
  - `data_content.py`
  - `reasoning_content.py`
  - `tool_request_content.py`
  - `tool_response_content.py`
  - `task_message_content.py` (union alias with discriminator)
- Content params:
  - `text_content_param.py`
  - `data_content_param.py`
  - `reasoning_content_param.py`
  - `tool_request_content_param.py`
  - `tool_response_content_param.py`
  - `task_message_content_param.py` (union alias)
- Streaming/deltas:
  - `task_message_update.py` (union alias with discriminator)
  - `task_message_delta.py` (union alias with discriminator)
  - `text_delta.py`
  - `data_delta.py`
  - `tool_request_delta.py`
  - `tool_response_delta.py`
  - `reasoning_content_delta.py`
  - `reasoning_summary_delta.py`

### RPC models
- `acp_type.py`
- `agent_rpc_params.py`
- `agent_rpc_by_name_params.py`
- `agent_rpc_result.py`
- `agent_rpc_response.py`

### Params models (`TypedDict`)
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

### Response wrappers
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

### Enum/literal aliases
- `message_author.py`
- `message_style.py`
- `text_format.py`

### Subpackages
- `messages/batch_create_params.py`
- `messages/batch_create_response.py`
- `messages/batch_update_params.py`
- `messages/batch_update_response.py`
- `shared/delete_response.py`

## Expected counts (current snapshot)
- Top-level files in `types` (excluding `__init__.py`): `65`
- `messages` subpackage files: `4`
- `shared` subpackage files: `1`
- Files containing `BaseModel`: `26`
- Files containing `TypedDict`: `25`
- Files containing `TypeAlias`: `19`

## Discriminated unions to find
- `task_message_content.py`: discriminator `type`
- `task_message_delta.py`: discriminator `type`
- `task_message_update.py`: discriminator `type`

## Reuse chains (examples)
1. `TaskMessage -> TaskMessageContent -> TextContent | DataContent | ReasoningContent | Tool*Content`
2. `Event -> TaskMessageContent`
3. `MessageCreateParams -> TaskMessageContentParam -> TextContentParam | ...`
4. `TaskMessageUpdate -> TaskMessageDelta -> TextDelta | DataDelta | Tool*Delta | Reasoning*Delta`
5. `AgentRpcResponse -> AgentRpcResult -> TaskMessageUpdate/Task/Event`

## Why this matters
This map gives you the exact boundary between:
- request payload shapes (`TypedDict` params),
- persisted/returned entities (`BaseModel`),
- and union-based polymorphic messaging (content/delta/update).
