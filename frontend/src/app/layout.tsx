import type { Metadata } from "next";
import "./globals.css";
import { SITE_URL } from "@/lib/site";

const title = "Astra AI — India's Personal AI Assistant on WhatsApp";
const description =
  "Astra is a personal AI assistant you text on WhatsApp. Draft emails, plan your day and get answers in English, Hindi or Hinglish. Free to start.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title,
  description,
  keywords: [
    "AI assistant on WhatsApp",
    "WhatsApp AI assistant India",
    "AI chatbot on WhatsApp in Hindi",
    "Hinglish AI assistant",
    "personal AI assistant",
    "ChatGPT on WhatsApp alternative",
  ],
  // Pages that are indexed set their own canonical; this covers "/" (the home page is a client component).
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    siteName: "Astra AI",
    locale: "en_IN",
    title,
    description,
    images: [{ url: "/og.png", width: 1200, height: 630, alt: "Astra AI — your personal AI assistant on WhatsApp" }],
  },
  twitter: { card: "summary_large_image", title, description, images: ["/og.png"] },
  icons: { icon: "/brand/astra-meta-icon-transparent-1024.png", apple: "/brand/astra-meta-icon-1024.png" },
};

const org = { "@type": "Organization", "@id": "https://nhancio.com/#org", name: "Nhancio", url: "https://nhancio.com", email: "nithindidigam@nhancio.com" };

const siteSchema = {
  "@context": "https://schema.org",
  "@graph": [
    org,
    { "@type": "WebSite", "@id": `${SITE_URL}/#website`, name: "Astra AI", url: SITE_URL, inLanguage: "en-IN", publisher: { "@id": org["@id"] } },
    {
      "@type": "SoftwareApplication",
      "@id": `${SITE_URL}/#app`,
      name: "Astra AI",
      url: SITE_URL,
      applicationCategory: "LifestyleApplication",
      operatingSystem: "WhatsApp",
      description,
      inLanguage: ["en-IN", "hi-IN"],
      offers: [
        { "@type": "Offer", name: "Bharat Free", price: "0", priceCurrency: "INR" },
        { "@type": "Offer", name: "Astra Pro", price: "99", priceCurrency: "INR" },
        { "@type": "Offer", name: "Astra Business", price: "299", priceCurrency: "INR" },
      ],
      featureList: [
        "Draft emails and WhatsApp messages",
        "Plan your day",
        "Replies in English, Hindi, Hinglish, Telugu and Tamil",
        "Send Gmail, add Google Calendar events and Todoist or Google Tasks tasks after you confirm",
      ],
      publisher: { "@id": org["@id"] },
    },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en-IN">
      <body className="antialiased min-h-screen font-sans bg-[#070b14] text-slate-100">
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(siteSchema) }} />
        {children}
      </body>
    </html>
  );
}
