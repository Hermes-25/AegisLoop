import * as React from "react";
import { cn } from "@/lib/utils";

export function Card({ className, ...props }: React.ComponentProps<"section">) {
  return <section className={cn("rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-panel)]", className)} {...props} />;
}
export function CardHeader({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("flex items-start justify-between gap-4 border-b border-[var(--border)] p-5", className)} {...props} />;
}
export function CardTitle({ className, ...props }: React.ComponentProps<"h2">) {
  return <h2 className={cn("text-base font-semibold tracking-tight", className)} {...props} />;
}
export function CardDescription({ className, ...props }: React.ComponentProps<"p">) {
  return <p className={cn("mt-1 text-sm leading-6 text-[var(--text-secondary)]", className)} {...props} />;
}
export function CardContent({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("p-5", className)} {...props} />;
}
