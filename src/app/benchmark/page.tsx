import Link from "next/link";
import { ExternalLink } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { QuickBenchmark } from "@/components/quick-benchmark";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export const metadata = { title: "Live Benchmark" };

export default function BenchmarkPage() {
  return <div><PageHeader eyebrow="Live benchmark" title="Run the loop without confusing a demo with the evidence." conclusion="The live control executes a smaller illustrative protocol. Submission-grade conclusions remain anchored to the archived full five-seed campaign." /><div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]"><QuickBenchmark /><Card><CardHeader><div><CardTitle>Full archived evidence</CardTitle><CardDescription>Use these immutable records for every comparison in the command center.</CardDescription></div></CardHeader><CardContent className="space-y-3"><Button asChild variant="secondary" className="w-full justify-between"><Link href="/api/evidence/aggregate" target="_blank">Five-seed aggregate <ExternalLink className="h-4 w-4" /></Link></Button><Button asChild variant="secondary" className="w-full justify-between"><Link href="/api/evidence/seedResults" target="_blank">Seed-level results <ExternalLink className="h-4 w-4" /></Link></Button><Button asChild variant="secondary" className="w-full justify-between"><Link href="/evidence">Claim ledger <ExternalLink className="h-4 w-4" /></Link></Button><Alert title="Protocol boundary" tone="warning" className="mt-5">Quick-run output is intentionally not rendered as a competing fourth set of headline metrics. Download it for inspection; use the full archive for claims.</Alert></CardContent></Card></div></div>;
}
