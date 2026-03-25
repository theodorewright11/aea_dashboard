import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";
import { SimpleModeProvider } from "@/lib/SimpleModeContext";

const inter = Inter({ subsets: ["latin"], display: "swap" });

export const metadata: Metadata = {
  title: "Automation Exposure Dashboard",
  description:
    "Explore how AI automation affects occupations, tasks, and wages across the economy.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.className}>
      <body className="antialiased" style={{ backgroundColor: "var(--bg-base)", color: "var(--text-primary)" }}>
        <SimpleModeProvider>
          <Navigation />
          {/* Content sits below the fixed nav */}
          <div style={{ paddingTop: "var(--nav-height)", minHeight: "calc(100vh - 60px)" }}>
            {children}
          </div>
          <Footer />
        </SimpleModeProvider>
      </body>
    </html>
  );
}
