import { useState } from "react";
import axios from "axios";
import dynamic from "next/dynamic";
const ReactCompareImage = dynamic(() => import("react-compare-image"), { ssr: false });

export default function Home() {
  const [file, setFile] = useState(null);
  const [modernPreview, setModernPreview] = useState(null);
  const [historicalUrl, setHistoricalUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const backendOrigin = process.env.NEXT_PUBLIC_BACKEND_ORIGIN || "http://localhost:8000";

  function onFileChange(e) {
    const f = e.target.files[0];
    setFile(f);
    setModernPreview(URL.createObjectURL(f));
  }

  async function onSubmit(e) {
    e.preventDefault();
    if (!file) return alert("Choose an image first.");
    setLoading(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await axios.post(`${backendOrigin}/process-photo`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      // historical_url is something like /historical/.. served by backend
      // Make absolute:
      const url = `${backendOrigin}${res.data.historical_url}`;
      setHistoricalUrl(url);
    } catch (err) {
      console.error(err);
      setError(err?.response?.data?.error || err.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 960, margin: "40px auto", padding: 16 }}>
      <h1>Street Time Machine — Chicago MVP</h1>
      <form onSubmit={onSubmit} style={{ marginBottom: 20 }}>
        <input type="file" accept="image/*" onChange={onFileChange} />
        <div style={{ marginTop: 12 }}>
          <button type="submit" disabled={loading}>See the Past</button>
        </div>
      </form>

      {loading && <p>Processing image…</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

      {modernPreview && historicalUrl && (
        <div>
          <h3>Modern (left) — Historical (right)</h3>
          <div style={{ width: "100%", maxWidth: 900 }}>
            <ReactCompareImage
              leftImage={modernPreview}
              rightImage={historicalUrl}
              leftImageLabel="Now"
              rightImageLabel="1950"
            />
          </div>
        </div>
      )}

      {!modernPreview && <p>Upload a photo of a Chicago street to try it.</p>}

      <hr style={{ margin: "40px 0" }} />

      <p>
        Want unlimited lookups? <a href="/pricing">Subscribe</a> (Demo Stripe flow).
      </p>
    </div>
  );
}
