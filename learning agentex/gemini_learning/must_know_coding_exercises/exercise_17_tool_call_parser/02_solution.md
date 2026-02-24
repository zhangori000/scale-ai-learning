# Solution: The Tool Call Parser (LLM to Python)

In `scale-agentex`, this logic is the bridge between the "Brain" (the LLM) and the "Body" (the code). When the Agent's SDK receives a JSON-RPC request to "Perform a Tool," it uses this exact pattern to find and run the Python function you wrote.

## The Implementation

```python
from typing import Dict, Any, Callable

# --- 1. The Real Python Tools (User Code) ---
def tool_add(a: int, b: int) -> int:
    return a + b

def tool_greet(name: str) -> str:
    return f"Hello, {name}! I am your AI Agent."

# --- 2. The Custom Exception ---
class ToolNotFoundError(Exception):
    def __init__(self, tool_name: str):
        super().__init__(f"Tool Not Found: The agent does not have a tool named '{tool_name}'.")

# --- 3. The Tool Executor (The Bridge) ---
class ToolExecutor:
    """
    Acts as the 'Registry' for all the capabilities of an agent.
    """
    def __init__(self):
        # Maps a string name (e.g. 'sum') to a real Python function
        self.tools: Dict[str, Callable] = {}

    def register_tool(self, name: str, func: Callable):
        """
        Registers a Python function as an agent's 'Tool'.
        """
        print(f"[REGISTRY] Registered tool: '{name}' (points to function {func.__name__})")
        self.tools[name] = func

    def execute_tool(self, request: dict) -> Any:
        """
        Takes a JSON-like 'Tool Call' request and runs the Python function.
        Example Request: {"name": "sum", "args": {"a": 5, "b": 10}}
        """
        # 1. Extract the name and arguments from the request
        tool_name = request.get("name")
        tool_args = request.get("args", {})
        
        print(f"[EXECUTOR] Calling tool: '{tool_name}' with args: {tool_args}")
        
        # 2. Find the function in our registry
        if tool_name not in self.tools:
            # 3. Handle unknown tools
            raise ToolNotFoundError(tool_name)
            
        func = self.tools[tool_name]
        
        # 4. Call the function with 'Unpacked' arguments (**tool_args)
        # This is a powerful Python feature that turns {"a": 5, "b": 10} 
        # into a=5, b=10 in the function call.
        result = func(**tool_args)
        
        return result

# --- 4. Execution (The Simulation) ---
executor = ToolExecutor()

# Register the tools (This happens during agent initialization)
executor.register_tool("add", tool_add)
executor.register_tool("greet", tool_greet)

print("
--- Testing Tool Success ---")
# This request would come from an LLM like GPT-4 or Claude-3
request_1 = {"name": "add", "args": {"a": 10, "b": 20}}
result_1 = executor.execute_tool(request_1)
print(f"  Result 1: {result_1}") # Output: 30

request_2 = {"name": "greet", "args": {"name": "Alice"}}
result_2 = executor.execute_tool(request_2)
print(f"  Result 2: {result_2}") # Output: "Hello, Alice!..."

print("
--- Testing Unknown Tool ---")
request_3 = {"name": "hack_the_world", "args": {}}
try:
    # This should be BLOCKED because it's not in the registry.
    executor.execute_tool(request_3)
except ToolNotFoundError as e:
    print(f"  [SUCCESS] Blocked invalid tool call: {e}")
```

### Key Takeaways from the Solution

1.  **Safety & Security:** The agent only has access to the functions you **explicitly** register. If an LLM hallucination tries to call a dangerous command like `os.system('rm -rf /')`, the `ToolExecutor` will block it because it's not in the `self.tools` registry.
2.  **Unpacked Arguments (`**kwargs`):** This is the magic that allows JSON data to become Python function arguments seamlessly.
3.  **Why we use it for Agents:** In `scale-agentex`, this is how the platform and the agent communicate. The platform doesn't need to know *what* your agent does; it just sends a `name` and `args` packet, and your code handles the rest. This makes the platform incredibly flexible and modular.
