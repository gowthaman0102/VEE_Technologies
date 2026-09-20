"use client";

import Link from "next/link";
import { Search } from "lucide-react";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { ModuleDeck } from "@/components/module-deck";

export function AppShell({ children, companyName }: { children: React.ReactNode; companyName: string }) {
  const router = useRouter();
  const [query, setQuery] = useState("");

  const submitSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const value = query.trim();
    router.push(value ? `/search?q=${encodeURIComponent(value)}` : "/search");
  };

  return (
    <div className="nova-app-shell">
      <header className="nova-header">
        <div className="nova-header-inner">
          <Link href="/" aria-label="Nova Cops Overview" className="nova-brand">
            <span className="nova-brand-mark" aria-hidden="true">N</span>
            <span><strong>NOVA COPS</strong><small>MEDIA INTELLIGENCE</small></span>
            <em>See Further. Understand Sooner.</em>
          </Link>
          <form className="nova-global-search" onSubmit={submitSearch} role="search">
            <Search size={16} aria-hidden="true" />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search monitored intelligence..." aria-label="Search monitored intelligence" />
            <kbd>Enter</kbd>
          </form>
          <div className="nova-company-context" title={companyName ? `Active company: ${companyName}` : "No active company"}>
            <span className="nova-live-dot" aria-hidden="true" />
            <span>{companyName || "No active company"}</span>
          </div>
        </div>
      </header>
      <div className="nova-atmosphere" aria-hidden="true" />
      <ModuleDeck />
      <main id="main-content" className="nova-main">{children}</main>
      <footer className="nova-footer"><span>Nova Cops Media Intelligence</span><span>Near Real-Time Intelligence</span></footer>
    </div>
  );
}