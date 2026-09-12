import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Ameen — approval queue",
};

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return children;
}
