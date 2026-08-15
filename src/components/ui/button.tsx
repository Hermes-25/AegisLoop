import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex min-h-10 items-center justify-center gap-2 rounded-md px-4 text-sm font-semibold transition-colors disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-[var(--signal-orange)] text-[var(--on-orange)] hover:bg-[#ff8b57]",
        secondary: "border border-[var(--border)] bg-[var(--surface-raised)] text-[var(--text)] hover:bg-[var(--surface-hover)]",
        ghost: "text-[var(--text-secondary)] hover:bg-[var(--surface-raised)] hover:text-[var(--text)]",
        danger: "bg-[var(--critical)] text-[var(--canvas)] hover:brightness-110",
      },
      size: {
        default: "h-10",
        sm: "h-8 min-h-8 px-3 text-xs",
        icon: "h-10 w-10 px-0",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  },
);

function Button({ className, variant, size, asChild = false, ...props }: React.ComponentProps<"button"> & VariantProps<typeof buttonVariants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot : "button";
  return <Comp className={cn(buttonVariants({ variant, size }), className)} {...props} />;
}

export { Button, buttonVariants };
