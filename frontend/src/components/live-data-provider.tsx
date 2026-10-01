"use client";

import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from "react";
import { API_BASE_URL } from "@/lib/api";

export type LiveStatus = "live" | "processing" | "delayed" | "offline";

interface LiveDataContextProps {
  status: LiveStatus;
  dataVersion: number;
  lastArticleInsertedAt: string | null;
  serverTime: string | null;
  lastPollStartedAt: string | null;
  lastPollCompletedAt: string | null;
}

const LiveDataContext = createContext<LiveDataContextProps>({
  status: "offline",
  dataVersion: 0,
  lastArticleInsertedAt: null,
  serverTime: null,
  lastPollStartedAt: null,
  lastPollCompletedAt: null,
});

export const useLiveData = () => useContext(LiveDataContext);

export function LiveDataProvider({ children }: { children: React.ReactNode }) {
  const [contextVal, setContextVal] = useState<LiveDataContextProps>({
    status: "offline",
    dataVersion: 0,
    lastArticleInsertedAt: null,
    serverTime: null,
    lastPollStartedAt: null,
    lastPollCompletedAt: null,
  });

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/live/status`, { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        setContextVal(prev => {
          if (prev.dataVersion !== data.data_version || prev.status !== data.status) {
            return {
              status: data.status,
              dataVersion: data.data_version,
              lastArticleInsertedAt: data.last_article_inserted_at,
              serverTime: data.server_time,
              lastPollStartedAt: data.last_poll_started_at,
              lastPollCompletedAt: data.last_poll_completed_at,
            };
          }
          return prev;
        });
      } else {
        setContextVal(prev => prev.status !== "offline" ? { ...prev, status: "offline" } : prev);
      }
    } catch {
      setContextVal(prev => prev.status !== "offline" ? { ...prev, status: "offline" } : prev);
    }
  }, []);

  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void fetchStatus();

    let sseSource: EventSource | null = null;
    let fallbackInterval: NodeJS.Timeout | null = null;

    const setupSSE = () => {
      sseSource = new EventSource(`${API_BASE_URL}/live/stream`);
      
      sseSource.onmessage = () => {
        // Debounce fetches to prevent bursting when multiple events fire instantly
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
        timeoutRef.current = setTimeout(() => {
          void fetchStatus();
        }, 300); // 300ms coalesce
      };

      sseSource.onerror = () => {
        sseSource?.close();
        if (!fallbackInterval) {
          fallbackInterval = setInterval(fetchStatus, 2000);
        }
      };

      sseSource.onopen = () => {
        if (fallbackInterval) {
          clearInterval(fallbackInterval);
          fallbackInterval = null;
        }
      };
    };

    setupSSE();

    return () => {
      if (sseSource) sseSource.close();
      if (fallbackInterval) clearInterval(fallbackInterval);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [fetchStatus]);

  return (
    <LiveDataContext.Provider value={contextVal}>
      {children}
    </LiveDataContext.Provider>
  );
}
