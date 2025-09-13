import { useState } from "react";
import axios from "axios";

export default function Pricing() {
  const backendOrigin = process.env.NEXT_PUBLIC_BACKEND_ORIGIN || "http://localhost:8000";
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);

  async function startCheckout(priceId) {
    if (!email) return alert("Enter your email to start checkout.");
    setLoading(true);
    try {
      const res = await axios.post(`${backendOrigin}/stripe/create-checkout-session`, {
        priceId,
        customer_email: email
      });
      window.location.href = res.data.checkout_url;
    } catch (err) {
      console.error(err);
      alert("Checkout failed: " + (err?.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  }

  // Replace with your Stripe price IDs
  const PRICE_ID_MONTHLY = process.env.NEXT_PUBLIC_STRIPE_PRICE_MONTHLY || "price_123_monthly";
  const PRICE_ID_YEARLY = process.env.NEXT_PUBLIC_STRIPE_PRICE_YEARLY || "price_123_yearly";

  return (
    <div style={{ maxWidth: 640, margin: "40px auto", padding: 16 }}>
      <h1>Pricing</h1>
      <p>Free tier: 5 lookups / month.</p>
      <p>Pro: unlimited lookups + hi-res downloads.</p>

      <div style={{ margin: "20px 0" }}>
        <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email for checkout" />
      </div>

      <div style={{ display: "flex", gap: 12 }}>
        <div style={{ border: "1px solid #ddd", padding: 12 }}>
          <h3>Monthly</h3>
          <p>$4.99 / month</p>
          <button onClick={() => startCheckout(PRICE_ID_MONTHLY)} disabled={loading}>Start monthly</button>
        </div>
        <div style={{ border: "1px solid #ddd", padding: 12 }}>
          <h3>Yearly</h3>
          <p>$39.99 / year</p>
          <button onClick={() => startCheckout(PRICE_ID_YEARLY)} disabled={loading}>Start yearly</button>
        </div>
      </div>
    </div>
  );
}
