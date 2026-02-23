# Context 00: How To Read Agentex As Interview Prep

If you are using a real codebase as study material for interviews, the biggest mistake is reading it linearly and trying to memorize APIs. That approach feels productive but does not transfer well to interviews because interviewers do not ask, "What method name did this repo use?" They ask, "Why did this system choose this pattern, what can go wrong, and how would you fix it under pressure?"

A better way to read this codebase is by failure mode. Pick one category of production failure and then follow it through the stack. For example, if the category is race conditions, you should not stop at one markdown document. You should read the conceptual guide, then find where the runtime path is implemented, then find where tests prove behavior, and finally ask what happens when assumptions fail.

Agentex is a very useful study target because it contains both docs and implementation paths. The docs tell you what the maintainers are trying to guarantee. The code tells you what they can actually guarantee. Any mismatch between those two is excellent interview material.

As you read, maintain a notebook with three columns. Column one is the invariant. Column two is the mechanism. Column three is the regression test. For instance, an invariant might be "no duplicate auth acceptance after invalid token cache poisoning." The mechanism could be short TTL negative entries and no caching of transient backend failures. The regression test could be a scenario where a token is invalid, then rotated to valid, then retried within the old negative TTL window.

This style of reading turns every code section into a reusable interview story. You can restate the problem, explain the mechanism, discuss tradeoffs, and propose tests. That is exactly what strong debugging and backend practical rounds are measuring.

One final reading rule: whenever you see a branch in code that looks overly defensive, assume it was added after a real incident. Defensive branches are not clutter. They are compressed outage history.
