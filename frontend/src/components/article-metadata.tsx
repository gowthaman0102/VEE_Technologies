import { formatArticleTimestamp } from "@/lib/format";

type ArticleMetadataProps = {
  publisherName: string;
  publishedAt?: string | null;
  collectedAt?: string | null;
  compact?: boolean; // Deprecated, prefer variant="default"
  variant?: "default" | "grid";
};

export function ArticleMetadata({
  publisherName,
  publishedAt,
  collectedAt,
  compact = false,
  variant = "default",
}: ArticleMetadataProps) {
  if (variant === "grid") {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-widest text-primary/80">
            Publisher
          </p>
          <p className="mt-1.5 text-[15px] font-semibold text-text">
            {publisherName || "Unavailable"}
          </p>
        </div>
        <div>
          <p className="text-[10px] font-bold uppercase tracking-widest text-primary/80">
            Published
          </p>
          <time dateTime={publishedAt ?? undefined} className="mt-1.5 block text-[15px] font-semibold text-text">
            {publishedAt ? formatArticleTimestamp(publishedAt) : "Unavailable"}
          </time>
        </div>
        <div>
          <p className="text-[10px] font-bold uppercase tracking-widest text-primary/80">
            Added to Nova Cops
          </p>
          <time dateTime={collectedAt ?? undefined} className="mt-1.5 block text-[15px] font-semibold text-text">
            {collectedAt ? formatArticleTimestamp(collectedAt) : "Unavailable"}
          </time>
        </div>
      </div>
    );
  }

  return (
    <div className={compact ? "space-y-1" : "space-y-2"}>
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">
        {publisherName}
      </p>
      <div className={`flex flex-wrap gap-x-4 gap-y-1 text-muted ${compact ? "text-xs" : "text-sm"}`}>
        <time dateTime={publishedAt ?? undefined}>
          Published: {formatArticleTimestamp(publishedAt, "Published time unavailable")}
        </time>
        <time dateTime={collectedAt ?? undefined}>
          Added to Nova Cops: {formatArticleTimestamp(collectedAt, "Added time unavailable")}
        </time>
      </div>
    </div>
  );
}
