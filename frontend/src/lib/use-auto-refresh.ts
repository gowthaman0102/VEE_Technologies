"use client";

import {
  useEffect,
  useRef,
} from "react";


type AutoRefreshOptions = {
  enabled?: boolean;
  intervalMs?: number;
};


export function useAutoRefresh(
  refresh: () => Promise<void> | void,
  {
    enabled = true,
    intervalMs = 60_000,
  }: AutoRefreshOptions = {},
) {
  const refreshRef = useRef(refresh);
  const runningRef = useRef(false);
  const lastRefreshRef = useRef(0);

  useEffect(() => {
    refreshRef.current = refresh;
  }, [refresh]);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    let cancelled = false;

    lastRefreshRef.current = Date.now();

    async function runRefresh() {
      if (
        cancelled
        || runningRef.current
        || document.visibilityState !== "visible"
      ) {
        return;
      }

      runningRef.current = true;

      try {
        await refreshRef.current();

        if (!cancelled) {
          lastRefreshRef.current = Date.now();
        }
      } finally {
        runningRef.current = false;
      }
    }

    function handleVisibilityChange() {
      if (
        document.visibilityState === "visible"
        && Date.now() - lastRefreshRef.current
          >= intervalMs
      ) {
        void runRefresh();
      }
    }

    void runRefresh();

    const interval = window.setInterval(
      () => {
        void runRefresh();
      },
      intervalMs,
    );

    document.addEventListener(
      "visibilitychange",
      handleVisibilityChange,
    );

    return () => {
      cancelled = true;

      window.clearInterval(interval);

      document.removeEventListener(
        "visibilitychange",
        handleVisibilityChange,
      );
    };
  }, [
    enabled,
    intervalMs,
  ]);
}
