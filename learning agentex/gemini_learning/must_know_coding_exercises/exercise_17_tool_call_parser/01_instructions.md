# Exercise: The Tool Call Parser (LLM to Python)

In `scale-agentex`, an agent can define a set of "Tools" it knows how to use. When an LLM says "I want to use the 'get_weather' tool," the platform must translate that into a real Python function call.

## The Goal
Create a `ToolExecutor` that can store a registry of Python functions and call them using a JSON-like "Tool Request."

## Requirements
1.  **Tools Registry:** Create a class `ToolExecutor` with a `self.tools` dictionary (`{tool_name: python_function}`).
2.  **Registration:** Create a method `register_tool(name: str, func: Callable)`:
    *   Adds the function to the registry.
3.  **Execution:** Create a method `execute_tool(request: dict)` that:
    *   Takes a request like `{"name": "sum", "args": {"a": 5, "b": 10}}`.
    *   Finds the matching tool.
    *   Calls the tool with the arguments using `func(**args)`.
    *   Returns the result.
4.  **Error Handling:** If the tool name is unknown, raise a custom `ToolNotFoundError`.

## Starter Code
```python
from typing import Dict, Any, Callable

# --- 1. The Real Python Tools (User Code) ---
def tool_add(a: int, b: int) -> int:
    return a + b

def tool_greet(name: str) -> str:
    return f"Hello, {name}! I am your AI Agent."

# --- 2. The Custom Exception ---
class ToolNotFoundError(Exception):
    pass

# --- 3. The Tool Executor (YOUR JOB) ---
class ToolExecutor:
    def __init__(self):
        # TODO: Store tools here
        self.tools: Dict[str, Callable] = {}

    def register_tool(self, name: str, func: Callable):
        # TODO: Implement
        pass

    def execute_tool(self, request: dict) -> Any:
        """
        TODO: 
        1. Extract 'name' and 'args' from the request.
        2. Find the function in self.tools.
        3. Call it with the unpacked arguments (**args).
        4. Return the result.
        """
        pass

# --- 4. Execution ---
executor = ToolExecutor()

# Register the tools
executor.register_tool("add", tool_add)
executor.register_tool("greet", tool_greet)

# Test A: Success (add)
request_1 = {"name": "add", "args": {"a": 10, "b": 20}}
result_1 = executor.execute_tool(request_1)
print(f"Result 1: {result_1}") # Expected: 30

# Test B: Success (greet)
request_2 = {"name": "greet", "args": {"name": "Alice"}}
result_2 = executor.execute_tool(request_2)
print(f"Result 2: {result_2}") # Expected: "Hello, Alice!..."

# Test C: Failure (Unknown Tool)
print("
--- Testing Unknown Tool ---")
request_3 = {"name": "hack_the_world", "args": {}}
try:
    executor.execute_tool(request_3)
except ToolNotFoundError:
    print("  [SUCCESS] Blocked invalid tool call.")
```
