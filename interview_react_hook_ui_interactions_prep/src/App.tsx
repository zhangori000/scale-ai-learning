import { useMemo, useState } from "react";

import { RawItem, getItems } from "./api/mockApi";
import { useApiData } from "./hooks/useApiData";

type UiItem = {
  id: number;
  title: string;
  tier: "high" | "medium" | "low";
};

function transformItems(raw: RawItem[]): UiItem[] {
  return raw.map((item) => ({
    id: item.id,
    title: `${item.name} (score: ${item.score})`,
    tier: item.score >= 85 ? "high" : item.score >= 70 ? "medium" : "low",
  }));
}

export default function App() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isListExpanded, setIsListExpanded] = useState(true);
  const [counter, setCounter] = useState(0);

  const { data, loading, error, refetch, clearError } = useApiData<
    RawItem[],
    UiItem[]
  >(getItems, {
    transform: transformItems,
  });

  const items = data ?? [];
  const hiddenSummary = useMemo(
    () => `${items.length} item${items.length === 1 ? "" : "s"} hidden`,
    [items.length]
  );

  return (
    <div className="page">
      <h1>Hook + UI Interaction Practice</h1>

      <div className="button-row">
        <button onClick={() => setIsModalOpen(true)}>Open Modal</button>
        <button onClick={() => void refetch()}>Refresh Data</button>
        <button onClick={clearError}>Clear Error</button>
        <button onClick={() => setCounter((x) => x + 1)}>Increment Counter</button>
        <button onClick={() => setIsListExpanded((x) => !x)}>
          {isListExpanded ? "Collapse List" : "Expand List"}
        </button>
      </div>

      <div className="meta">
        <span>Counter: {counter}</span>
      </div>

      <section className="panel">
        <h2>Items</h2>
        {loading && <p className="loading">Loading data...</p>}
        {error && <p className="error">Error: {error}</p>}

        {!isListExpanded ? (
          <p className="summary">{hiddenSummary}</p>
        ) : (
          <ul>
            {items.map((item) => (
              <li key={item.id}>
                {item.title} <span className={`tier ${item.tier}`}>{item.tier}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      {isModalOpen && (
        <div className="modal-backdrop" role="presentation" onClick={() => setIsModalOpen(false)}>
          <div
            className="modal"
            role="dialog"
            aria-modal="true"
            onClick={(e) => e.stopPropagation()}
          >
            <h3>Modal Placeholder</h3>
            <p>This modal is controlled by component state.</p>
            <button onClick={() => setIsModalOpen(false)}>Close</button>
          </div>
        </div>
      )}
    </div>
  );
}
