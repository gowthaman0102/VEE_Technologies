"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { navigation } from "@/lib/navigation";

export function Sidebar() {
  const pathname = usePathname();
  return <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-sidebar-border bg-sidebar lg:flex">
    <div className="border-b border-sidebar-border px-5 py-5"><p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white">NOVA COPS</p><h2 className="mt-1.5 text-[17px] font-semibold text-white">Media Intelligence</h2></div>
    <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4" aria-label="Primary navigation">{navigation.map((item) => { const isActive = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href); const Icon = item.icon; return <Link key={item.href} href={item.href} aria-current={isActive ? "page" : undefined} className={`relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors duration-150 ${isActive ? "before:absolute before:left-0 before:h-5 before:w-[3px] before:rounded-r-full before:bg-white bg-sidebar-active font-semibold text-white" : "text-white hover:bg-white/[0.06]"}`}><Icon size={16} strokeWidth={1.75} aria-hidden="true" />{item.label}</Link>; })}</nav>
    <div className="border-t border-sidebar-border px-5 py-4"><p className="break-words text-[11px] leading-5 text-white">Nova Cops Media Intelligence</p></div>
  </aside>;
}
