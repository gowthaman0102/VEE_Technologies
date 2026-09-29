import { TriangleAlert } from "lucide-react";
import type { ClientConfiguration, SourceAnalyticsResponse } from "@/lib/api";

type PublisherSource = SourceAnalyticsResponse["sources"][number];

export function PublisherReliabilityTable({ sources, config }: { sources: PublisherSource[] | null, config: ClientConfiguration | null }) {
  if (!sources || !config) return null;

  return (
    <section className="mt-5 rounded-2xl border border-[rgba(90,72,160,0.12)] bg-white shadow-[0_8px_20px_rgba(65,50,120,0.06)] overflow-hidden">
      <div className="border-b border-border px-6 py-4">
        <h2 className="text-[16px] font-semibold text-text">Publisher reliability scoring</h2>
      </div>
      
      {sources.length === 0 ? (
        <div className="p-8 text-center text-sm text-muted bg-[#FAF9FF]">
          No publisher data available for the selected period.
        </div>
      ) : (
        <div className="max-h-[400px] overflow-y-auto relative">
          <table className="w-full text-left text-[12px]">
            <thead className="sticky top-0 z-10 bg-[#FAF9FF] text-[10px] font-bold uppercase tracking-[0.12em] text-muted shadow-sm">
              <tr>
                <th className="px-6 py-3 font-bold border-b border-border">Publisher</th>
                <th className="px-6 py-3 font-bold border-b border-border">Articles</th>
                <th className="px-6 py-3 font-bold border-b border-border">Avg risk score</th>
                <th className="px-6 py-3 font-bold border-b border-border">High &amp; critical rate</th>
                <th className="px-6 py-3 font-bold border-b border-border text-right">Risk level</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {[...sources].sort((a, b) => b.article_count - a.article_count).map((source) => {
                const name = source.source_name || "Unknown";
                const publisherUrl = getPublisherUrl(name, source.publisher_domain);
                const highRiskRate = source.risk_assessed_count > 0
                  ? ((source.critical_risk_count + source.high_risk_count) / source.risk_assessed_count) * 100
                  : null;
                const riskLevels = [
                  { label: "Critical", count: source.critical_risk_count },
                  { label: "High", count: source.high_risk_count },
                  { label: "Medium", count: source.medium_risk_count },
                  { label: "Low", count: source.low_risk_count },
                ];
                const dominantRisk = riskLevels.reduce((current, level) => level.count > current.count ? level : current);
                const riskLevel = source.risk_assessed_count > 0 && dominantRisk.count > 0 ? dominantRisk.label : "Unrated";
                const riskTextClass = {
                  Critical: "text-[#991b1b]",
                  High: "text-red-700",
                  Medium: "text-amber-800",
                  Low: "text-green-700",
                  Unrated: "text-muted",
                }[riskLevel];
                const riskDotClass = {
                  High: "bg-red-600",
                  Medium: "bg-amber-500",
                  Low: "bg-green-600",
                }[riskLevel];
                
                return (
                  <tr key={name} className="bg-white">
                    <td className="px-6 py-4">
                      {publisherUrl ? (
                        <a
                          href={publisherUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="group inline-flex items-center gap-1.5 font-semibold text-primary hover:underline underline-offset-2"
                          title={`Visit ${name}`}
                        >
                          {name}
                          <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="opacity-0 group-hover:opacity-100 transition-opacity shrink-0"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                        </a>
                      ) : (
                        <span className="font-semibold text-text-body">{name}</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-text">{source.article_count.toLocaleString()}</td>
                    <td className="px-6 py-4 text-text">{source.average_risk_score?.toFixed(1) ?? "—"}</td>
                    <td className="px-6 py-4 text-text">{highRiskRate === null ? "—" : `${highRiskRate.toFixed(0)}%`}</td>
                    <td className="px-6 py-4 text-right">
                      <span title={`Most frequent stored article severity across ${source.risk_assessed_count} scored articles`} className={`inline-flex items-center gap-1.5 text-[10px] font-bold ${riskTextClass}`}>
                        {riskLevel === "Critical" ? <TriangleAlert size={12} strokeWidth={2.5} aria-hidden="true" /> : riskDotClass ? <span className={`h-2 w-2 rounded-full ${riskDotClass}`} aria-hidden="true" /> : null}
                        {riskLevel}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

const PUBLISHER_DOMAINS: Record<string, string> = {
  "the next web": "thenextweb.com",
  "the hindu": "thehindu.com",
  "the new york times": "nytimes.com",
  "new york times": "nytimes.com",
  "financial times": "ft.com",
  "financial post": "financialpost.com",
  "the guardian": "theguardian.com",
  "business insider": "businessinsider.com",
  "wall street journal": "wsj.com",
  wsj: "wsj.com",
  bbc: "bbc.com",
  "bbc news": "bbc.com",
  reuters: "reuters.com",
  yahoo: "yahoo.com",
  "yahoo news": "news.yahoo.com",
  forbes: "forbes.com",
  bloomberg: "bloomberg.com",
  fortune: "fortune.com",
  techcrunch: "techcrunch.com",
  "the verge": "theverge.com",
  cnbc: "cnbc.com",
  cnn: "cnn.com",
  "al jazeera": "aljazeera.com",
  pypi: "pypi.org",
  "pypi.org": "pypi.org",
};

function getPublisherUrl(name: string, publisherDomain?: string | null): string | null {
  if (publisherDomain) {
    try {
      const candidate = publisherDomain.includes("://") ? publisherDomain : `https://${publisherDomain}`;
      const hostname = new URL(candidate).hostname.toLowerCase().replace(/^www\./, "");
      if (hostname && hostname !== "google.com" && !hostname.endsWith(".google.com") && hostname !== "msn.com") {
        return `https://${hostname}`;
      }
    } catch {
      // Ignore malformed source domains and try a known publisher name.
    }
  }

  const cleaned = name
    .trim()
    .toLowerCase()
    .replace(/^(?:google news|newsapi)\s*-\s*/, "")
    .replace(/ official news$/, "");
  const knownDomain = PUBLISHER_DOMAINS[cleaned];
  if (knownDomain) return `https://${knownDomain}`;
  if (/^[a-z0-9-]+(?:\.[a-z0-9-]+)+$/.test(cleaned)) return `https://${cleaned}`;
  return null;
}
