import { Skeleton } from "@/components/ui/skeleton";

export default function Loading() {
  return <div aria-label="Loading validated evidence" className="space-y-8"><div className="space-y-3 border-b border-[var(--border)] pb-7"><Skeleton className="h-3 w-40" /><Skeleton className="h-10 w-3/4" /><Skeleton className="h-5 w-2/3" /></div><div className="grid gap-4 md:grid-cols-3">{Array.from({ length: 3 }).map((_,index)=><Skeleton key={index} className="h-40" />)}</div><Skeleton className="h-[420px]" /><p className="text-sm text-[var(--text-muted)]">Validating artifact schemas and preparing the command center…</p></div>;
}
