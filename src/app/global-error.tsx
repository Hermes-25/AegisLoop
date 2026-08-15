"use client";

export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <html lang="en"><body style={{ margin: 0, background: "#081321", color: "#f4f8fc", fontFamily: "system-ui, sans-serif" }}><main style={{ maxWidth: 680, margin: "12vh auto", padding: 32, border: "1px solid #ff6b6b", borderRadius: 10, background: "#12243a" }}><p style={{ color: "#ff6b6b", fontWeight: 700 }}>AEGISLOOP · SAFE FAILURE</p><h1>The command center could not start.</h1><p style={{ color: "#b7c6d8", lineHeight: 1.6 }}>No evidence has been rendered. Retry the application; if the problem persists, inspect the health endpoint and artifact bundle.</p><button onClick={reset} style={{ marginTop: 20, padding: "10px 16px", border: 0, borderRadius: 6, background: "#e45a21", color: "#0a1b30", fontWeight: 700 }}>Retry</button></main></body></html>;
}
