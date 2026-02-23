# Day 08: Advanced Coding - Rich Text & Parsing
**Focus:** Turning complex, unstructured strings into structured data (the "bread and butter" of Scale AI's data labeling engine).

## 01. The Problem: The Nested Markup Parser
**Scenario:** Scale AI's labeling UI uses a simple markup like `[b]bold[/b]` and `[i]italic[/i]`. You need to write a parser that takes a string and returns a list of "Spans" (text segments with active styles).

**The Challenge:**
- **Nesting:** `[b]This is [i]both[/i] bold.[/b]`
- **Mismatched Tags:** `[b]Wait, I closed italic first! [/i][/b]` (This should be an error).
- **Adjacency:** `[b]Hello [/b][b]World[/b]` should be merged into one single bold span: `Hello World`.

If you just use Regex, you will fail. Regex cannot handle **arbitrary nesting** because it is not a "Context-Free Grammar." You need a **Stack**.

---

## 02. The Solution: The "Flush-and-Stack" Pattern
1. **The Stack:** Keeps track of "What styles are active right now?"
2. **The Buffer:** Collects characters one by one.
3. **The Flush:** Every time a tag opens (`[b]`) or closes (`[/b]`), we "flush" the buffer into a Span using whatever styles are currently on the stack.

---

## 03. The Working Code (The Recursive Descent Parser)
This is a clean, robust implementation that an interviewer at Scale would love to see.

```python
from typing import List, Tuple, Set
from dataclasses import dataclass

@dataclass
class Span:
    text: str
    styles: Tuple[str, ...] # Using a tuple so it's hashable/comparable

class ParseError(Exception):
    pass

def parse_markup(text: str) -> List[Span]:
    ALLOWED_TAGS = {"b", "i", "u", "code"}
    
    spans = []
    stack = []   # Current active styles (e.g. ['b', 'i'])
    buffer = []  # Current characters being read
    
    i = 0
    while i < len(text):
        if text[i] == "[":
            # 1. We hit a tag! First, flush anything in the buffer
            if buffer:
                current_text = "".join(buffer)
                current_styles = tuple(stack)
                # OPTIMIZATION: Merge with previous span if styles match
                if spans and spans[-1].styles == current_styles:
                    spans[-1].text += current_text
                else:
                    spans.append(Span(current_text, current_styles))
                buffer = []

            # 2. Identify the tag
            end_bracket = text.find("]", i)
            if end_bracket == -1:
                raise ParseError("Unclosed bracket")
            
            tag_content = text[i+1 : end_bracket] # e.g. "b" or "/b"
            is_closing = tag_content.startswith("/")
            tag_name = tag_content[1:] if is_closing else tag_content
            
            if tag_name not in ALLOWED_TAGS:
                raise ParseError(f"Unknown tag: {tag_name}")

            # 3. Update Stack
            if is_closing:
                if not stack or stack[-1] != tag_name:
                    raise ParseError(f"Mismatched tag: {tag_name}")
                stack.pop()
            else:
                stack.append(tag_name)
            
            i = end_bracket + 1
        else:
            # Just a normal character, add to buffer
            buffer.append(text[i])
            i += 1
            
    # Final Flush for the remaining text
    if buffer:
        spans.append(Span("".join(buffer), tuple(stack)))
        
    if stack:
        raise ParseError(f"Unclosed tags remaining: {stack}")
        
    return spans

# --- TEST CASE ---
# Input: "[b]Bold [i]Italic[/i] Still Bold[/b]"
# Output: [Span("Bold ", ("b",)), Span("Italic", ("b", "i")), Span("Still Bold", ("b",))]
print(parse_markup("[b]Bold [i]Italic[/i] Still Bold[/b]"))
```

---

## 04. Architectural Tradeoffs: How to Ace the Interview

### Q: Why use a Stack?
**A:** "Because markup is inherently **hierarchical**. A stack is the natural data structure for Last-In-First-Out (LIFO) operations. When I open a tag, it's the 'most specific' style until it's closed. A stack ensures that tags are closed in the exact reverse order they were opened, which is the definition of well-formed nested markup."

### Q: How do you handle malformed input like `[b]Hello [i]World[/b][/i]`?
**A:** "In my implementation, this throws a `ParseError`. When the `[/b]` tag is encountered, the stack top is `i`. Since `b != i`, I know the user closed tags out of order. In a real product like Scale, we might choose to 'auto-fix' it, but for a strict parser, raising an error is safer for data integrity."

### Q: What is the Time Complexity?
**A:** "**O(N)**. I iterate through the string exactly once. Each tag operation (find, push, pop) is effectively constant time relative to the total string length. The space complexity is also **O(N)** for the output spans and the stack."

### Q: How would you add 'Escaping' (e.g. `[[` to mean a literal `[` )?
**A:** "I would modify the scanner logic. When I see `[`, I'd check the next character. If it's also `[`, I'd treat it as a literal and skip the tag logic. Alternatively, I'd introduce a **Lexer** phase that tokenizes the string into `TEXT`, `OPEN_TAG`, and `CLOSE_TAG` before the parser even starts."
