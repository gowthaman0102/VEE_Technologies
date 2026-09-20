"use client";

import { Toaster, toast } from "sonner";

export function AppToaster() {
  return (
    <Toaster
      position="top-right"
      toastOptions={{
        style: {
          background: "var(--surface)",
          color: "var(--text)",
          border: "1px solid var(--border)",
          borderRadius: "10px",
          fontFamily: "var(--font-sans)",
        },
      }}
    />
  );
}

export { toast };
