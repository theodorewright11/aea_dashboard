import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Automation Exposure Dashboard",
  description:
    "Compare automation exposure across occupation groups using AEI, MCP, and Microsoft datasets.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 antialiased">{children}</body>
    </html>
  );
}
