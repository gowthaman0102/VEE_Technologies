"use client";

import { FormEvent, useState } from "react";

type SearchResult = {
  article_id: number;
  title: string;
  source_name: string;
  url: string;
  published_at: string | null;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    const response = await fetch(`${API_BASE_URL}/search/keyword?q=${encodeURIComponent(query)}&limit=50`);
    const data = await response.json();
    setResults(data.results ?? []);
    setLoading(false);
  }

  return (
    <main className="px-6 py-8">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-400">Search</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">Article Discovery</h2>
        </div>
        <form onSubmit={submit} className="flex flex-col gap-3 sm:flex-row">
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search article titles and content" className="min-h-12 flex-1 rounded-xl border border-slate-700 bg-slate-900 px-4 text-white outline-none focus:border-cyan-400" />
          <button type="submit" className="min-h-12 rounded-xl bg-cyan-400 px-6 font-semibold text-slate-950">{loading ? "Searching..." : "Search"}</button>
        </form>
        <div className="mt-6 space-y-4">
          {results.map((result) => (
            <article key={result.article_id} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
              <a href={result.url} target="_blank" rel="noreferrer" className="text-lg font-semibold text-white hover:text-cyan-300">{result.title}</a>
              <p className="mt-2 text-sm text-slate-400">{result.source_name}</p>
            </article>
          ))}
        </div>
      </div>
    </main>
  );
}
