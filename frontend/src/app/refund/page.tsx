import type { Metadata } from "next";

export const metadata: Metadata = { title: "Astra — Refund and Cancellation Policy", alternates: { canonical: "/refund" } };

export default function RefundPage() {
  return (
    <main style={{ maxWidth: 760, margin: "60px auto", padding: "0 24px", lineHeight: 1.8 }}>
      <a href="/">← Astra</a>
      <h1 style={{ fontSize: 36, margin: "24px 0" }}>Refund and Cancellation Policy</h1>
      <p>Last updated: 3 November 2026</p>
      <p>Astra is a digital service. Nothing is shipped; paid plans are activated on your WhatsApp number as soon as payment is confirmed.</p>
      <h2>Cancellation</h2>
      <p>Paid plans are monthly subscriptions. You can cancel at any time by emailing <a href="mailto:nithindidigam@nhancio.com">nithindidigam@nhancio.com</a> with the phone number on your account. After cancellation your plan stays active until the end of the period you have paid for, and you are not charged again.</p>
      <h2>Refunds</h2>
      <p>You are entitled to a full refund if:</p>
      <ul>
        <li>you were charged more than once for the same period;</li>
        <li>you were charged but your paid plan was not activated within 24 hours and we could not fix it; or</li>
        <li>you were charged for a renewal after you had cancelled.</li>
      </ul>
      <p>Other refund requests made within 7 days of a payment are reviewed case by case. Partial months are not otherwise refunded.</p>
      <h2>How to request a refund</h2>
      <p>Email <a href="mailto:nithindidigam@nhancio.com">nithindidigam@nhancio.com</a> with your phone number, the payment date, and the amount. We reply within 2 business days. Approved refunds go back to the original payment method, normally within 5–7 business days, depending on your bank or payment provider.</p>
      <h2>Contact</h2>
      <p>See our <a href="/contact">contact page</a> for other ways to reach us.</p>
    </main>
  );
}
