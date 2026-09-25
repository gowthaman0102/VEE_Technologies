import sys

with open('frontend/src/components/overview-snapshots.tsx', 'a', encoding='utf-8') as f:
    f.write('''
export function PublisherCountrySnapshot({ countries }: { countries: Array<{ country_name: string; article_count: number }> }) {
  const sorted = [...countries].sort((a, b) => b.article_count - a.article_count).slice(0, 5);

  return (
    <div className="rounded-xl border border-border bg-surface p-5 h-full flex flex-col">
      <h3 className="text-[13px] font-bold uppercase tracking-wider text-muted">Publisher Coverage by Country</h3>
      <div className="mt-4 flex-1 flex flex-col justify-center gap-3">
        {sorted.length > 0 ? sorted.map((s, i) => (
          <div key={`${s.country_name}-${i}`} className="flex items-center justify-between">
            <span className="text-sm font-medium text-text-body truncate mr-2">{s.country_name}</span>
            <span className="text-sm font-semibold text-text tabular-nums">{s.article_count}</span>
          </div>
        )) : (
          <p className="text-sm text-muted text-center italic">No country data available.</p>
        )}
      </div>
    </div>
  );
}
''')

with open('frontend/src/components/overview-content.tsx', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    'export function SourceCoverageSnapshot(',
    'export function PublisherCountrySnapshot(props: any); export function SourceCoverageSnapshot('
)
code = code.replace(
    'import { RiskSnapshot, SentimentSnapshot, BusinessImpactSnapshot, SourceCoverageSnapshot, EmergingTopicsSnapshot } from "./overview-snapshots";',
    'import { RiskSnapshot, SentimentSnapshot, BusinessImpactSnapshot, SourceCoverageSnapshot, EmergingTopicsSnapshot, PublisherCountrySnapshot } from "./overview-snapshots";'
)
code = code.replace(
    '<SourceCoverageSnapshot sources={sourcesForSnapshot} />',
    '<SourceCoverageSnapshot sources={sourcesForSnapshot} />\n            <PublisherCountrySnapshot countries={overview.publisher_country_distribution || []} />'
)

with open('frontend/src/components/overview-content.tsx', 'w', encoding='utf-8') as f:
    f.write(code)
