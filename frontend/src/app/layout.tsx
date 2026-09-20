import type { Metadata } from "next";
import { Inter } from "next/font/google";

import { AppShell } from "@/components/app-shell";
import { AppToaster } from "@/components/ui/toast";
import { getActiveCompany } from "@/lib/api";

import "./globals.css";


const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Nova Cops · Media Intelligence",
  description:
    "Near real-time AI-powered media monitoring, risk intelligence, search, and executive reporting.",
};


export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const company = await getActiveCompany().catch(() => ({ name: "" }));

  return (
    <html
      lang="en"
      className={inter.variable}
    >
      <body className="min-h-screen bg-canvas font-sans text-body antialiased">
        <AppShell companyName={company.name}>{children}</AppShell>
        <AppToaster />
      </body>
    </html>
  );
}
