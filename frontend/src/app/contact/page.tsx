import type { Metadata } from "next";

export const metadata: Metadata = { title: "Astra — Contact Us", alternates: { canonical: "/contact" } };

export default function ContactPage() {
  return (
    <main style={{ maxWidth: 760, margin: "60px auto", padding: "0 24px", lineHeight: 1.8 }}>
      <a href="/">← Astra</a>
      <h1 style={{ fontSize: 36, margin: "24px 0" }}>Contact Us</h1>
      <p>Astra is operated by <a href="https://nhancio.com" target="_blank" rel="noreferrer">Nhancio</a>.</p>
      <h2>Support, billing, and refunds</h2>
      <p>Email: <a href="mailto:nithindidigam@nhancio.com">nithindidigam@nhancio.com</a><br />
        WhatsApp: <a href="https://wa.me/918790968218">+91 87909 68218</a><br />
        We reply within 2 business days. Please include the phone number on your account.</p>
      <h2>Grievance Officer</h2>
      <p>Under the Information Technology Act, 2000, the rules made under it, and the Digital Personal Data Protection Act, 2023, you can raise complaints about the service or your personal data with our Grievance Officer:</p>
      <p>Didigam Nithin, Nhancio<br />
        Email: <a href="mailto:nithindidigam@nhancio.com">nithindidigam@nhancio.com</a></p>
      <p>We acknowledge complaints within 24 hours and aim to resolve them within 15 days.</p>
      <h2>Policies</h2>
      <p><a href="/terms">Terms of Service</a> · <a href="/privacy">Privacy Policy</a> · <a href="/refund">Refund and Cancellation Policy</a> · <a href="/data-deletion">Data deletion</a></p>
    </main>
  );
}
