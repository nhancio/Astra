import type { Metadata } from "next";
import AdminPortal from "./portal";

export const metadata: Metadata = {
  title: "Astra Admin · Mission control",
  description: "Private operations console for Astra AI",
  robots: { index: false, follow: false },
};

export default function AdminPage() { return <AdminPortal />; }
