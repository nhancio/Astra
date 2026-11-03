import type { Metadata } from "next";

// The brands page is a client component, so its metadata lives here.
export const metadata: Metadata = {
  title: "Astra for Brands — Sponsored Perks on WhatsApp in India",
  description:
    "Reach people in India inside their WhatsApp chats with Astra: one-line sponsored perks matched to what they asked for, shown only to free-plan users.",
  alternates: { canonical: "/brands" },
  openGraph: { url: "/brands", title: "Astra for Brands — Sponsored Perks on WhatsApp in India", images: ["/og.png"] },
};

export default function BrandsLayout({ children }: { children: React.ReactNode }) {
  return children;
}
