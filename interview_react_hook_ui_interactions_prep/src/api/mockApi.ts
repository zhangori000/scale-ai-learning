export type RawItem = {
  id: number;
  name: string;
  score: number;
};

const MOCK_DATA: RawItem[] = [
  { id: 1, name: "Alpha", score: 91 },
  { id: 2, name: "Beta", score: 67 },
  { id: 3, name: "Gamma", score: 84 },
  { id: 4, name: "Delta", score: 55 },
  { id: 5, name: "Epsilon", score: 73 },
];

export async function getItems(signal?: AbortSignal): Promise<RawItem[]> {
  // Simulate network delay and occasional failure.
  await new Promise<void>((resolve, reject) => {
    const timer = setTimeout(resolve, 600);
    if (signal) {
      signal.addEventListener(
        "abort",
        () => {
          clearTimeout(timer);
          reject(new DOMException("Request aborted", "AbortError"));
        },
        { once: true }
      );
    }
  });

  // 15% failure rate to exercise error UI paths.
  if (Math.random() < 0.15) {
    throw new Error("Mock API temporary failure");
  }

  return [...MOCK_DATA];
}
