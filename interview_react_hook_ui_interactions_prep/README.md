# React Hook + UI Interaction Prep

This folder is a standalone frontend practice solution for:

- reusable custom hook for API data fetching
- loading/error/refetch behavior
- response transformation
- modal open/close wiring
- collapsible list wiring
- button-driven interactions

## Implemented requirements

## Custom hook (`src/hooks/useApiData.ts`)

- calls API on mount with `useEffect` + inner async function
- supports optional transform function
- returns `{ data, loading, error, refetch, clearError }`
- handles loading/error transitions
- supports unmount safety via `AbortController` + mounted check

## UI interactions (`src/App.tsx`)

- `Open Modal` / `Close` (modal state)
- `Refresh Data` (hook `refetch`)
- `Clear Error` (hook `clearError`)
- `Increment Counter` (local counter state)
- `Toggle List` (expand/collapse list)
- loading + error shown near list
- collapsed state shows summary (`N items hidden`)

## Mock API (`src/api/mockApi.ts`)

- `getItems()` returns mocked data with delay
- occasional failure to exercise error paths

## Run

```bash
npm install
npm run dev
```

Open the local Vite URL shown in terminal (usually `http://localhost:5173`).

## Notes

- The hook is endpoint-agnostic and can be reused with different fetchers/transforms.
- In real apps, move API modules and hook tests into separate packages/modules.
