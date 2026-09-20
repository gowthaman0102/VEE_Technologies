import type { Metadata } from "next";
import { Nunito_Sans } from "next/font/google";

import {
  DashboardHeader,
} from "@/components/dashboard-header";
import {
  Sidebar,
} from "@/components/sidebar";
import { AppToaster } from "@/components/ui/toast";

import "./globals.css";


const nunitoSans = Nunito_Sans({
  variable: "--font-nunito-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: "Nova Cops · Media Intelligence",
  description:
    "Real-time AI-powered media monitoring and crisis intelligence dashboard.",
};


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={nunitoSans.variable}
    >
      <body className="min-h-screen bg-canvas font-sans text-body antialiased">
          <div className="flex min-h-screen">
            <Sidebar />

            <div className="flex min-w-0 flex-1 flex-col">
              <DashboardHeader />
              <main className="flex-1">
                {children}
              </main>
            </div>
          </div>
          <AppToaster />
      </body>
    </html>
  );
}
