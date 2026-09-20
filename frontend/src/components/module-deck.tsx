"use client";

import Link from "next/link";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import { navigation } from "@/lib/navigation";

function isActiveRoute(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
}

export function ModuleDeck() {
  const pathname = usePathname();
  const trackRef = useRef<HTMLDivElement>(null);
  const activeRef = useRef<HTMLAnchorElement>(null);

  useEffect(() => {
    activeRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
  }, [pathname]);

  const scroll = (direction: number) => {
    trackRef.current?.scrollBy({ left: direction * 280, behavior: "smooth" });
  };

  return (
    <nav aria-label="Application modules" className="module-deck-shell">
      <button type="button" className="module-deck-arrow left-2" aria-label="Previous modules" onClick={() => scroll(-1)}>
        <ChevronLeft size={17} aria-hidden="true" />
      </button>
      <div ref={trackRef} className="module-deck-track">
        {navigation.map((item, index) => {
          const active = isActiveRoute(pathname, item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              ref={active ? activeRef : undefined}
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={`module-card module-card-${item.visual}${active ? " module-card-active" : ""}`}
            >
              <span className="module-card-number">{String(index + 1).padStart(2, "0")}</span>
              <Icon className="module-card-icon" size={19} strokeWidth={1.7} aria-hidden="true" />
              <span className="module-card-title">{item.label}</span>
              <span className="module-card-subtitle">{item.subtitle}</span>
              <span className="module-card-signal" aria-hidden="true" />
            </Link>
          );
        })}
      </div>
      <button type="button" className="module-deck-arrow right-2" aria-label="Next modules" onClick={() => scroll(1)}>
        <ChevronRight size={17} aria-hidden="true" />
      </button>
    </nav>
  );
}