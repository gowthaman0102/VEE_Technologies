'use client';

import { useEffect } from 'react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error(error);
  }, [error]);

  return (
    <div className="flex h-screen w-full flex-col items-center justify-center bg-canvas p-6 text-center">
      <div className="max-w-md space-y-6">
        <h2 className="text-2xl font-bold text-text">Unable to Connect</h2>
        <p className="text-text-body">
          The dashboard couldn&apos;t connect to the backend services. This usually means the API is still starting up or isn&apos;t running.
        </p>
        <div className="rounded-md bg-surface p-4 text-left text-sm text-muted overflow-auto border border-border">
          <code>{error.message}</code>
        </div>
        <button
          onClick={() => reset()}
          className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-primary/90"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
