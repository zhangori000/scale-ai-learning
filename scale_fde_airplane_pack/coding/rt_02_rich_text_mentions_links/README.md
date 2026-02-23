# RT-02: Rich Text Mentions, Links, and Offset Mapping (Essay Editorial)

This chapter teaches a class of parsing question that shows up in product-facing backends: translate user-authored inline markup into normalized text plus structured entities with exact offsets. The difficulty is not parsing alone. The difficulty is preserving a stable index mapping while syntax is transformed.

The prompt uses two entity syntaxes:

Mention: `@{user_id|display_name}`. Link: `<url|label>`.

Output has two parts:

`text`: rendered plain text where mention renders to `display_name` and link renders to `label`. `entities`: list with `[start, end)` offsets into the rendered text.

The subtle part is this: entity offsets are measured in output text coordinates, not input coordinates. Because syntax markers are removed during rendering, output positions drift relative to source string. If you compute offsets against source string, all your offsets are wrong.

The clean mental model is this: build output text incrementally and create entity offsets from current output length at the moment you render each entity.

We process left to right with a deterministic scanner.

At any position, we have three possibilities:

mention opener `@{`. link opener `<`. plain character.

When we hit entity opener, we parse until closing delimiter (`}` for mention, `>` for link), validate payload format, render replacement text into output buffer, and record offset interval around the rendered segment.

Why this approach is robust: offsets are computed from actual output buffer length, so they remain correct regardless of input syntax length.

Let us walk an example by hand.

Input:

`Hi @{u1|Alice} see <https://docs.example|docs>`

Output build:

write `Hi ` -> output length 3. parse mention payload `u1|Alice`. start = 3, append `Alice`, end = 8. record mention entity `[3,8)`. write ` see ` -> length 13. parse link payload `https://docs.example|docs`. start = 13, append `docs`, end = 17. record link entity `[13,17)`.

Final text: `Hi Alice see docs`

Entities now point into rendered text exactly.

A common failure is allowing malformed payloads. For mention, both user_id and display_name must exist. For link, both URL and label must exist. If one is missing, reject with position-specific error.

Another common failure is not defining URL policy. A practical interview answer uses minimal scheme validation (`http://` or `https://`) unless interviewer asks for strict RFC parser.

Complexity is linear in input size because each character is scanned at most once and entity parsing uses direct delimiter search.

Reference implementation:

```python
from dataclasses import dataclass
from typing import Dict, Any, List

class EntityParseError(ValueError):
    pass

@dataclass
class Entity:
    type: str
    start: int
    end: int
    meta: Dict[str, Any]

def parse_entities(message: str) -> Dict[str, Any]:
    i = 0
    n = len(message)
    out: List[str] = []
    entities: List[Entity] = []

    def out_len() -> int:
        return len(out)

    while i < n:
        if message.startswith("@{", i):
            close = message.find("}", i + 2)
            if close == -1:
                raise EntityParseError(f"Unclosed mention at index {i}")

            payload = message[i + 2 : close]
            parts = payload.split("|", 1)
            if len(parts) != 2 or not parts[0] or not parts[1]:
                raise EntityParseError(f"Invalid mention payload at index {i}")

            user_id, display_name = parts
            start = out_len()
            out.extend(display_name)
            end = out_len()

            entities.append(
                Entity(
                    type="mention",
                    start=start,
                    end=end,
                    meta={"user_id": user_id, "display_name": display_name},
                )
            )

            i = close + 1
            continue

        if message.startswith("<", i):
            close = message.find(">", i + 1)
            if close == -1:
                raise EntityParseError(f"Unclosed link at index {i}")

            payload = message[i + 1 : close]
            parts = payload.split("|", 1)
            if len(parts) != 2 or not parts[0] or not parts[1]:
                raise EntityParseError(f"Invalid link payload at index {i}")

            url, label = parts
            if not (url.startswith("http://") or url.startswith("https://")):
                raise EntityParseError(f"Invalid URL scheme at index {i}")

            start = out_len()
            out.extend(label)
            end = out_len()

            entities.append(
                Entity(
                    type="link",
                    start=start,
                    end=end,
                    meta={"url": url, "label": label},
                )
            )

            i = close + 1
            continue

        out.append(message[i])
        i += 1

    return {
        "text": "".join(out),
        "entities": [
            {"type": e.type, "start": e.start, "end": e.end, **e.meta}
            for e in entities
        ],
    }
```

Correctness argument in interview terms:

Scanner is left-to-right deterministic. Every emitted entity interval is measured from output buffer length at render time. Output text and entities are produced in the same sequence, so offsets remain coherent. Malformed syntax is rejected with exact location.

Good tests should include multiple adjacent entities, malformed mention/link payloads, and mixed plain+entity text.

```python
def test_happy_path():
    out = parse_entities("Hi @{u1|Alice} see <https://x|docs>")
    assert out["text"] == "Hi Alice see docs"
    assert out["entities"][0]["type"] == "mention"

def test_bad_mention_payload():
    try:
        parse_entities("@{u1}")
    except EntityParseError:
        return
    raise AssertionError("expected EntityParseError")

def test_bad_url_scheme():
    try:
        parse_entities("<ftp://x|label>")
    except EntityParseError:
        return
    raise AssertionError("expected EntityParseError")
```

If interviewer asks extension questions, natural next additions are escaping rules (for literal `@{` or `<`), hashtag entities, and optional source-to-output index map for editor tooling.

A strong close statement:

"I parse inline entities in one pass, render directly to output text, and derive offsets from output length at insertion time. That guarantees offset correctness after syntax removal and keeps complexity linear."

## Deep Dive Appendix

This appendix explains index mapping, which is the central correctness challenge in entity extraction tasks.

### Input Index vs Output Index

Input contains syntax wrappers like `@{...}` and `<...>`. Output strips wrappers and keeps rendered labels. Therefore source indices and output indices diverge.

Correct offsets must be computed in output coordinate space at render time.

### Why Single-Pass Is Clean

By emitting output as you parse and measuring `start/end` using output length, you avoid post-hoc index remapping tables.

This keeps algorithm easy to reason about and reduces off-by-one risk.

### Entity Validation Philosophy

Validation should be fail-fast:

mention missing user_id or display_name -> error. link missing url or label -> error. invalid URL scheme per agreed policy -> error.

Silent acceptance of malformed entities usually causes hard-to-debug downstream behavior.

### Overlap Safety

Because parser consumes one entity at a time and appends rendered text atomically, generated entities cannot overlap unless syntax nesting is added. If nesting is disallowed, this property should be stated.

### Unicode Note

Offsets are by Python codepoint index in this implementation. If product requirements use UTF-16 code units (common in some frontends), conversion layer is needed. Mention this if interviewer asks internationalization questions.

### Learning summary

"I parse and render in one pass, record each entity offset from current output length, and validate payload shape strictly. This guarantees offsets reference rendered text correctly even though source markup length is different."

## Algorithmic Foundations For This Problem

Restate input and output contract in deterministic terms. Define tie-breakers explicitly. Define malformed-input behavior explicitly.

Write invariants before coding. Invariants reduce logical bugs. Examples include deterministic ordering and no duplicate contribution.

Choose data structures based on semantics. Use map for dedupe and latest-by-key patterns. Use heap for progressive ordering extraction. Use stack for nested grammar. Use deque for sliding windows.

Separate transformation phase from aggregation phase when semantics differ. Dry-run tiny examples before implementation. Then scale to stress tests.

Complexity should be explained phase-by-phase. Prefer clarity first, then optimize if bottlenecks are measured.

