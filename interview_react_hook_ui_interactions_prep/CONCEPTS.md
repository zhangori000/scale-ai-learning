# Concepts and Interview Framing

## 1) Why this question exists

This tests whether you can:

1. design reusable hook logic (not hard-coded one-off fetches)
2. handle async state transitions safely
3. wire multiple UI interactions to state cleanly
4. keep component concerns separated

## 2) Hook design choices

`useApiData` is generic and reusable:

- takes any `fetcher(signal?) => Promise<T>`
- optional `transform(raw) => mappedData`
- exposes:
  - `data`
  - `loading`
  - `error`
  - `refetch`
  - `clearError`

Why this matters:

- Components stay focused on rendering and interactions.
- API details stay encapsulated.

## 3) Async safety details

The hook guards against state update after unmount:

1. abort current request in cleanup (`AbortController`)
2. track mounted state and request sequence
3. ignore stale/aborted responses

This avoids common React warning patterns and race bugs.

## 4) UI interaction wiring pattern

Keep each interaction as explicit state + handler:

- `isModalOpen` -> open/close modal
- `isListExpanded` -> expand/collapse list
- `counter` -> increment button
- `refetch` + `clearError` from hook for data controls

This keeps behavior predictable and easy to debug.

## 5) Loading and error UX

Best practice shown:

- show loading state near relevant content (the list)
- show error message where user expects it
- provide explicit recovery actions:
  - `Refresh Data`
  - `Clear Error`

## 6) Transform layer

API returns raw shape; UI may need a different shape.

Using `transform` in hook keeps mapping logic centralized and testable.
Alternative is mapping in component; both are acceptable in interview if justified.

## 7) Interview talk-track (60-90 seconds)

"I implemented a generic `useApiData` hook that fetches on mount/dependency changes using `useEffect` with an inner async function.  
It supports data transformation, returns loading/error/refetch, and prevents stale state updates using abort + mounted guards.  
In the component, I wired modal visibility, list expand/collapse, and button actions (`refresh`, `clear error`, `increment counter`, `toggle list`) to local state and hook outputs.  
I also render loading/error near the list and show a collapsed summary to satisfy UX requirements."
