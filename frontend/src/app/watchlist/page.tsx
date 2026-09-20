"use client";

import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle, Building2, Check, FileCheck2, Gavel, GraduationCap,
  Handshake, Layers3, LockKeyhole, Megaphone, Plus, RefreshCcw, Scale,
  Server, Shield, Sparkles, Star, Tag, Trash2, Users, X,
} from "lucide-react";
import {
  ArticleCategory, createArticleCategory, deleteArticleCategory,
  getActiveCompany, getArticleCategories, updateArticleCategory,
} from "@/lib/api";
import { inputClasses, primaryButton, secondaryButton } from "@/components/ui/button-styles";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { toast } from "@/components/ui/toast";
import { PageAmbient } from "@/components/page-ambient";

type Priority = "high" | "medium" | "low";
const PRIORITIES: Array<{ key: Priority; label: string; tint: string; icon: ReactNode }> = [
  { key: "high", label: "High Priority", tint: "border-high-border bg-high-bg", icon: <AlertTriangle className="h-4 w-4" /> },
  { key: "medium", label: "Medium Priority", tint: "border-medium-border bg-medium-bg", icon: <Layers3 className="h-4 w-4" /> },
  { key: "low", label: "Low Priority", tint: "border-low-border bg-low-bg", icon: <Check className="h-4 w-4" /> },
];

function normalizedPriority(priority: string): Priority {
  const value = priority.toLowerCase();
  return value === "high" || value === "critical" ? "high" : value === "low" ? "low" : "medium";
}

function getCategoryIcon(name: string): ReactNode {
  const value = name.toLowerCase();
  if (value.includes("cyber") || value.includes("security") || value.includes("fraud")) return <LockKeyhole className="h-4 w-4" />;
  if (value.includes("ai") || value.includes("safety")) return <Shield className="h-4 w-4" />;
  if (value.includes("regulat")) return <FileCheck2 className="h-4 w-4" />;
  if (value.includes("legal") || value.includes("law")) return <Gavel className="h-4 w-4" />;
  if (value.includes("reputation")) return <Star className="h-4 w-4" />;
  if (value.includes("model") || value.includes("release")) return <Sparkles className="h-4 w-4" />;
  if (value.includes("launch") || value.includes("product")) return <Megaphone className="h-4 w-4" />;
  if (value.includes("partner")) return <Handshake className="h-4 w-4" />;
  if (value.includes("infrastructure") || value.includes("server")) return <Server className="h-4 w-4" />;
  if (value.includes("enterprise") || value.includes("expansion")) return <Building2 className="h-4 w-4" />;
  if (value.includes("education")) return <GraduationCap className="h-4 w-4" />;
  if (value.includes("team") || value.includes("user")) return <Users className="h-4 w-4" />;
  if (value.includes("scale")) return <Scale className="h-4 w-4" />;
  return <Tag className="h-4 w-4" />;
}

function Toggle({ active, onChange, label }: { active: boolean; onChange: () => void; label: string }) {
  return <button type="button" role="switch" aria-checked={active} aria-label={`${active ? "Disable" : "Enable"} ${label}`} onClick={onChange} className={`flex h-7 shrink-0 items-center rounded-full border px-3 text-[10px] font-semibold transition-colors ${active ? "border-primary-border bg-surface text-primary hover:bg-primary-soft" : "border-border bg-surface-raised text-muted hover:border-border-strong hover:text-text"}`}>
    <span>{active ? "Enabled" : "Disabled"}</span>
  </button>;
}

function CategoryCard({ item, onToggle, onRemove }: { item: ArticleCategory; onToggle: () => void; onRemove: () => void }) {
  return <article className={`group flex items-center gap-3 rounded-lg border bg-surface p-3 shadow-[0_1px_2px_rgba(28,23,52,0.06)] transition-colors hover:border-border-strong ${item.is_active ? "border-border" : "border-border bg-surface-raised opacity-70"}`}>
    <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border ${item.is_active ? "border-primary-border bg-primary-soft text-primary" : "border-border bg-surface-raised text-muted"}`}>{getCategoryIcon(item.name)}</div>
    <div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold text-text">{item.name}</p><p className="mt-0.5 text-[11px] text-muted">{item.is_active ? "Active monitoring" : "Currently disabled"}</p></div>
    <Toggle active={item.is_active} onChange={onToggle} label={item.name} />
    <button type="button" onClick={onRemove} aria-label={`Delete ${item.name}`} title="Delete category" className="rounded-lg p-2 text-muted transition-colors hover:bg-critical-bg hover:text-critical focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"><Trash2 className="h-4 w-4" /></button>
  </article>;
}

export default function WatchlistPage() {
  const [companyId, setCompanyId] = useState<number | null>(null);
  const [companyName, setCompanyName] = useState("");
  const [items, setItems] = useState<ArticleCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [categoryName, setCategoryName] = useState("");
  const [priority, setPriority] = useState<Priority>("medium");
  const [adding, setAdding] = useState(false);
  const [viewingPriority, setViewingPriority] = useState<Priority | null>(null);
  const [pendingDelete, setPendingDelete] = useState<ArticleCategory | null>(null);

  async function loadCategories(id: number) { setItems((await getArticleCategories(id)).items); }

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const company = await getActiveCompany();
        if (cancelled) return;
        setCompanyId(company.id); setCompanyName(company.name); await loadCategories(company.id);
      } catch (cause) { if (!cancelled) setError(cause instanceof Error ? cause.message : "Unable to load article settings."); }
      finally { if (!cancelled) setLoading(false); }
    })();
    return () => { cancelled = true; };
  }, []);

  const grouped = useMemo(() => PRIORITIES.reduce<Record<Priority, ArticleCategory[]>>((result, option) => {
    result[option.key] = items.filter((item) => normalizedPriority(item.priority) === option.key); return result;
  }, { high: [], medium: [], low: [] }), [items]);

  async function refresh() {
    if (companyId === null) return;
    setRefreshing(true); setError("");
    try { await loadCategories(companyId); } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to refresh article settings."); }
    finally { setRefreshing(false); }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const name = categoryName.trim();
    if (!name || companyId === null) return;
    if (items.some((item) => item.name.toLowerCase() === name.toLowerCase())) { setError("A category with that name already exists."); return; }
    setAdding(true); setError("");
    try {
      const created = await createArticleCategory({ company_id: companyId, name, priority });
      setItems((current) => [...current, created]); setCategoryName(""); setPriority("medium"); setModalOpen(false);
      toast.success(`Category created: ${created.name}`);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to create article category."); toast.error("Unable to create article category."); }
    finally { setAdding(false); }
  }

  async function toggle(item: ArticleCategory) {
    const next = !item.is_active;
    setItems((current) => current.map((candidate) => candidate.id === item.id ? { ...candidate, is_active: next } : candidate));
    try { await updateArticleCategory(item.id, { is_active: next }); } catch (cause) {
      setItems((current) => current.map((candidate) => candidate.id === item.id ? { ...candidate, is_active: item.is_active } : candidate));
      setError(cause instanceof Error ? cause.message : "Unable to update article category.");
    }
  }

  async function remove(item: ArticleCategory) {
    setPendingDelete(item);
  }

  async function confirmRemove() {
    if (!pendingDelete) return;
    const item = pendingDelete;
    setPendingDelete(null);
    setItems((current) => current.filter((candidate) => candidate.id !== item.id));
    try {
      await deleteArticleCategory(item.id);
      toast.success(`Category deleted: ${item.name}`);
    } catch (cause) {
      setItems((current) => [...current, item]);
      setError(cause instanceof Error ? cause.message : "Unable to delete article category.");
      toast.error("Unable to delete article category.");
    }
  }

  return <main className="relative min-h-[calc(100vh-74px)] overflow-hidden bg-canvas px-4 py-5 sm:px-6 lg:px-8"><PageAmbient kind="settings" /><div className="relative z-10 mx-auto flex min-h-[calc(100vh-7rem)] w-full max-w-[1400px] flex-col">
    <header className="shrink-0 border-b border-border pb-4"><p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary">ARTICLE SETTINGS</p><div className="mt-2 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between"><div><h1 className="text-[36px] font-semibold leading-none tracking-[-0.05em] text-text">{companyName || "OpenAI"}</h1><p className="mt-3 text-sm text-muted">Control which article categories are enabled or disabled for monitoring and display.</p></div><button type="button" onClick={() => { setError(""); setModalOpen(true); }} className={`${primaryButton} shrink-0`}><Plus className="h-4 w-4" /> Add Category</button></div></header>
    {error && <div className="mt-4 shrink-0 rounded-lg border border-critical-border bg-critical-bg px-4 py-3 text-sm text-critical">{error}</div>}
    <div className="mt-4 flex shrink-0 flex-wrap items-center justify-between gap-3"><div className="flex flex-wrap gap-2"><span className="rounded-full border border-border bg-surface px-3 py-1.5 text-xs text-muted"><strong className="text-text">{items.length}</strong> Total</span>{PRIORITIES.map((option) => <span key={option.key} className="rounded-full border border-border bg-surface px-3 py-1.5 text-xs text-muted"><strong className="text-text">{grouped[option.key].length}</strong> {option.key}</span>)}</div><button type="button" onClick={() => void refresh()} disabled={refreshing || loading} className={`${secondaryButton} h-9 px-3 text-xs`}>{refreshing ? <RefreshCcw className="h-3.5 w-3.5 animate-spin" /> : <RefreshCcw className="h-3.5 w-3.5" />} Refresh</button></div>
    <section className="mt-4 grid h-[min(58vh,560px)] min-h-[360px] gap-4 lg:grid-cols-3">{PRIORITIES.map((option) => { const visibleItems = grouped[option.key].slice(0, 5); const hasMore = grouped[option.key].length > visibleItems.length; return <div key={option.key} className={`flex h-full min-w-0 flex-col rounded-2xl border p-3 ${option.tint}`}><div className="flex shrink-0 items-center justify-between px-1 pb-3"><div className="flex items-center gap-2 text-sm font-semibold text-text">{option.icon}{option.label}</div><span className="rounded-full border border-border bg-surface px-2 py-0.5 text-xs font-semibold text-muted">{grouped[option.key].length}</span></div><div className="min-h-0 flex-1 space-y-2 overflow-hidden">{loading ? Array.from({ length: 4 }).map((_, index) => <div key={index} className="h-[66px] animate-pulse rounded-xl border border-border bg-surface/70" />) : visibleItems.length ? visibleItems.map((item) => <CategoryCard key={item.id} item={item} onToggle={() => void toggle(item)} onRemove={() => void remove(item)} />) : <div className="flex h-full min-h-[160px] items-center justify-center rounded-xl border border-dashed border-border bg-surface/40 p-5 text-center text-xs text-muted">No categories in this priority.</div>}</div>{hasMore && <button type="button" onClick={() => setViewingPriority(option.key)} className="mt-3 flex shrink-0 items-center justify-center rounded-lg border border-border bg-surface/80 px-3 py-2 text-xs font-semibold text-primary transition-colors hover:bg-surface">View all {grouped[option.key].length} categories</button>}</div>; })}</section>
  </div>
  {modalOpen && <div className="fixed inset-0 z-50 flex items-center justify-center bg-text/20 p-4" role="presentation" onMouseDown={(event) => { if (event.currentTarget === event.target) setModalOpen(false); }}><div role="dialog" aria-modal="true" aria-labelledby="add-category-title" className="w-full max-w-md rounded-2xl border border-border bg-surface p-5 shadow-[0_20px_60px_rgba(18,32,31,0.18)]"><div className="flex items-start justify-between gap-4"><div><p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-primary">NEW CATEGORY</p><h2 id="add-category-title" className="mt-1 text-xl font-semibold text-text">Add article category</h2></div><button type="button" onClick={() => setModalOpen(false)} aria-label="Close dialog" className="rounded-lg p-2 text-muted hover:bg-surface-raised hover:text-text"><X className="h-4 w-4" /></button></div><form onSubmit={submit} className="mt-5 space-y-4"><label className="block text-sm font-medium text-body">Category name<input autoFocus value={categoryName} onChange={(event) => setCategoryName(event.target.value)} placeholder="e.g. AI Safety" className={`mt-2 ${inputClasses}`} /></label><label className="block text-sm font-medium text-body">Priority<select value={priority} onChange={(event) => setPriority(event.target.value as Priority)} className={`mt-2 ${inputClasses}`}><option value="high">High Priority</option><option value="medium">Medium Priority</option><option value="low">Low Priority</option></select></label><div className="flex items-center gap-3 rounded-xl border border-border bg-surface-raised p-3"><div className="flex h-9 w-9 items-center justify-center rounded-lg border border-primary-border bg-primary-soft text-primary">{getCategoryIcon(categoryName || "New category")}</div><div><p className="text-xs font-semibold text-text">Assigned icon preview</p><p className="text-xs text-muted">Automatically selected from the category name.</p></div></div><div className="flex justify-end gap-2 pt-2"><button type="button" onClick={() => setModalOpen(false)} className={secondaryButton}>Cancel</button><button type="submit" disabled={adding || !categoryName.trim()} className={primaryButton}>{adding ? "Adding..." : "Add Category"}</button></div></form></div></div>}
  {viewingPriority && <div className="fixed inset-0 z-50 flex items-center justify-center bg-text/20 p-4" role="presentation" onMouseDown={(event) => { if (event.currentTarget === event.target) setViewingPriority(null); }}><div role="dialog" aria-modal="true" aria-labelledby="view-categories-title" className="w-full max-w-lg rounded-2xl border border-border bg-surface p-5 shadow-[0_20px_60px_rgba(18,32,31,0.18)]"><div className="flex items-start justify-between gap-4"><div><p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-primary">COMPLETE VIEW</p><h2 id="view-categories-title" className="mt-1 text-xl font-semibold text-text">{PRIORITIES.find((option) => option.key === viewingPriority)?.label}</h2></div><button type="button" onClick={() => setViewingPriority(null)} aria-label="Close complete view" className="rounded-lg p-2 text-muted hover:bg-surface-raised hover:text-text"><X className="h-4 w-4" /></button></div><div className="mt-4 max-h-[60vh] space-y-2 overflow-y-auto">{grouped[viewingPriority].map((item) => <CategoryCard key={item.id} item={item} onToggle={() => void toggle(item)} onRemove={() => void remove(item)} />)}</div></div></div>}
  <ConfirmDialog open={pendingDelete !== null} title="Delete category" description={pendingDelete ? `Are you sure you want to remove the category "${pendingDelete.name}"?` : undefined} confirmLabel="Delete" tone="danger" onConfirm={confirmRemove} onCancel={() => setPendingDelete(null)} />
  </main>;
}
