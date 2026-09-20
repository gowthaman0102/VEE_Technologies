"use client";

import type { ReactNode } from "react";

type AmbientKind = "overview" | "intelligence" | "risk" | "analytics" | "companies" | "search" | "reports" | "settings";

const motifs: Record<AmbientKind, ReactNode> = {
  overview: <><circle cx="80" cy="80" r="42" /><path d="M38 80h84M80 38c14 12 21 26 21 42s-7 30-21 42M80 38c-14 12-21 26-21 42s7 30 21 42" /><path d="M48 58c18 9 45 9 64 0M48 102c18-9 45-9 64 0" /><circle cx="119" cy="38" r="5" fill="currentColor" /></>,
  intelligence: <><path d="M22 108c24-36 43-28 61-52 15-20 30-20 55-39" /><path d="M22 126h116" /><circle cx="83" cy="56" r="7" /><circle cx="138" cy="17" r="7" /><path d="M83 56l-20-19M83 56l25 17M108 73l30-56" /></>,
  risk: <><path d="M80 18l48 18v35c0 30-20 49-48 59-28-10-48-29-48-59V36l48-18Z" /><path d="M80 41v28M80 85v2" /><circle cx="80" cy="77" r="4" fill="currentColor" /><path d="M20 126h120M26 112l20-12 19 7 24-27 19 10 25-31" /></>,
  analytics: <><path d="M18 113c20-30 31-15 49-42 17-25 32 23 49-8 10-18 18-26 44-44" /><path d="M18 127h124" /><circle cx="116" cy="63" r="6" fill="currentColor" /><path d="M32 127V98M53 127V86M74 127v-20M95 127V76" /></>,
  companies: <><circle cx="80" cy="37" r="17" /><circle cx="35" cy="111" r="14" /><circle cx="125" cy="111" r="14" /><path d="M68 51L44 99M92 51l24 48M49 111h62" /><path d="M72 37h16M80 29v16" /></>,
  search: <><circle cx="67" cy="65" r="34" /><path d="M91 90l34 34" /><path d="M29 122h32M29 108h17M108 35h29M108 49h18" /><circle cx="67" cy="65" r="16" strokeDasharray="4 6" /></>,
  reports: <><rect x="39" y="18" width="65" height="94" rx="7" /><path d="M54 42h36M54 56h24M54 91V75M68 91V63M82 91V51" /><path d="M106 42l20-14v83H61" /><circle cx="118" cy="28" r="5" fill="currentColor" /></>,
  settings: <><path d="M24 38h112M24 80h112M24 122h112" /><circle cx="55" cy="38" r="9" fill="var(--surface-raised)" /><circle cx="105" cy="80" r="9" fill="var(--surface-raised)" /><circle cx="72" cy="122" r="9" fill="var(--surface-raised)" /><path d="M55 29v18M105 71v18M72 113v18" /></>,
};

export function PageAmbient({ kind }: { kind: AmbientKind }) {
  return (
    <div className={`page-ambient page-ambient-${kind}`} aria-hidden="true">
      <div className="page-ambient-glow" />
      <svg viewBox="0 0 160 145" fill="none" xmlns="http://www.w3.org/2000/svg">
        <g stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
          {motifs[kind]}
        </g>
      </svg>
    </div>
  );
}
