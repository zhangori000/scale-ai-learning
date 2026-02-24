# Solution: The Configuration Validator (The Manifest Pattern)

In `scale-agentex`, this pattern is the very first step of an agent's lifecycle. It ensures that the "Blueprint" (the manifest) is solid before building the house (the agent).

## The Implementation

```python
from typing import List, Optional
from pydantic import BaseModel, Field, ValidationError

# --- 1. Define the Sections (The Components) ---

class AgentSection(BaseModel):
    # 'name' is REQUIRED, 'description' is OPTIONAL.
    name: str
    description: Optional[str] = None

class RuntimeSection(BaseModel):
    # 'port' and 'host' have DEFAULTS so the user doesn't have to provide them!
    # Pydantic will automatically coerce "8080" into the integer 8080.
    port: int = Field(default=8080, ge=1, le=65535) # Validates port range
    host: str = Field(default="0.0.0.0")

class CapabilitiesSection(BaseModel):
    # A list of strings, default to an empty list.
    tools: List[str] = Field(default_factory=list)

# --- 2. Define the Complete Manifest (The Root) ---

class AgentManifest(BaseModel):
    """
    The main configuration object for an agent.
    It combines all the nested sections.
    """
    agent: AgentSection
    runtime: RuntimeSection = Field(default_factory=RuntimeSection)
    capabilities: CapabilitiesSection = Field(default_factory=CapabilitiesSection)

# --- 3. The Loader ---
def load_manifest(data: dict) -> AgentManifest:
    """
    Parses the raw dictionary (as if it came from a YAML file) 
    into the AgentManifest object.
    """
    return AgentManifest(**data)

# --- 4. Test Cases ---

# Test A: Correct, Full Data
print("--- Test A: Full Data ---")
raw_yaml_1 = {
    "agent": {"name": "LegalBot", "description": "Analyzes contracts"},
    "runtime": {"port": 5003},
    "capabilities": {"tools": ["search", "summarize"]}
}
m1 = load_manifest(raw_yaml_1)
print(f"  Agent Name: {m1.agent.name}, Port: {m1.runtime.port}")
# Output: LegalBot, 5003

# Test B: Minimal Data (Check Defaults)
print("
--- Test B: Minimal Data ---")
raw_yaml_2 = {
    "agent": {"name": "SupportBot"}
}
m2 = load_manifest(raw_yaml_2)
print(f"  Agent Name: {m2.agent.name}")
print(f"  Default Port: {m2.runtime.port}")      # Should be 8080
print(f"  Default Host: {m2.runtime.host}")      # Should be 0.0.0.0
print(f"  Default Tools: {m2.capabilities.tools}") # Should be []

# Test C: BAD Data (Port is not a number)
print("
--- Test C: Bad Data (Port='hello') ---")
raw_yaml_3 = {
    "agent": {"name": "BrokenBot"},
    "runtime": {"port": "hello"}
}
try:
    load_manifest(raw_yaml_3)
except ValidationError as e:
    print(f"  [ERROR] Pydantic caught the typo: {e.errors()[0]['msg']}")
    # Output: input should be a valid integer

# Test D: BAD Data (Missing Name)
print("
--- Test D: Bad Data (Missing Name) ---")
raw_yaml_4 = {
    "runtime": {"port": 1234}
}
try:
    load_manifest(raw_yaml_4)
except ValidationError as e:
    print(f"  [ERROR] Pydantic caught the missing field: {e.errors()[0]['loc']}")
    # Output: ('agent',)
```

### Key Takeaways from the Solution:

1.  **Defaults are Power:** By using `Field(default=...)`, you make your software "opinionated but flexible." It works out of the box with sensible settings, but the user can change them if they need to.
2.  **Validation is Free:** You didn't write a single `if isinstance(port, int)` check. Pydantic handles all the "Type Coercion" and "Validation" for you, saving you from writing hundreds of lines of boring boilerplate code.
3.  **Self-Documenting:** If you want to know what a "LegalBot" needs, you just read the `AgentManifest` class. It tells you exactly which fields are required and what they should be.
4.  **Why we use it for Agents:** In `scale-agentex`, every time you initialize an agent via the CLI, it creates this file for you. The platform then reads it back to know exactly how to "hook up" your agent into the overall ecosystem.
