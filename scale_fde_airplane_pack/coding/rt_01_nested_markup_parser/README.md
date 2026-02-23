# RT-01: Nested Rich Text Markup Parser (Essay Editorial)

This chapter is a slow, deliberate walkthrough of a parsing problem that appears simple on paper and then fails in edge cases during implementation. If you are preparing for coding rounds, this style of question is common because it tests whether you can turn grammar rules into a deterministic algorithm while preserving correctness under malformed input.

The prompt asks for a parser over a mini rich-text syntax with tags like `[b]...[/b]`, `[i]...[/i]`, and `[code]...[/code]`. The output is not raw text; it is normalized spans where each span carries the active style set. The hidden challenge is not tokenization. The hidden challenge is state transitions at style boundaries.

Before writing code, it helps to think in terms of language structure. This syntax is nested and requires LIFO closure. That means a stack is not a convenience; it is the natural mathematical model of the grammar. Every opening tag pushes style context. Every closing tag must match the current top. If it does not, the string is syntactically invalid. This is where many candidates lose points: they "recover" from invalid structure instead of reporting exact parse errors.

A robust parser for this problem has three moving pieces.

First, a scanner over the input string. The scanner decides whether the next token is plain text or a tag boundary.

Second, a style stack. The stack captures active styles in order. This order is what allows nested spans like bold-inside-italic to be represented correctly.

Third, a text buffer. The buffer holds plain text since the last style transition. Whenever style context changes, you flush buffer into a span with the current stack snapshot.

That flush rule is the conceptual center of the entire problem. If you forget to flush before push/pop, styles leak across boundaries and output becomes inconsistent.

Let us walk one example slowly:

Input: `[b]A[i]B[/i]C[/b]`

At `[b]`, stack becomes `[b]`.

Read `A` into buffer.

At `[i]`, flush buffer as `("A", [b])`, then push `i`. Stack is `[b, i]`.

Read `B`.

At `[/i]`, flush buffer as `("B", [b, i])`, then pop `i`. Stack back to `[b]`.

Read `C`.

At `[/b]`, flush as `("C", [b])`, pop `b`, stack empty.

End of string with empty stack means syntactically complete.

One more normalization rule matters: adjacent spans with identical style lists should be merged. This keeps output canonical and prevents noisy fragmentation.

Now consider malformed input: `[b]A[/i]`. At close tag `i`, top of stack is `b`, so close mismatch is detected. A strict parser should raise a parse error with position. This is important in interviews because strong error messages demonstrate that your algorithm tracks exact control state.

Unknown tags are another policy decision. Unless interviewer says otherwise, reject unknown tags explicitly. Silent fallback to plain text usually causes inconsistent behavior and hidden bugs.

Complexity is straightforward once algorithm is designed well. You scan each character once and do constant-time stack operations per tag, so time is `O(n)`. Space is `O(n)` in worst case for output spans plus temporary buffers.

A full reference implementation is below.

```python
from dataclasses import dataclass
from typing import List, Tuple

class ParseError(ValueError):
    pass

ALLOWED = {"b", "i", "code"}

@dataclass(eq=True)
class Span:
    text: str
    styles: Tuple[str, ...]

def parse_rich_text(source: str) -> List[Span]:
    spans: List[Span] = []
    stack: List[str] = []
    buf: List[str] = []
    i = 0
    n = len(source)

    def flush() -> None:
        if not buf:
            return
        text = "".join(buf)
        buf.clear()
        if not text:
            return
        styles = tuple(stack)
        if spans and spans[-1].styles == styles:
            spans[-1] = Span(spans[-1].text + text, styles)
        else:
            spans.append(Span(text, styles))

    while i < n:
        ch = source[i]
        if ch != "[":
            buf.append(ch)
            i += 1
            continue

        close = source.find("]", i + 1)
        if close == -1:
            raise ParseError(f"Unclosed tag starting at index {i}")

        token = source[i + 1 : close]
        is_close = token.startswith("/")
        tag = token[1:] if is_close else token

        if tag not in ALLOWED:
            raise ParseError(f"Unknown tag '{tag}' at index {i}")

        flush()

        if is_close:
            if not stack:
                raise ParseError(f"Unexpected close tag '{tag}' at index {i}")
            if stack[-1] != tag:
                raise ParseError(
                    f"Mismatched close tag '{tag}' at index {i}; expected '{stack[-1]}'"
                )
            stack.pop()
        else:
            stack.append(tag)

        i = close + 1

    flush()

    if stack:
        raise ParseError(f"Unclosed tag(s): {stack}")

    return spans
```

The best way to discuss correctness in interview is by invariants, not by confidence.

Invariant 1: stack always equals active style context for current scanner position.

Invariant 2: buffer contains plain text collected since last style transition.

Invariant 3: every flushed span is labeled with exact stack snapshot at the time text was read.

Given these three invariants, output style assignment is correct by construction.

High-value tests include nested style transitions, malformed closure order, adjacent merge behavior, and trailing unclosed tags. A concise set is below.

```python
def test_nested():
    out = parse_rich_text("[b]A[i]B[/i]C[/b]")
    assert out == [
        Span("A", ("b",)),
        Span("B", ("b", "i")),
        Span("C", ("b",)),
    ]

def test_merge_adjacent():
    out = parse_rich_text("[b]A[/b][b]B[/b]")
    assert out == [Span("AB", ("b",))]

def test_mismatch():
    try:
        parse_rich_text("[b]A[/i]")
    except ParseError:
        return
    raise AssertionError("expected ParseError")

def test_unclosed():
    try:
        parse_rich_text("[b]A")
    except ParseError:
        return
    raise AssertionError("expected ParseError")
```

A strong verbal close for this question sounds like this:

"I modeled the markup grammar with a stack, flushed buffered text exactly at style boundaries, and enforced strict LIFO closure with precise parse errors. The parser runs in linear time and produces canonical spans by merging adjacent identical styles."

## Deep Dive Appendix

This appendix deepens parser reasoning and gives a formal lens for why the stack solution is correct.

### Grammar Perspective

You can model this mini language with tokens:

text char. open tag `[name]`. close tag `[/name]`.

The nesting rule implies well-formedness is equivalent to balanced, properly ordered delimiters. That is exactly what a stack validates.

### Why Flush Boundaries Matter

Consider this sequence: `[b]A[i]B[/i]C[/b]`.

If you do not flush before push/pop, `A`, `B`, and `C` can collapse into one span with wrong style coverage. Flushing at every style transition preserves exact style interval boundaries.

### Canonicalization

Merging adjacent identical style spans creates a canonical representation. Canonical output simplifies downstream diffing and tests.

Without canonicalization, two semantically equal parses can produce different span fragmentation.

### Error Taxonomy

Useful parse errors to surface:

unknown tag. unclosed tag opener. unexpected close when stack empty. mismatched close vs stack top. non-empty stack at end.

Position-aware errors dramatically improve debugging and candidate signal in interviews.

### Complexity Justification

Each character is processed once. Tag parsing uses `find(']')` from current position. In aggregate, this still yields linear behavior for practical implementations, assuming standard string search optimizations.

### Extension Strategy

If interviewer asks for escaping, add lexer phase with escape handling before parser phase. Keeping lexer and parser responsibilities separate prevents accidental complexity explosion.

### Learning summary

"I model style nesting with a stack, flush buffered text at every style boundary, and validate close tags strictly against stack top. This gives linear parsing with exact error localization and normalized spans."

## Algorithmic Foundations For This Problem

Restate input and output contract in deterministic terms. Define tie-breakers explicitly. Define malformed-input behavior explicitly.

Write invariants before coding. Invariants reduce logical bugs. Examples include deterministic ordering and no duplicate contribution.

Choose data structures based on semantics. Use map for dedupe and latest-by-key patterns. Use heap for progressive ordering extraction. Use stack for nested grammar. Use deque for sliding windows.

Separate transformation phase from aggregation phase when semantics differ. Dry-run tiny examples before implementation. Then scale to stress tests.

Complexity should be explained phase-by-phase. Prefer clarity first, then optimize if bottlenecks are measured.

