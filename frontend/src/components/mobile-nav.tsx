"use client";

import Link from "next/link";
import { Menu, X } from "lucide-react";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { navigation } from "@/lib/navigation";
import { focusRing } from "@/components/ui/button-styles";

export function MobileNav() {
  const pathname = usePathname();
  return <MobileNavContent key={pathname} pathname={pathname} />;
}

function MobileNavContent({ pathname }: { pathname: string }) {
  const [open, setOpen] = useState(false);
  useEffect(() => { if (!open) return; const closeOnEscape = (event: KeyboardEvent) => { if (event.key === "Escape") setOpen(false); }; document.addEventListener("keydown", closeOnEscape); document.body.style.overflow = "hidden"; return () => { document.removeEventListener("keydown", closeOnEscape); document.body.style.overflow = ""; }; }, [open]);
  return <><button type="button" aria-label="Open navigation" onClick={() => setOpen(true)} className={`lg:hidden ${focusRing}`}><Menu size={21} /></button>{open && <div className="fixed inset-0 z-50 bg-text/40" onClick={() => setOpen(false)}><aside className="sidebar-shell h-full w-72 bg-sidebar shadow-[0_8px_30px_rgba(28,23,52,0.18)]" onClick={(event) => event.stopPropagation()}><div className="flex items-center justify-between border-b border-sidebar-border px-5 py-5"><div><p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white">NOVA COPS</p><h2 className="mt-1.5 text-[17px] font-semibold text-white">Media Intelligence</h2></div><button type="button" aria-label="Close navigation" onClick={() => setOpen(false)} className={`text-white hover:text-white ${focusRing}`}><X size={20} /></button></div><nav className="space-y-1 overflow-y-auto px-3 py-4" aria-label="Mobile navigation">{navigation.map((item) => { const isActive = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href); const Icon = item.icon; return <Link key={item.href} href={item.href} aria-current={isActive ? "page" : undefined} className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium ${isActive ? "bg-sidebar-active font-semibold text-white" : "text-white hover:bg-white/[0.06]"}`}><Icon size={16} strokeWidth={1.75} aria-hidden="true" />{item.label}</Link>; })}</nav></aside></div>}</>;
}
