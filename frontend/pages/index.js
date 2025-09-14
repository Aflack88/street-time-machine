import { useState, useEffect } from "react";
import axios from "axios";
import dynamic from "next/dynamic";
const ReactCompareImage = dynamic(() => import("react-compare-image"), { ssr: false });

export default function Home() {
  const [file, setFile] = useState(null);
  const [modernPreview, setModernPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [locationData, setLocationData] = useState(null);
  const [heading, setHeading] = useState(null);

  const backendOrigin = process.env.NEXT_PUBLIC_BACKEND_ORIGIN || "http://localhost:8000";

  // Get user location and device orientation
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocationData({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy
          });
        },
        (error) => console.error("Location error:", error),
        { enableHighAccuracy: true, timeout: 10000 }
      );
    }

    // Device orientation for compass heading
    const handleOrientation = (event) => {
      if (event.alpha !== null) {
        // Convert to 0-360 degrees
        let compassHeading = event.alpha;
        if (event.webkitCompassHeading) {
          compassHeading = event.webkitCompassHeading; // iOS
        }
        setHeading(Math.round(compassHeading));
      }
    };

    if (window.DeviceOrientationEvent) {
      window.addEventListener('deviceorientationabsolute', handleOrientation);
      window.addEventListener('deviceorientation', handleOrientation);
    }

    return () => {
      window.removeEventListener('deviceorientationabsolute', handleOrientation);
      window.removeEventListener('deviceorientation', handleOrientation);
    };
  }, []);

  function onFileChange(e) {
    const f = e.target.files[0];
    if (f) {
      setFile(f);
      setModernPreview(URL.createObjectURL(f));
      setResult(null);
      setError(null);
    }
  }

  async function onSubmit(e) {
    e.preventDefault();
    if (!file) return alert("Choose an image first.");
    if (!locationData) return alert("Location access required. Please enable location services.");
    
    setLoading(true);
    setError(null);
    
    try {
      const form = new FormData();
      form.append("file", file);
      
      // Enhanced metadata
      const metadata = {
        gps: locationData,
        heading: heading,
        timestamp: new Date().toISOString(),
        user_agent: navigator.userAgent
      };
      form.append("metadata", JSON.stringify(metadata));

      const res = await axios.post(`${backendOrigin}/process-photo`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      
      setResult(res.data);
    } catch (err) {
      console.error(err);
      setError(err?.response?.data?.error || err.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  const getDirectionText = (heading) => {
    if (!heading) return "";
    const directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
    const index = Math.round(heading / 45) % 8;
    return directions[index];
  };

  return (
    <div style={{ maxWidth: 960, margin: "40px auto", padding: 16 }}>
      <h1>Street Time Machine — Chicago</h1>
      <p>Discover how your location looked throughout history</p>

      {/* Status indicators */}
      <div style={{ marginBottom: 20, padding: 12, background: "#f0f0f0", borderRadius: 6 }}>
        <div>📍 Location: {locationData ? "✅ Detected" : "❌ Required"}</div>
        <div>🧭 Direction: {heading ? `${heading}° (${getDirectionText(heading)})` : "Detecting..."}</div>
      </div>

      <form onSubmit={onSubmit} style={{ marginBottom: 20 }}>
        <div style={{ marginBottom: 12 }}>
          <input 
            type="file" 
            accept="image/*" 
            onChange={onFileChange}
            capture="environment" // Prefer rear camera on mobile
          />
        </div>
        <div>
          <button 
            type="submit" 
            disabled={loading || !locationData}
            style={{
              padding: "12px 24px",
              backgroundColor: loading || !locationData ? "#ccc" : "#007bff",
              color: "white",
              border: "none",
              borderRadius: 6,
              fontSize: 16,
              cursor: loading || !locationData ? "not-allowed" : "pointer"
            }}
          >
            {loading ? "Finding Historical Match..." : "Discover the Past"}
          </button>
        </div>
      </form>

      {loading && (
        <div style={{ textAlign: "center", margin: "20px 0" }}>
          <div style={{ fontSize: 18, marginBottom: 10 }}>🔍 Analyzing your photo...</div>
          <div style={{ fontSize: 14, color: "#666" }}>
            • Extracting visual landmarks<br/>
            • Searching historical archives<br/>
            • Finding the best match
          </div>
        </div>
      )}

      {error && (
        <div style={{ 
          color: "red", 
          padding: 12, 
          background: "#ffe6e6", 
          borderRadius: 6,
          marginBottom: 20 
        }}>
          {error}
        </div>
      )}

      {result && modernPreview && (
        <div>
          <div style={{ marginBottom: 20 }}>
            <h3>Then & Now</h3>
            <div style={{ 
              background: "#e8f4f8", 
              padding: 12, 
              borderRadius: 6, 
              marginBottom: 16,
              fontSize: 14
            }}>
              <strong>Match Confidence:</strong> {result.confidence}% | 
              <strong> Era:</strong> {result.year} | 
              <strong> Distance:</strong> ~{result.distance_meters}m
            </div>
          </div>
          
          <div style={{ width: "100%", maxWidth: 900, marginBottom: 20 }}>
            <ReactCompareImage
              leftImage={modernPreview}
              rightImage={`${backendOrigin}${result.historical_url}`}
              leftImageLabel="Today"
              rightImageLabel={result.year}
            />
          </div>

          {/* Historical context */}
          {result.story && (
            <div style={{ 
              background: "#f8f9fa", 
              padding: 20, 
              borderRadius: 8,
              marginBottom: 20 
            }}>
              <h4>📚 Historical Context</h4>
              <blockquote style={{ 
                fontStyle: "italic", 
                fontSize: 16, 
                lineHeight: 1.5,
                borderLeft: "4px solid #007bff",
                paddingLeft: 16,
                margin: "10px 0"
              }}>
                "{result.story.quote}"
              </blockquote>
              <p><strong>Fun Fact:</strong> {result.story.fact}</p>
              {result.story.source && (
                <p style={{ fontSize: 12, color: "#666" }}>
                  Source: {result.story.source}
                </p>
              )}
            </div>
          )}

          {/* Social sharing */}
          <div style={{ textAlign: "center", marginTop: 20 }}>
            <button
              onClick={() => {
                if (navigator.share) {
                  navigator.share({
                    title: `Street Time Machine - ${result.year}`,
                    text: result.story?.quote || "Check out how this street looked in the past!",
                    url: window.location.href
                  });
                } else {
                  navigator.clipboard.writeText(window.location.href);
                  alert("Link copied to clipboard!");
                }
              }}
              style={{
                padding: "10px 20px",
                backgroundColor: "#28a745",
                color: "white",
                border: "none",
                borderRadius: 6,
                cursor: "pointer"
              }}
            >
              📤 Share This Discovery
            </button>
          </div>
        </div>
      )}

      {!modernPreview && (
        <div style={{ 
          textAlign: "center", 
          padding: 40, 
          background: "#f8f9fa", 
          borderRadius: 8,
          color: "#666"
        }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>📷</div>
          <p>Take a photo of any Chicago street to see its history unfold</p>
          <p style={{ fontSize: 14 }}>Best results: clear street view, outdoor locations, recognizable landmarks</p>
        </div>
      )}

      <hr style={{ margin: "40px 0" }} />

      <div style={{ textAlign: "center" }}>
        <p>
          Love discovering history? <a href="/pricing" style={{ color: "#007bff" }}>
            Get unlimited lookups & HD downloads
          </a>
        </p>
      </div>
    </div>
  );
}
