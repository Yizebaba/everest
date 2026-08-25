import { useEffect, useRef, useState } from "react";

import { ApiError } from "@/api/client";

export type FetchStatus = "idle" | "loading" | "success" | "error";

export interface FetchState<T> {
  status: FetchStatus;
  data: T | null;
  error: ApiError | Error | null;
  refetch: () => void;
}

export function useApiFetch<T>(fetcher: () => Promise<T>): FetchState<T> {
  const [status, setStatus] = useState<FetchStatus>("idle");
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | Error | null>(null);
  const [nonce, setNonce] = useState(0);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  useEffect(() => {
    let cancelled = false;
    setStatus("loading");
    setError(null);
    fetcherRef
      .current()
      .then((result) => {
        if (!cancelled) {
          setData(result);
          setStatus("success");
        }
      })
      .catch((reason: unknown) => {
        if (!cancelled) {
          setError(
            reason instanceof Error ? reason : new Error("request failed"),
          );
          setStatus("error");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [nonce]);

  return {
    status,
    data,
    error,
    refetch: () => setNonce((value) => value + 1),
  };
}
