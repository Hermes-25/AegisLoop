import { cn } from "@/lib/utils";

export function PageHeader({ eyebrow, title, conclusion, children, className }: { eyebrow: string; title: string; conclusion: string; children?: React.ReactNode; className?: string }) {
  return (
    <header className={cn("mb-8 grid gap-6 border-b border-[var(--border)] pb-7 xl:grid-cols-[minmax(0,1fr)_auto] xl:items-end", className)}>
      <div className="max-w-4xl"><p className="eyebrow">{eyebrow}</p><h1 className="mt-3 text-3xl font-semibold tracking-[-0.035em] sm:text-4xl">{title}</h1><p className="mt-4 max-w-3xl text-base leading-7 text-[var(--text-secondary)] sm:text-lg">{conclusion}</p></div>
      {children && <div className="flex flex-wrap gap-3">{children}</div>}
    </header>
  );
}
