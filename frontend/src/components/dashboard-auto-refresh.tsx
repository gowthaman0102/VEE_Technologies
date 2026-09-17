"use client";

import {
  useRouter,
} from "next/navigation";

import {
  useAutoRefresh,
} from "@/lib/use-auto-refresh";


export function DashboardAutoRefresh() {
  const router = useRouter();

  useAutoRefresh(
    () => {
      router.refresh();
    },
    {
      intervalMs: 60_000,
    },
  );

  return null;
}
