import { DependencyList, useCallback, useEffect, useRef, useState } from "react";

type UseApiDataOptions<TRaw, TData> = {
  deps?: DependencyList;
  initialData?: TData;
  transform?: (raw: TRaw) => TData;
};

type UseApiDataResult<TData> = {
  data: TData | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  clearError: () => void;
};

/**
 * Reusable data-fetch hook with:
 * - mount/dependency-driven fetch
 * - transform support
 * - loading/error semantics
 * - refetch
 * - unmount/abort protection
 */
export function useApiData<TRaw, TData = TRaw>(
  fetcher: (signal?: AbortSignal) => Promise<TRaw>,
  options?: UseApiDataOptions<TRaw, TData>
): UseApiDataResult<TData> {
  const { deps = [], initialData, transform } = options ?? {};

  const [data, setData] = useState<TData | null>(initialData ?? null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mountedRef = useRef(true);
  const activeControllerRef = useRef<AbortController | null>(null);
  const requestSeqRef = useRef(0);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const refetch = useCallback(async () => {
    requestSeqRef.current += 1;
    const requestId = requestSeqRef.current;

    activeControllerRef.current?.abort();
    const controller = new AbortController();
    activeControllerRef.current = controller;

    setLoading(true);
    setError(null);

    try {
      const raw = await fetcher(controller.signal);
      if (!mountedRef.current || requestId != requestSeqRef.current) {
        return;
      }
      const nextData = transform ? transform(raw) : (raw as unknown as TData);
      setData(nextData);
    } catch (err) {
      if (!mountedRef.current || requestId != requestSeqRef.current) {
        return;
      }
      const isAbort =
        err instanceof DOMException && err.name === "AbortError";
      if (!isAbort) {
        setError(err instanceof Error ? err.message : String(err));
      }
    } finally {
      if (!mountedRef.current || requestId != requestSeqRef.current) {
        return;
      }
      setLoading(false);
    }
  }, [fetcher, transform]);

  useEffect(() => {
    mountedRef.current = true;
    // Requirement: useEffect + inner async function (effect callback itself not async).
    const run = async () => {
      await refetch();
    };
    void run();

    return () => {
      mountedRef.current = false;
      activeControllerRef.current?.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refetch, ...deps]);

  return {
    data,
    loading,
    error,
    refetch,
    clearError,
  };
}
