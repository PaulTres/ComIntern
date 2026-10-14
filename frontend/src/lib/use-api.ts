"use client";

import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";

/** Minimal data-fetching hook: loads `path` when it changes and exposes a reload function. */
export function useApi<T>(path: string) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let cancelled = false;
    api<T>(path).then(
      (result) => {
        if (cancelled) return;
        setData(result);
        setError(null);
      },
      (e: Error) => !cancelled && setError(e),
    );
    return () => {
      cancelled = true;
    };
  }, [path, version]);

  const reload = useCallback(() => setVersion((v) => v + 1), []);

  return { data, error, reload };
}
