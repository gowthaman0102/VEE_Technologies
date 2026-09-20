import type { ReactNode } from "react";

export function Section({ title, children, className = "", action }: { title: string; children: ReactNode; className?: string; action?: ReactNode }) {
  return (
    <section className={className}>
      <div className="mb-4 flex items-center justify-between gap-3">
        <h3 className="text-base font-semibold text-text">{title}</h3>
        {action && <div className="shrink-0">{action}</div>}
      </div>
      {children}
    </section>
  );
}

