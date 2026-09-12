import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Ameen — approval queue",
  description:
    "Invoices arrive in Slack and land here for approval, with the commitment they contradict quoted inline.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
