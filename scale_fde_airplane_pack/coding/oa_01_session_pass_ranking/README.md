# OA-01: Session Pass Ranking
This chapter is written as a full editorial guide. The purpose is to make the problem understandable from zero while still giving you implementation-level precision. The chapter follows your required structure: prompt, deep understanding, concept realities with sub-realities, and code with line-by-line annotations.
## Part 1: Prompt
You are given a list of events. Each event has session_id, user_id, score, and timestamp. Implement session_pass_ranking(events, pass_score). Return one summary row per session with session_id, pass_count, avg_pass_score, and top_user. Rules: for each (session_id, user_id), keep only the newest event by timestamp. A passing user has latest score >= pass_score. top_user is the passing user with maximum passing score. If multiple passing users tie at top score, choose lexicographically smaller user_id. Sessions with zero passing users must still appear in the result with pass_count=0, avg_pass_score=0.0, and top_user=None. Sort output by pass_count descending, then avg_pass_score descending, then session_id ascending.
### Example Input
```json
[
  {"session_id":"s1","user_id":"u1","score":65,"timestamp":100},
  {"session_id":"s1","user_id":"u1","score":80,"timestamp":110},
  {"session_id":"s1","user_id":"u2","score":90,"timestamp":120},
  {"session_id":"s2","user_id":"u3","score":75,"timestamp":100},
  {"session_id":"s2","user_id":"u3","score":60,"timestamp":130},
  {"session_id":"s2","user_id":"u4","score":55,"timestamp":140},
  {"session_id":"s3","user_id":"u9","score":69,"timestamp":200}
]
```
Use pass_score = 70.
### Example Output
```json
[
  {"session_id":"s1","pass_count":2,"avg_pass_score":85.0,"top_user":"u2"},
  {"session_id":"s2","pass_count":0,"avg_pass_score":0.0,"top_user":null},
  {"session_id":"s3","pass_count":0,"avg_pass_score":0.0,"top_user":null}
]
```
Explanation for the example: for s1, latest scores are u1=80 and u2=90, so both pass, average is 85.0, top_user is u2. For s2, latest scores are u3=60 and u4=55, so none pass, yet s2 remains in output. For s3, latest u9=69 does not pass, and s3 still appears with zero metrics.
## Part 2: How To Understand The Prompt And What Is Going On
The central confusion in this problem is mistaking event rows for final state rows. Events are not final truth. Events are updates. Newer updates replace older updates for the same key. The key is not user_id alone. The key is session_id plus user_id. The same user can appear in multiple sessions and those records are independent. Once this key is explicit, the first phase becomes obvious: reconstruct latest user state per session by timestamp comparison. Only after state reconstruction can you aggregate pass metrics. Aggregating first is a semantic bug, not just a style issue. Pass_count is based on latest scores only. Old passing scores that were later replaced by failing scores must not count. Average is also based on passing latest scores only. Dividing by all users in the session is mathematically neat but contractually wrong. Top_user is selected from passing users only. A non-passing user with high old score or high failing score cannot be top_user. You also have a visibility contract: sessions with zero passing users still appear. This means your session set cannot come only from passing records. Output determinism is part of correctness. Missing tie-break rules produce flaky outputs, especially when maps iterate in arbitrary or insertion order. The easiest interview narration is: phase one dedupe by latest timestamp, phase two aggregate pass metrics, phase three deterministic sort. If equal timestamps are possible for the same key and prompt does not define behavior, state your policy. A safe choice is strict greater-than for updates, which means first-seen-wins at equal time. This style of question tests whether you model data reality, not whether you remember one Python trick. Good modeling beats clever one-liners every time. A robust mental shortcut is to ask: if I delete all but newest event per key, does my algorithm still read correctly? If yes, your logic likely respects semantics. When debugging, inspect one session at a time. Validate deduped states, then threshold result, then average and top user. Local reasoning reduces panic. In production terms, this is event-sourced reduction into a materialized report. Interviewers often like hearing this framing because it shows systems awareness. Complexity should be linear for dedupe and aggregation plus sort cost over sessions. If your algorithm repeatedly scans all events per session, it is usually overcomplicated. Do not compress logic too early. Clarity first. Once you pass correctness checks, minor refactors can shorten code without changing semantics. The strongest signal you can send in this round is coherent reasoning from contract to data structure to invariant to output.
## Part 3: Concepts To Solve The Problem
This section is the main learning body. Each concept is described as a fundamental reality with several sub-realities.
### Fundamental Reality 1: Replacement Semantics
Sub-reality 1A: Every event says what the state might be at that timestamp, not forever. Sub-reality 1B: A later event for the same key replaces earlier state even if later value is lower. Sub-reality 1C: Counting all rows violates replacement semantics and overstates passing performance. Sub-reality 1D: Therefore, dedupe by newest event must precede all summary math. Sub-reality 1E: Invariant: exactly one surviving record per (session_id, user_id) after dedupe.
### Fundamental Reality 2: Identity Shape
Sub-reality 2A: Identity is a composite key of session_id and user_id. Sub-reality 2B: Composite keys prevent accidental joins between unrelated sessions. Sub-reality 2C: This identity should appear directly in code as a tuple key for readability. Sub-reality 2D: If key choice is wrong, every downstream metric can look plausible while being wrong. Sub-reality 2E: Correct key modeling is the fastest path to stable logic.
### Fundamental Reality 3: Threshold Participation
Sub-reality 3A: pass_score defines who participates in pass metrics and top-user competition. Sub-reality 3B: Thresholding happens after dedupe because freshness determines the effective score. Sub-reality 3C: pass_count counts passing deduped users, not passing events. Sub-reality 3D: pass_sum accumulates only passing scores so average reflects exactly pass-only performance. Sub-reality 3E: Zero-pass sessions use explicit neutral defaults to keep output schema stable.
### Fundamental Reality 4: Deterministic Winners
Sub-reality 4A: top_user requires deterministic tie resolution among equal scores. Sub-reality 4B: Lexicographically smaller user_id is a simple deterministic tie-break. Sub-reality 4C: Without tie-break, different runtimes may return different winners for same data. Sub-reality 4D: Deterministic selection simplifies testing and debugging. Sub-reality 4E: Determinism is a contract feature, not optional polish.
### Fundamental Reality 5: Session Ordering Contract
Sub-reality 5A: Session rows are sorted by pass_count descending first. Sub-reality 5B: Secondary sort is avg_pass_score descending for sessions with equal pass_count. Sub-reality 5C: Tertiary sort is session_id ascending for full determinism. Sub-reality 5D: Implement sort in one key function to avoid branchy comparator code. Sub-reality 5E: Verify sort behavior with tie-heavy examples, not only clean examples.
### Fundamental Reality 6: Accumulator Design
Sub-reality 6A: Per-session accumulator should include pass_count, pass_sum, top_score, and top_user. Sub-reality 6B: Grouping these fields in one object keeps updates local and coherent. Sub-reality 6C: top_score exists to avoid rescanning participants for every new candidate. Sub-reality 6D: Clear accumulator fields make invariants testable and debuggable. Sub-reality 6E: Opaque temporary variables make interview debugging harder than necessary.
### Fundamental Reality 7: Complexity Boundaries
Sub-reality 7A: Dedupe pass is O(n) with hash map updates. Sub-reality 7B: Aggregation pass is O(u) where u is deduped user-session pairs. Sub-reality 7C: Final sort is O(s log s) where s is number of sessions. Sub-reality 7D: Memory is O(u + s), which is expected because output depends on those sets. Sub-reality 7E: Complexity explanation should be tied to data cardinality, not just asymptotic symbols.
### Fundamental Reality 8: Timestamp Tie Policy
Sub-reality 8A: Equal timestamp behavior is often unspecified and must be made explicit. Sub-reality 8B: Strict-greater update implies first-seen-wins on equal timestamps. Sub-reality 8C: Greater-or-equal update implies last-seen-wins on equal timestamps. Sub-reality 8D: Either policy can pass if communicated and applied consistently. Sub-reality 8E: Hidden assumptions create silent mismatch with interviewer expectations.
### Fundamental Reality 9: Numeric Precision
Sub-reality 9A: Keep internal sums unrounded and compute average at finalization time. Sub-reality 9B: Premature rounding can alter ordering when averages are close. Sub-reality 9C: Represent average as float in output even when integral. Sub-reality 9D: For strict financial semantics, decimal types can be discussed as an extension. Sub-reality 9E: For this OA-style problem, float is usually accepted with deterministic arithmetic order.
### Fundamental Reality 10: Invariant-Driven Debugging
Sub-reality 10A: Invariant one: one latest record per key after phase one. Sub-reality 10B: Invariant two: pass_count equals number of passing deduped records per session. Sub-reality 10C: Invariant three: top_user is None if and only if pass_count is zero. Sub-reality 10D: Invariant four: avg_pass_score is zero exactly when pass_count is zero. Sub-reality 10E: Invariants reduce debugging from broad panic to local inspection.
### Fundamental Reality 11: Test Coverage As Proof
Sub-reality 11A: Include overwrite tests where newer failing score replaces older passing score. Sub-reality 11B: Include equal-top-score tests to validate lexicographic top_user tie-break. Sub-reality 11C: Include sessions that never pass to validate visibility requirements. Sub-reality 11D: Include tie-heavy session ordering tests to validate global deterministic sort. Sub-reality 11E: Good tests demonstrate contract understanding, not only code execution.
### Fundamental Reality 12: Interview Execution
Sub-reality 12A: State your two-phase algorithm before coding to align expectations. Sub-reality 12B: Use variable names that encode semantics and reduce cognitive load. Sub-reality 12C: Dry-run the provided example after coding to demonstrate confidence. Sub-reality 12D: Mention one extension path, such as streaming incremental updates. Sub-reality 12E: Finish by restating complexity and deterministic guarantees.
## Part 4: Move To The Code With Line-By-Line Analysis And Annotations
The solution below is intentionally explicit so each semantic rule maps cleanly to code.
```python
from collections import defaultdict
from typing import Any, Dict, List, Tuple

def session_pass_ranking(events: List[Dict[str, Any]], pass_score: float) -> List[Dict[str, Any]]:
    latest_state: Dict[Tuple[str, str], Dict[str, Any]] = {}

    for event in events:
        session_id = event["session_id"]
        user_id = event["user_id"]
        key = (session_id, user_id)

        if key not in latest_state:
            latest_state[key] = event
            continue

        if event["timestamp"] > latest_state[key]["timestamp"]:
            latest_state[key] = event

    session_acc: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "pass_count": 0,
            "pass_sum": 0.0,
            "top_user": None,
            "top_score": None,
        }
    )

    for (session_id, user_id), record in latest_state.items():
        score = float(record["score"])
        acc = session_acc[session_id]

        if score >= pass_score:
            acc["pass_count"] += 1
            acc["pass_sum"] += score

            if acc["top_score"] is None or score > acc["top_score"]:
                acc["top_score"] = score
                acc["top_user"] = user_id
            elif score == acc["top_score"] and user_id < acc["top_user"]:
                acc["top_user"] = user_id

    rows: List[Dict[str, Any]] = []
    for session_id, acc in session_acc.items():
        pass_count = acc["pass_count"]
        avg_pass_score = acc["pass_sum"] / pass_count if pass_count else 0.0
        rows.append(
            {
                "session_id": session_id,
                "pass_count": pass_count,
                "avg_pass_score": avg_pass_score,
                "top_user": acc["top_user"],
            }
        )

    rows.sort(key=lambda r: (-r["pass_count"], -r["avg_pass_score"], r["session_id"]))
    return rows
```
Line-by-line commentary follows. Each entry explains what the line does and why it exists.
### Line 1
Source text: from collections import defaultdict This lazy initializer creates clean per-session accumulators on demand, reducing manual existence checks. Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 2
Source text: from typing import Any, Dict, List, Tuple Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 4
Source text: def session_pass_ranking(events: List[Dict[str, Any]], pass_score: float) -> List[Dict[str, Any]]: Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 5
Source text: latest_state: Dict[Tuple[str, str], Dict[str, Any]] = {} This creates the deduplicated state map. Without this map, stale records would leak into pass metrics and ranking. Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 7
Source text: for event in events: Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 8
Source text: session_id = event["session_id"] Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 9
Source text: user_id = event["user_id"] Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 10
Source text: key = (session_id, user_id) This defines the exact identity boundary used by replacement semantics. The tuple keeps per-session user states independent. Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 12
Source text: if key not in latest_state: This handles first-seen state for a key. Initial insert avoids unnecessary comparisons and keeps logic straightforward. Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 13
Source text: latest_state[key] = event Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 14
Source text: continue Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 16
Source text: if event["timestamp"] > latest_state[key]["timestamp"]: This is the freshness gate. Only newer timestamps replace stored state, which enforces latest-update semantics deterministically. Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 17
Source text: latest_state[key] = event Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 19
Source text: session_acc: Dict[str, Dict[str, Any]] = defaultdict( This lazy initializer creates clean per-session accumulators on demand, reducing manual existence checks. Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 20
Source text: lambda: { Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 21
Source text: "pass_count": 0, This initializes the passing user counter for each session. It remains zero if no user crosses the threshold. Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 22
Source text: "pass_sum": 0.0, This initializes the passing score sum in floating-point form so average division behaves consistently. Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 23
Source text: "top_user": None, This initializes top_user as absent. It is intentionally None for sessions where no user passes. Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 24
Source text: "top_score": None, This initializes comparison baseline for selecting the top passing user in constant time per passing record. Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 25
Source text: } Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 26
Source text: ) Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 28
Source text: for (session_id, user_id), record in latest_state.items(): This begins phase two over deduplicated truth records. Aggregation after dedupe is the key correctness boundary. Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 29
Source text: score = float(record["score"]) This normalizes score to numeric form used in thresholding and arithmetic. It avoids type drift in mixed int/float inputs. Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 30
Source text: acc = session_acc[session_id] Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 32
Source text: if score >= pass_score: This threshold branch decides metric participation. Only passing latest records affect pass_count, average, and top_user. Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 33
Source text: acc["pass_count"] += 1 This increments the passing population for the session, defining the denominator of average pass score. Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 34
Source text: acc["pass_sum"] += score This accumulates passing score mass that will later be divided by pass_count to compute the contract average. Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 36
Source text: if acc["top_score"] is None or score > acc["top_score"]: This initializes comparison baseline for selecting the top passing user in constant time per passing record. Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 37
Source text: acc["top_score"] = score Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 38
Source text: acc["top_user"] = user_id This writes the current winning user id for the session. It is coupled with top_score updates for consistency. Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 39
Source text: elif score == acc["top_score"] and user_id < acc["top_user"]: This is deterministic tie-break logic. Equal top scores are resolved lexicographically so tests are stable. Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 40
Source text: acc["top_user"] = user_id This writes the current winning user id for the session. It is coupled with top_score updates for consistency. Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 42
Source text: rows: List[Dict[str, Any]] = [] Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 43
Source text: for session_id, acc in session_acc.items(): Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 44
Source text: pass_count = acc["pass_count"] Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 45
Source text: avg_pass_score = acc["pass_sum"] / pass_count if pass_count else 0.0 This initializes the passing user counter for each session. It remains zero if no user crosses the threshold. Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 46
Source text: rows.append( Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 47
Source text: { Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 48
Source text: "session_id": session_id, Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 49
Source text: "pass_count": pass_count, Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 50
Source text: "avg_pass_score": avg_pass_score, Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 51
Source text: "top_user": acc["top_user"], Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 52
Source text: } Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 53
Source text: ) Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 55
Source text: rows.sort(key=lambda r: (-r["pass_count"], -r["avg_pass_score"], r["session_id"])) Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
### Line 56
Source text: return rows Reasoning anchor: this line belongs to one of the three contracts you must preserve during interviews: latest-state reconstruction, pass-only aggregation, or deterministic ordering.
## Closing Paragraph
If you feel overloaded, collapse the entire question into one mantra: reconstruct latest state per user per session, then aggregate pass metrics, then sort deterministically. Repeat that mantra while coding, and most failure modes disappear.
## Appendix: Full Step-By-Step Walkthrough Narrative
Assume the interviewer asks you to solve this from scratch without writing code immediately. You start by repeating the contract in your own words to confirm alignment. You say that each event is an update, not a final row for aggregation. You say the identity of an update is session_id plus user_id. You say timestamp decides which update survives for each identity key. You say that only surviving latest records can participate in pass metrics. You say top_user is selected only among passers, with lexicographic tie-break. You say sessions with zero passers must still appear as explicit zero rows. You say final sorting is deterministic over three keys in exact order. Now you dry-run with an empty map for latest state. You ingest the first event and insert its key-value pair. You ingest the second event for same key and replace because timestamp is newer. You ingest a third event for a different key and insert normally. You continue this process until every event is processed once. At this stage you can print latest_state to verify phase-one correctness. You fix dedupe first because all metrics depend on that map. Once dedupe is correct, you create per-session accumulators. Each accumulator starts with pass_count zero, pass_sum zero, top_user none, top_score none. You iterate deduped records and route each record to its session accumulator. For each record, you test score against pass_score. If score fails threshold, you skip metric updates but keep session visibility. If score passes threshold, you increment pass_count and add score to pass_sum. Then you compare score with top_score for top_user selection. If score is strictly greater, current user replaces top_user. If score ties top_score, lexicographically smaller user wins. After processing all deduped records, each session accumulator is complete. Now you materialize output rows from accumulators. For each session, average is pass_sum divided by pass_count when pass_count is positive. For each session with pass_count zero, average is explicitly 0.0. For each session with pass_count zero, top_user remains None. Then you perform one deterministic sort using all three keys. Primary key uses negative pass_count for descending order. Secondary key uses negative average for descending order. Tertiary key uses raw session_id for ascending lexical order. At this point output rows are contract-compliant. Then you do a verbal verification against the sample input-output pair. You confirm that overwritten scores are not double-counted. You confirm that failing latest scores can erase earlier passing states. You confirm that zero-pass sessions are visible in final output. You confirm that tie scenarios are deterministic. If interviewer asks for complexity, you answer in cardinality terms. Dedupe is linear in number of events. Aggregation is linear in number of deduped keys. Sorting is session_count times log of session_count. Memory is proportional to deduped keys plus sessions. If interviewer asks where bugs happen most, you mention three hotspots. Hotspot two is aggregating before dedupe. Hotspot three is missing tie-break logic. If interviewer asks for production extension, you propose incremental updates. You keep latest_state in a store and update session aggregates by delta. On each new event, you remove old contribution and apply new contribution. This preserves the same semantics while enabling streaming behavior. If interviewer asks about equal timestamps, you declare policy clearly. You can keep strict-greater replacement for first-seen-wins. Either is acceptable when declared and tested. If interviewer asks for test strategy, you propose scenario-first tests. One test where passing is overwritten by failing. One test with top-score tie among passers. One test with complete metric ties requiring session_id ordering. One test with empty input returning empty output. This appendix is intentionally narrative so you can read it like a script. If you rehearse this exact flow, the coding round becomes deterministic.
