export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded-md bg-surface-sunken motion-reduce:animate-none ${className}`}
      aria-hidden="true"
    />
  );
}
