import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return <section className="mx-auto mt-16 max-w-xl text-center"><p className="eyebrow">Route not found</p><h1 className="mt-4 text-3xl font-semibold">This mission-control view does not exist.</h1><p className="mt-4 text-[var(--text-secondary)]">Return to the briefing and follow the validated loop.</p><Button asChild className="mt-6"><Link href="/"><ArrowLeft className="h-4 w-4" />Mission briefing</Link></Button></section>;
}
