import type { LucideIcon } from "lucide-react";
import { Building2, FileText, LayoutDashboard, Newspaper, Search, Settings2, ShieldAlert, TrendingUp } from "lucide-react";

export type NavigationItem = { label: string; href: string; icon: LucideIcon; subtitle: string; visual: string };

export const navigation: NavigationItem[] = [
  { label: "Overview", href: "/", icon: LayoutDashboard, subtitle: "The bigger picture", visual: "overview" },
  { label: "Intelligence", href: "/intelligence", icon: Newspaper, subtitle: "Near-real-time media signals", visual: "intelligence" },
  { label: "Risk Analytics", href: "/risk", icon: ShieldAlert, subtitle: "Assess emerging risk", visual: "risk" },
  { label: "Analytics", href: "/analytics", icon: TrendingUp, subtitle: "Turn data into insight", visual: "analytics" },
  { label: "Companies", href: "/companies", icon: Building2, subtitle: "Company monitoring", visual: "companies" },
  { label: "Search", href: "/search", icon: Search, subtitle: "Find intelligence faster", visual: "search" },
  { label: "Reports", href: "/reports", icon: FileText, subtitle: "Generate executive reports", visual: "reports" },
  { label: "Article Settings", href: "/watchlist", icon: Settings2, subtitle: "Manage monitoring categories", visual: "settings" },
];
