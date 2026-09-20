import type { LucideIcon } from "lucide-react";
import { Building2, FileText, LayoutDashboard, Newspaper, Search, Settings2, ShieldAlert, TrendingUp } from "lucide-react";

export type NavigationItem = { label: string; href: string; icon: LucideIcon };

export const navigation: NavigationItem[] = [
  { label: "Overview", href: "/", icon: LayoutDashboard },
  { label: "Intelligence", href: "/intelligence", icon: Newspaper },
  { label: "Risk Analytics", href: "/risk", icon: ShieldAlert },
  { label: "Analytics", href: "/analytics", icon: TrendingUp },
  { label: "Companies", href: "/companies", icon: Building2 },
  { label: "Search", href: "/search", icon: Search },
  { label: "Reports", href: "/reports", icon: FileText },
  { label: "Article Settings", href: "/watchlist", icon: Settings2 },
];
