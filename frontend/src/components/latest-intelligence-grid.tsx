import { LatestArticleCard } from "./latest-article-card";
import { EmptyState } from "./ui/empty-state";
import type { DashboardIntelligenceItem } from "@/lib/api";
import { FileText } from "lucide-react";
import Link from "next/link";

export function LatestIntelligenceGrid({ items }: { items: DashboardIntelligenceItem[] }) {
  return (
    <div className="w-full rounded-[16px] bg-white border border-border shadow-[0_8px_24px_rgba(23,54,76,0.04)] p-5 lg:p-6 mb-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6">
        <div className="flex items-start sm:items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[10px] bg-primary-soft text-primary">
            <FileText size={20} strokeWidth={2} />
          </div>
          <div>
            <h2 className="text-base font-bold text-text">Latest Intelligence</h2>
            <p className="text-[13px] text-muted">Most recent and important signals from global media sources.</p>
          </div>
        </div>
        <Link 
          href="/intelligence" 
          className="mt-4 sm:mt-0 inline-flex shrink-0 items-center justify-center rounded-[10px] border border-border bg-white px-4 py-2 text-[13px] font-bold text-text transition-colors hover:bg-surface-raised hover:border-primary"
        >
          View all
        </Link>
      </div>

      {items.length === 0 ? (
        <EmptyState title="No processed intelligence" description="No recent intelligence is available yet." />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((item) => (
            <LatestArticleCard key={`${item.company_id}-${item.article_id}`} article={item} />
          ))}
        </div>
      )}
    </div>
  );
}
