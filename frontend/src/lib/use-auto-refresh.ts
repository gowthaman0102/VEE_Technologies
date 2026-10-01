"use client";

import {
  useEffect,
  useRef,
} from "react";
import { useLiveData } from "@/components/live-data-provider";

type AutoRefreshOptions = {
  enabled?: boolean;
  intervalMs?: number; // kept for backwards compatibility but ignored for live pushes
};

export function useAutoRefresh(
  refresh: () => Promise<void> | void,
  {
    enabled = true,
  }: AutoRefreshOptions = {},
) {
  const refreshRef = useRef(refresh);
  const runningRef = useRef(false);
  const { dataVersion } = useLiveData();

  useEffect(() => {
    refreshRef.current = refresh;
  }, [refresh]);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    let cancelled = false;

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
      } finally {
        runningRef.current = false;
      }
    }
    
    // When dataVersion changes, trigger refresh
    void runRefresh();

    function handleVisibilityChange() {
      if (
        document.visibilityState === "visible"
      ) {
        void runRefresh();
      }
    }

    document.addEventListener(
      "visibilitychange",
      handleVisibilityChange,
    );

    return () => {
      cancelled = true;

      document.removeEventListener(
        "visibilitychange",
        handleVisibilityChange,
      );
    };
  }, [
    enabled,
    dataVersion, // Dependency on dataVersion replaces the interval
  ]);
}
