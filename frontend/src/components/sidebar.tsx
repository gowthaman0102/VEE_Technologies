"use client";

import Link from "next/link";
import {
  usePathname,
} from "next/navigation";


const navigation = [
  {
    label: "Overview",
    href: "/",
  },
  {
    label: "Intelligence",
    href: "/intelligence",
  },
  {
    label: "Risk Analytics",
    href: "/risk",
  },
  {
    label: "Analytics",
    href: "/analytics",
  },
  {
    label: "Alerts & SLA",
    href: "/alerts",
  },
  {
    label: "Companies",
    href: "/companies",
  },
  {
    label: "Watchlist",
    href: "/watchlist",
  },
  {
    label: "Reports",
    href: "/reports",
  },
  {
    label: "Search",
    href: "/search",
  },
  {
    label: "Event Clusters",
    href: "/event-clusters",
  },
];


export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden min-h-screen w-64 shrink-0 border-r border-slate-800 bg-slate-950 lg:block">
      <div className="flex h-full flex-col">
        <div className="border-b border-slate-800 px-6 py-6">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">
            VEE Technologies
          </p>

          <h2 className="mt-2 text-lg font-semibold text-white">
            Media Intelligence
          </h2>
        </div>

        <nav className="flex-1 space-y-2 px-4 py-6">
          {navigation.map((item) => {
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(
                    item.href,
                  );

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`block rounded-xl px-4 py-3 text-sm font-medium transition ${
                  isActive
                    ? "border border-cyan-900/60 bg-cyan-950/30 text-cyan-300"
                    : "border border-transparent text-slate-300 hover:bg-slate-900 hover:text-white"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-slate-800 px-6 py-5">
          <p className="text-xs text-slate-500">
            AI Agents & Near Real-Time Intelligence
          </p>
        </div>
      </div>
    </aside>
  );
}
