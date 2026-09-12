import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Ameen — the finance agent that remembers what was promised",
  description:
    "Invoices arrive in Slack. What your team agreed in that channel arrives with them, cited and linked.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
