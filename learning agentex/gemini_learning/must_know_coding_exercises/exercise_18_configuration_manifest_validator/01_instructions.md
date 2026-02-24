# Exercise: The Configuration Validator (The Manifest Pattern)

In `scale-agentex`, every agent has a `manifest.yaml`. This file defines its identity, its port, and its capabilities. If the user makes a typo (e.g., `port: "eighty" instead of 8080`), the platform must catch it **before** trying to start the agent.

## The Goal
Create a nested Pydantic model called `AgentManifest` that validates a dictionary representing a YAML file.

## Requirements
1.  **Nested Models:**
    *   `AgentSection`: `name` (str), `description` (str, optional).
    *   `RuntimeSection`: `port` (int, default=8080), `host` (str, default="0.0.0.0").
    *   `CapabilitiesSection`: `tools` (list of strings, default=[]).
2.  **Manifest Model:**
    *   Combines all three sections.
3.  **The Validator:** Create a function `load_manifest(raw_data: dict)` that returns an `AgentManifest` or raises a clear error.
4.  **The Test:** Try a "Correct" dictionary and an "Incorrect" one (where port is a string).

## Starter Code
```python
from typing import List, Optional
from pydantic import BaseModel, Field, ValidationError

# --- 1. Define the Sections (YOUR JOB) ---

class AgentSection(BaseModel):
    # TODO: name, description
    pass

class RuntimeSection(BaseModel):
    # TODO: port, host
    pass

class CapabilitiesSection(BaseModel):
    # TODO: tools
    pass

class AgentManifest(BaseModel):
    # TODO: Combine them
    pass

# --- 2. The Loader ---
def load_manifest(data: dict) -> AgentManifest:
    """
    Parses the raw dictionary into the Manifest object.
    """
    return AgentManifest(**data)

# --- 3. Test Cases ---

# Test A: Correct Data
raw_yaml_1 = {
    "agent": {"name": "LegalBot", "description": "Analyzes contracts"},
    "runtime": {"port": 5003},
    "capabilities": {"tools": ["search", "summarize"]}
}
m1 = load_manifest(raw_yaml_1)
print(f"Agent Name: {m1.agent.name}, Port: {m1.runtime.port}")

# Test B: Missing Data (Should use defaults)
raw_yaml_2 = {
    "agent": {"name": "SupportBot"}
}
# TODO: Load this and check the defaults for 'port' and 'tools'

# Test C: BAD Data (Port is not a number)
raw_yaml_3 = {
    "agent": {"name": "BrokenBot"},
    "runtime": {"port": "hello"}
}
# TODO: Try-except this to see the Pydantic error
```
