import type { Metadata } from "next";
import {
  Geist,
  Geist_Mono,
} from "next/font/google";

import {
  DashboardHeader,
} from "@/components/dashboard-header";
import {
  Sidebar,
} from "@/components/sidebar";

import "./globals.css";


const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});


export const metadata: Metadata = {
  title: "AI Media Intelligence",
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
      className={`${geistSans.variable} ${geistMono.variable}`}
    >
      <body className="min-h-screen bg-slate-950 font-sans text-white antialiased">
        <div className="flex min-h-screen">
          <Sidebar />

          <div className="min-w-0 flex-1">
            <DashboardHeader />

            <div className="min-h-[calc(100vh-73px)]">
              {children}
            </div>
          </div>
        </div>
      </body>
    </html>
  );
}
