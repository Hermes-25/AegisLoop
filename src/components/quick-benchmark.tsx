"use client";

import { useEffect, useRef, useState } from "react";
import { CheckCircle2, Download, LoaderCircle, Play, ShieldAlert, TimerOff } from "lucide-react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

type RunState = "idle" | "running" | "complete" | "timed_out" | "failed";

export function QuickBenchmark() {
  const [state, setState] = useState<RunState>("idle");
  const [message, setMessage] = useState("");
  const resultRef = useRef<unknown>(null);
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => () => controllerRef.current?.abort(), []);

  async function run() {
    setState("running");
    setMessage("Simulator → red team → hardening → held-out evaluation");
    resultRef.current = null;
    const controller = new AbortController();
    controllerRef.current = controller;
    const timer = window.setTimeout(() => controller.abort("client_timeout"), 225_000);
    try {
      const response = await fetch("/api/benchmark", { method: "POST", signal: controller.signal, cache: "no-store" });
      const payload = await response.json().catch(() => ({ status: "failed", message: "The benchmark returned an unreadable response." }));
      if (!response.ok) {
        const timedOut = response.status === 504 || payload.status === "timed_out";
        setState(timedOut ? "timed_out" : "failed");
        setMessage(payload.message ?? "The benchmark did not complete.");
        return;
      }
      resultRef.current = payload;
      setState("complete");
      setMessage("A fresh quick-run artifact was generated successfully. Its values remain separate from full evidence.");
    } catch (error) {
      const aborted = error instanceof DOMException && error.name === "AbortError";
      setState(aborted ? "timed_out" : "failed");
      setMessage(aborted ? "The browser stopped waiting at the safe client limit; the rest of the command center remains available." : "The benchmark service is unavailable. The archived evidence remains available.");
    } finally {
      window.clearTimeout(timer);
      controllerRef.current = null;
    }
  }

  function download() {
    if (!resultRef.current) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(resultRef.current, null, 2)], { type: "application/json" }));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "aegisloop-illustrative-quick-run.json";
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return <div className="rounded-md border border-[var(--border)] bg-[var(--chrome)] p-6"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="eyebrow !text-[var(--signal-orange)]">Illustrative quick run</p><h2 className="mt-2 text-xl font-semibold">Execute the smaller demonstration protocol</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--text-secondary)]">This uses the real simulator and learning loop, but its output is never substituted for the archived full five-seed evidence.</p></div><Button onClick={run} disabled={state === "running"}>{state === "running" ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}{state === "running" ? "Running" : "Run quick benchmark"}</Button></div>{state !== "idle" && <div className="mt-6" aria-live="polite">{state === "running" && <div className="rounded-md border border-[var(--accent-blue)] bg-[rgb(76_155_232_/_0.08)] p-4"><p className="flex items-center gap-2 font-medium text-[var(--accent-blue)]"><LoaderCircle className="h-4 w-4 animate-spin" />Benchmark in progress</p><p className="mt-2 text-sm text-[var(--text-secondary)]">{message}</p><div className="mt-4 h-1 overflow-hidden rounded-full bg-[var(--surface)]"><div className="h-full w-1/2 animate-pulse rounded-full bg-[var(--accent-blue)]" /></div></div>}{state === "complete" && <Alert title="Quick run complete" tone="success"><p>{message}</p><Button variant="secondary" size="sm" className="mt-3" onClick={download}><Download className="h-4 w-4" />Download runtime artifact</Button></Alert>}{state === "timed_out" && <div className="flex gap-3 rounded-md border-l-4 border-[var(--warning)] bg-[var(--surface-raised)] p-4"><TimerOff className="h-5 w-5 shrink-0 text-[var(--warning)]" /><div><p className="font-semibold">Benchmark timed out safely</p><p className="mt-1 text-sm text-[var(--text-secondary)]">{message}</p></div></div>}{state === "failed" && <div className="flex gap-3 rounded-md border-l-4 border-[var(--critical)] bg-[var(--surface-raised)] p-4"><ShieldAlert className="h-5 w-5 shrink-0 text-[var(--critical)]" /><div><p className="font-semibold">Benchmark could not complete</p><p className="mt-1 text-sm text-[var(--text-secondary)]">{message}</p></div></div>}</div>}<div className="mt-6 grid gap-3 text-xs text-[var(--text-muted)] sm:grid-cols-3"><span className="flex items-center gap-2"><CheckCircle2 className="h-3.5 w-3.5 text-[var(--defender)]" />Real Python pipeline</span><span className="flex items-center gap-2"><CheckCircle2 className="h-3.5 w-3.5 text-[var(--defender)]" />Bounded timeout</span><span className="flex items-center gap-2"><CheckCircle2 className="h-3.5 w-3.5 text-[var(--defender)]" />Isolated from headline claims</span></div></div>;
}
