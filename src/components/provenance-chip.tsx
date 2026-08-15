"use client";

import * as Dialog from "@radix-ui/react-dialog";
import Link from "next/link";
import { Database, ExternalLink, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { evidenceManifest, type EvidenceKey } from "@/lib/evidence/manifest";

export function ProvenanceChip({ source, field, note }: { source: string; field: string; note?: string }) {
  const artifactKey = (Object.entries(evidenceManifest) as [EvidenceKey, (typeof evidenceManifest)[EvidenceKey]][])
    .find(([, entry]) => entry.path === source)?.[0];

  return (
    <Dialog.Root>
      <Dialog.Trigger asChild><button className="mono inline-flex items-center gap-1.5 rounded-full border border-[var(--border)] bg-[var(--surface-raised)] px-2.5 py-1 text-[0.65rem] text-[var(--text-muted)] transition-colors hover:border-[var(--accent-blue)] hover:text-[var(--text)]"><Database className="h-3 w-3" aria-hidden="true" />View source</button></Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/70" />
        <Dialog.Content className="fixed right-0 top-0 z-50 h-full w-full max-w-md border-l border-[var(--border)] bg-[var(--chrome)] p-6 shadow-2xl focus:outline-none">
          <div className="flex items-start justify-between gap-4"><div><Dialog.Title className="text-lg font-semibold">Evidence provenance</Dialog.Title><Dialog.Description className="mt-2 text-sm leading-6 text-[var(--text-secondary)]">The displayed value is loaded and validated from this versioned artifact at runtime.</Dialog.Description></div><Dialog.Close asChild><Button variant="ghost" size="icon" aria-label="Close provenance"><X className="h-5 w-5" /></Button></Dialog.Close></div>
          <dl className="mt-8 space-y-6"><div><dt className="eyebrow">Artifact</dt><dd className="mono mt-2 break-all text-sm text-[var(--text)]">{source}</dd></div><div><dt className="eyebrow">Field or derivation</dt><dd className="mono mt-2 break-words text-sm text-[var(--text)]">{field}</dd></div>{note && <div><dt className="eyebrow">Interpretation boundary</dt><dd className="mt-2 text-sm leading-6 text-[var(--text-secondary)]">{note}</dd></div>}</dl>
          {artifactKey ? <Button asChild variant="secondary" className="mt-8 w-full justify-between"><Link href={`/api/evidence/${artifactKey}`} target="_blank" rel="noreferrer">Open verified payload <ExternalLink className="h-4 w-4" aria-hidden="true" /></Link></Button> : null}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
