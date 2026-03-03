# Solution: Request/Response Contract Matrix

## Reference matrix (minimum complete set)

### Agents
- `retrieve(agent_id)` -> response: `Agent`
- `list(**AgentListParams)` -> response: `AgentListResponse` (list alias)
- `delete(agent_id)` -> response: `DeleteResponse`
- `delete_by_name(agent_name)` -> response: `DeleteResponse`
- `retrieve_by_name(agent_name)` -> response: `Agent`
- `rpc(agent_id, **AgentRpcParams)` -> response: `AgentRpcResponse`
- `rpc_by_name(agent_name, **AgentRpcByNameParams)` -> response: `AgentRpcResponse`

### Tasks
- `retrieve(task_id, **TaskRetrieveParams)` -> response: `TaskRetrieveResponse`
- `list(**TaskListParams)` -> response: `TaskListResponse` (list alias of `TaskListResponseItem`)
- `delete(task_id)` -> response: `DeleteResponse`
- `delete_by_name(task_name)` -> response: `DeleteResponse`
- `retrieve_by_name(task_name, **TaskRetrieveByNameParams)` -> response: `TaskRetrieveByNameResponse`

### Messages
- `create(**MessageCreateParams)` -> response: `TaskMessage`
- `retrieve(message_id)` -> response: `TaskMessage`
- `update(message_id, **MessageUpdateParams)` -> response: `TaskMessage`
- `list(**MessageListParams)` -> response: `MessageListResponse` (list alias)
- `list_paginated(**MessageListPaginatedParams)` -> response: `MessageListPaginatedResponse` (wrapper with pagination metadata)

### Messages Batch
- `batch.create(**messages.BatchCreateParams)` -> response: `messages.BatchCreateResponse` (list alias)
- `batch.update(**messages.BatchUpdateParams)` -> response: `messages.BatchUpdateResponse` (list alias)

### Spans
- `create(**SpanCreateParams)` -> response: `Span`
- `retrieve(span_id)` -> response: `Span`
- `update(span_id, **SpanUpdateParams)` -> response: `Span`
- `list(**SpanListParams)` -> response: `SpanListResponse` (list alias)

### States
- `create(**StateCreateParams)` -> response: `State`
- `retrieve(state_id)` -> response: `State`
- `update(state_id, **StateUpdateParams)` -> response: `State`
- `list(**StateListParams)` -> response: `StateListResponse` (list alias)
- `delete(state_id)` -> response: `State`

### Events
- `retrieve(event_id)` -> response: `Event`
- `list(**EventListParams)` -> response: `EventListResponse` (list alias)

### Tracker
- `retrieve(tracker_id)` -> response: `AgentTaskTracker`
- `update(tracker_id, **TrackerUpdateParams)` -> response: `AgentTaskTracker`
- `list(**TrackerListParams)` -> response: `TrackerListResponse` (list alias)

### Deployment History
- `retrieve(deployment_id)` -> response: `DeploymentHistory`
- `list(**DeploymentHistoryListParams)` -> response: `DeploymentHistoryListResponse` (list alias)

## Required-field examples (`TypedDict`)

1. `MessageCreateParams`
- required: `task_id`, `content`

2. `StateCreateParams`
- required: `task_id`, `agent_id`, `state`

3. `messages.BatchCreateParams`
- required: `task_id`, `contents`

## Nested/reused response examples

1. `TaskMessage`
- contains `content: TaskMessageContent` (discriminated union)

2. `MessageListPaginatedResponse`
- contains `data: List[TaskMessage]`
- adds `has_more`, `next_cursor`

3. `AgentRpcResponse`
- contains `result: AgentRpcResult`
- `AgentRpcResult` can be `Task`, `Event`, list of `TaskMessage`, stream updates, or `None`

## Where polymorphism appears in outputs

- `TaskMessage.content` -> `TaskMessageContent` (text/data/reasoning/tool request/tool response)
- `AgentRpcResponse.result` -> `AgentRpcResult` union
- `SendMessageStreamResponse.result` (inside `agent_rpc_response.py`) -> `TaskMessageUpdate` union

## Why this matters

This matrix is your bridge from API method names to concrete model files, so debugging can start at the exact type boundary instead of guessing.
