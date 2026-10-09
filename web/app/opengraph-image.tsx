import { ImageResponse } from "next/og";

export const dynamic = "force-static";
export const alt = "Sentinel: Behavioral Fraud Detection";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "80px",
          background: "#0a0b0d",
          color: "#e9ebee",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 36 }}>
          <div
            style={{
              width: 34,
              height: 34,
              borderRadius: "50%",
              border: "4px solid #4ade80",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#4ade80" }} />
          </div>
          <div style={{ fontSize: 30, fontWeight: 600, letterSpacing: -0.5 }}>Sentinel</div>
        </div>
        <div style={{ fontSize: 52, fontWeight: 600, lineHeight: 1.15, maxWidth: 980 }}>
          Learn what&apos;s normal for this account. Flag what isn&apos;t.
        </div>
        <div style={{ fontSize: 24, color: "#9aa0ab", marginTop: 28, maxWidth: 920 }}>
          Behavioral fraud detection on 590K real transactions, measured against four required baselines,
          including the one that came back negative.
        </div>
      </div>
    ),
    { ...size }
  );
}
