"use client";

import { useState } from "react";
import { focusRing } from "@/components/ui/button-styles";
import { ArrowRight } from "lucide-react";
import { ArticleReaderModal } from "./article-reader-modal";

type ArticleViewButtonProps = {
  articleId: number;
  sourceUrl?: string | null;
  sourceName?: string | null;
  className?: string;
};

export function ArticleViewButton({
  articleId,
  sourceName,
  className = "",
}: ArticleViewButtonProps) {
  const [isOpen, setIsOpen] = useState(false);

  const ariaLabel = sourceName
    ? `View article from ${sourceName}`
    : "View article";

  return (
    <>
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        aria-label={ariaLabel}
        className={`inline-flex items-center justify-center rounded-[8px] border border-[#DFE9F0] bg-white px-3.5 py-1.5 text-[13px] font-bold text-[#0A1730] transition-colors duration-150 hover:bg-[#F4F9FC] hover:border-[#C0D4E4] ${focusRing} ${className}`}
      >
        View <ArrowRight size={14} className="ml-1.5" aria-hidden="true" />
      </button>

      {isOpen && (
        <ArticleReaderModal
          articleId={articleId}
          onClose={() => setIsOpen(false)}
        />
      )}
    </>
  );
}
