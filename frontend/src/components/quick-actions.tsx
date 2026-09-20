import Link from "next/link";
import { Search, Bell, BarChart2, FileText, ChevronRight } from "lucide-react";

const QUICK_ACTIONS = [
  {
    title: "Search Intelligence",
    description: "Run keyword or semantic search with advanced filters.",
    href: "/search",
    icon: Search,
    iconColorClass: "bg-primary-soft text-primary",
  },
  {
    title: "Article Settings",
    description: "Enable or disable article categories for monitoring and display.",
    href: "/watchlist",
    icon: Bell,
    iconColorClass: "bg-primary-soft text-primary",
  },
  {
    title: "Analytics",
    description: "Explore intelligence trends across selectable time ranges.",
    href: "/analytics",
    icon: BarChart2,
    iconColorClass: "bg-primary-soft text-primary",
  },
  {
    title: "Reports",
    description: "Generate and download executive intelligence reports.",
    href: "/reports",
    icon: FileText,
    iconColorClass: "bg-primary-soft text-primary",
  },
] as const;

export function QuickActions() {
  return (
    <section className="mt-8 mb-8">
      <h2 className="mb-4 text-base font-semibold text-[#0A1730]">Quick Actions</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {QUICK_ACTIONS.map((action) => {
          const Icon = action.icon;
          return (
            <Link
              key={action.title}
              href={action.href}
              className="group flex flex-col justify-between rounded-xl border border-border bg-surface p-5 shadow-[0_1px_2px_rgba(28,23,52,0.06)] transition-colors duration-150 hover:border-border-strong"
            >
              {/* Top row: icon + chevron */}
              <div className="flex items-start justify-between">
                <div className={`flex h-[44px] w-[44px] items-center justify-center rounded-[10px] ${action.iconColorClass} transition-transform duration-200 group-hover:scale-110`}>
                  <Icon size={22} strokeWidth={2} />
                </div>
                  <ChevronRight
                  size={18}
                  className="text-border-strong transition-transform group-hover:translate-x-0.5 group-hover:text-primary"
                />
              </div>

              {/* Title + description */}
              <div className="mt-5">
                <p className="text-[15px] font-semibold text-text leading-tight">{action.title}</p>
                <p className="mt-2 text-[13px] leading-snug text-muted font-medium">
                  {action.description}
                </p>
              </div>
            </Link>
          );
        })}
      </div>
    </section>
  );
}
