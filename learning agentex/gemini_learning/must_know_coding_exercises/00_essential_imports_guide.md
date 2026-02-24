# 00: Essential Imports Guide

When reading `scale-agentex` or these exercises, you will see several "modern" Python imports that might look confusing. Here is the context for the most important ones.

## 1. The `typing` Module (Type Safety)
Python is dynamic, but Scale-Agentex uses "Type Hints" everywhere to prevent bugs.

*   **`Annotated[T, metadata]`**: Think of this as a **Labeled Container**. `Annotated[str, Header()]` means "This is a string, but also, it's a Header." The framework reads that metadata to know what to do.
*   **`Literal["value"]`**: Restricts a variable to *only* specific strings. `method: Literal["GET", "POST"]` means the method CANNOT be "PUT".
*   **`Union[A, B]`**: Means "This can be either Type A or Type B."
*   **`Protocol`**: Used for **Structural Typing**. It defines a "Contract" (an interface). Any class that has the same methods as the Protocol "counts" as that type, even if it doesn't inherit from it.
*   **`AsyncIterator[T]`**: Used for **Streaming**. It tells Python that this function will `yield` values asynchronously (one by one over time).

## 2. The `contextvars` Module (Request Isolation)
*   **`ContextVar`**: This is like a global variable that is **safe for async**. If User A and User B both call the API at the same time, `ContextVar` ensures User A's `request_id` doesn't accidentally leak into User B's logs.

## 3. The `inspect` Module (Code Reflection)
*   **`inspect.signature`**: This allows a program to **read its own code**. FastAPI uses this to look at your function arguments and say "Oh, I see you want a `db` connection, let me get that for you."

## 4. Pydantic (Data Validation)
*   **`BaseModel`**: The foundation of every data object in Agentex. It automatically converts JSON into Python objects.
*   **`Field(..., description="...")`**: Adds metadata to a Pydantic field. Used for validation (like `min_length=5`) and for generating the Swagger documentation automatically.

## 5. FastAPI & Starlette (Web Plumbing)
*   **`StreamingResponse`**: Instead of sending a whole JSON file at once, this keeps the connection open and sends data bit-by-bit (like a water faucet).
*   **`Depends`**: The "Dependency Injection" marker. It tells FastAPI "Run this other function first and give me the result."
