"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  createWatchlistItem,
  deleteWatchlistItem,
  getActiveCompany,
  getWatchlist,
  updateWatchlistItem,
  WatchlistItem,
} from "@/lib/api";

export default function WatchlistPage() {
  const [companyId, setCompanyId] = useState<number | null>(null);
  const [companyName, setCompanyName] = useState("");
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [itemType, setItemType] = useState("keyword");
  const [itemName, setItemName] = useState("");
  const [value, setValue] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    try {
      const company = await getActiveCompany();
      setCompanyId(company.id);
      setCompanyName(company.name);
      const data = await getWatchlist(company.id);
      setItems(data.items);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to load watchlist.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(); }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (companyId === null || !itemName.trim() || !value.trim()) return;
    await createWatchlistItem({ company_id: companyId, item_type: itemType, item_name: itemName, value });
    setItemName("");
    setValue("");
    await load();
  }

  async function toggle(item: WatchlistItem) {
    await updateWatchlistItem(item.id, { is_active: !item.is_active });
    await load();
  }

  async function remove(item: WatchlistItem) {
    await deleteWatchlistItem(item.id);
    await load();
  }

  return (
    <main className="px-6 py-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-8"><p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-400">Watchlist</p><h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">{companyName || "Monitoring Watchlist"}</h2></div>
        {error && <p className="mb-5 rounded-xl border border-red-900 bg-red-950/30 p-4 text-sm text-red-300">{error}</p>}
        <form onSubmit={submit} className="grid gap-3 rounded-2xl border border-slate-800 bg-slate-900/70 p-5 md:grid-cols-4">
          <select value={itemType} onChange={(event) => setItemType(event.target.value)} className="rounded-lg border border-slate-700 bg-slate-950 p-3 text-white"><option value="keyword">Keyword</option><option value="topic">Topic</option><option value="source">Source</option><option value="risk_category">Risk category</option><option value="impact_category">Impact category</option></select>
          <input value={itemName} onChange={(event) => setItemName(event.target.value)} placeholder="Item name" className="rounded-lg border border-slate-700 bg-slate-950 p-3 text-white" />
          <input value={value} onChange={(event) => setValue(event.target.value)} placeholder="Match value" className="rounded-lg border border-slate-700 bg-slate-950 p-3 text-white" />
          <button className="rounded-lg bg-cyan-400 p-3 font-semibold text-slate-950">Add item</button>
        </form>
        <div className="mt-6 space-y-4">{loading ? <p className="text-slate-400">Loading watchlist...</p> : items.length === 0 ? <div className="rounded-2xl border border-dashed border-slate-700 p-10 text-center text-slate-400">No watchlist items configured yet.</div> : items.map((item) => <article key={item.id} className="flex flex-col gap-4 rounded-2xl border border-slate-800 bg-slate-900/70 p-5 md:flex-row md:items-center md:justify-between"><div><span className="rounded-full border border-cyan-900 bg-cyan-950/30 px-3 py-1 text-xs font-semibold text-cyan-300">{item.item_type.toUpperCase()}</span><p className="mt-3 text-lg text-white">{item.item_name}: {item.value}</p></div><div className="flex gap-2"><button onClick={() => void toggle(item)} className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300">{item.is_active ? "Disable" : "Enable"}</button><button onClick={() => void remove(item)} className="rounded-lg border border-red-900 px-3 py-2 text-sm text-red-300">Delete</button></div></article>)}</div>
      </div>
    </main>
  );
}
