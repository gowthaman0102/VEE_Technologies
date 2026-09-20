"use client";

import { focusRing } from "@/components/ui/button-styles";
import { ArrowRight } from "lucide-react";

type ArticleViewButtonProps = {
  articleId: number;
  sourceUrl?: string | null;
  sourceName?: string | null;
  className?: string;
};

export function ArticleViewButton({
  sourceName,
  sourceUrl,
  className = "",
}: ArticleViewButtonProps) {
  const ariaLabel = sourceName
    ? `View article from ${sourceName}`
    : "View article";

  return (
      <a
        href={sourceUrl ?? undefined}
        aria-label={ariaLabel}
        className={`inline-flex items-center justify-center rounded-[8px] border border-border bg-white px-3.5 py-1.5 text-[13px] font-bold text-text transition-colors duration-150 hover:bg-surface-raised hover:border-primary ${focusRing} ${className}`}
      >
        View <ArrowRight size={14} className="ml-1.5" aria-hidden="true" />
      </a>
  );
}
