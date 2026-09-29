"use client";

import Link from "next/link";
import {
  LayoutList,
  ShieldAlert,
  BarChart2,
  Building2,
  Search,
  FileText,
  Settings2,
} from "lucide-react";

const ACTIONS = [
  {
    href: "/intelligence",
    label: "Intelligence",
    description: "Article queue",
    Icon: LayoutList,
  },
  {
    href: "/risk-analytics",
    label: "Risk Analytics",
    description: "Risk signals",
    Icon: ShieldAlert,
  },
  {
    href: "/analytics",
    label: "Analytics",
    description: "Trends & charts",
    Icon: BarChart2,
  },
  {
    href: "/companies",
    label: "Companies",
    description: "Company profiles",
    Icon: Building2,
  },
  {
    href: "/search",
    label: "Search",
    description: "Find articles",
    Icon: Search,
  },
  {
    href: "/reports",
    label: "Reports",
    description: "Generate reports",
    Icon: FileText,
  },
  {
    href: "/article-settings",
    label: "Article Settings",
    description: "Manage settings",
    Icon: Settings2,
  },
] as const;

export function QuickActionsRow() {
  return (
    <section className="mt-8">
      <h2 className="mb-4 text-base font-semibold text-text">Quick actions</h2>
      <div className="flex gap-3 overflow-x-auto pb-1 scrollbar-none">
        {ACTIONS.map(({ href, label, description, Icon }) => (
          <Link
            key={href}
            href={href}
            className="group flex min-w-0 flex-1 flex-col items-center gap-2 rounded-xl border border-border bg-surface px-3 py-4 text-center shadow-[0_1px_2px_rgba(28,23,52,0.06)] transition-all hover:border-primary/40 hover:bg-primary-soft hover:shadow-[0_2px_8px_rgba(62,47,130,0.10)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
          >
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary-soft text-primary transition-colors group-hover:bg-primary group-hover:text-white">
              <Icon size={18} aria-hidden="true" />
            </span>
            <span className="w-full">
              <span className="block text-[13px] font-semibold text-text leading-tight group-hover:text-primary">
                {label}
              </span>
              <span className="mt-0.5 block text-[11px] text-muted leading-tight">
                {description}
              </span>
            </span>
          </Link>
        ))}
      </div>
    </section>
  );
}
