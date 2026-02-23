# Day 13 - Code: Interview Readiness and "Standard Libs"

How do you write "Scale-Level" code in 60 minutes? This is a **Developer Productivity** lesson.

## 1. The Scenario
Scale AI's interviewers want to see "Professional Python." This means:
1.  **Type Hints:** Use `str`, `int`, `Optional`, `List`.
2.  **Standard Libraries:** Use `collections`, `itertools`, `bisect`, `heapq`.
3.  **Clean Exceptions:** Don't just `raise Exception`. Use `ValueError`, `KeyError`, `HTTPException`.

---

## 2. The Solution: The "Interview Toolbox"
You don't want to "Re-invent" a Priority Queue or a Sliding Window. 

### The "Scale AI" Standard Libs:
1.  **`collections.defaultdict(int)`**: For counting (Day 07!).
2.  **`collections.deque(maxlen=100)`**: For "Sliding Windows" (e.g. "Last 100 events").
3.  **`heapq.heappush(h, x)`**: For "Top K" leaderboards (Day 13!).
4.  **`itertools.groupby(data)`**: For "Batching" events by `tenant_id` (Day 03!).
5.  **`bisect.bisect_left(data, x)`**: For fast "Binary Search" in sorted lists (Day 10!).

### The "Standard" Implementation for a "Top 10" Leaderboard:
```python
import heapq

def get_top_10(scores: dict):
    # 1. HEAP: A 'Min-Heap' of the top 10 scores
    # O(N log 10) complexity! Much faster than sorting.
    h = []
    for user, score in scores.items():
        if len(h) < 10:
            heapq.heappush(h, (score, user))
        elif score > h[0][0]:
            heapq.heapreplace(h, (score, user))
    
    # 2. SORT: Just the 10 results at the end
    return sorted(h, reverse=True)
```

---

## 3. 🧠 Key Teaching Points:
*   **The "Standard Library" Rule**: In an interview, if you use a standard library instead of a manual loop, you're "Signaling" that you're an experienced engineer who knows their tools. 
*   **Performance vs. Simplicity**: For 100 items, `sorted()` is fine. For 10,000,000 items, `heapq` is required. **Know the Big-O.**
*   **Memory Efficiency**: `deque(maxlen=N)` is much safer than `list.append()` because it automatically "Drops" old items. This prevents **OOM** errors (Day 02 lesson!).
*   **FDE Tip**: When an interviewer says "Find the median of a stream of numbers," your first response should be: "I would use **Two Heaps (a Min-Heap and a Max-Heap)** to track the median in O(log N) time."
*   **Scale's Best Practice**: For 99% of "Algorithm" problems, the answer is a **Heap**, a **Hash Map**, or a **Double-Ended Queue**.
*   **The "Type Hint" Habit**: Always start your interview code with `def my_func(data: List[int]) -> int:`. It shows you care about **Correctness and Maintainability**.
*   **The "Pydantic" Habit**: If the problem involves JSON, use `BaseModel`. It shows you care about **Validation** (Day 00 lesson!).
