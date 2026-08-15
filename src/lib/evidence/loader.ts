import "server-only";

import { readFile } from "node:fs/promises";
import path from "node:path";
import { cache } from "react";
import { parse } from "csv-parse/sync";
import { ZodError } from "zod";

import { evidenceKeys, evidenceManifest, type EvidenceKey } from "./manifest";
import {
  aggregateSchema,
  attackCardSchema,
  calibrationSchema,
  diagnosticRowSchema,
  prevalenceRowSchema,
  representativeCampaignSchema,
  seedResultSchema,
  type Aggregate,
  type AttackCard,
  type CalibrationAudit,
  type DiagnosticRow,
  type PrevalenceRow,
  type RepresentativeCampaign,
  type SeedResult,
} from "./schemas";

export class EvidenceLoadError extends Error {
  constructor(public readonly artifact: EvidenceKey, message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "EvidenceLoadError";
  }
}

// Keep server-side file tracing scoped to the versioned evidence directory. This
// also makes the path-containment check explicit instead of tracing the repo root.
const artifactsRoot = path.join(process.cwd(), "artifacts");

function resolveArtifact(key: EvidenceKey) {
  const relativePath = evidenceManifest[key].path.replace(/^artifacts[\\/]/, "");
  const resolved = path.resolve(artifactsRoot, relativePath);
  if (!resolved.startsWith(`${artifactsRoot}${path.sep}`)) {
    throw new EvidenceLoadError(key, "Evidence path escaped the artifact directory.");
  }
  return resolved;
}

async function readArtifact(key: EvidenceKey): Promise<unknown> {
  const entry = evidenceManifest[key];
  try {
    const raw = await readFile(resolveArtifact(key), "utf8");
    return entry.format === "json"
      ? JSON.parse(raw)
      : parse(raw, { columns: true, skip_empty_lines: true, trim: true });
  } catch (error) {
    throw new EvidenceLoadError(
      key,
      `Could not read ${entry.label} from ${entry.path}.`,
      { cause: error },
    );
  }
}

function validate<T>(key: EvidenceKey, parser: { parse: (value: unknown) => T }, value: unknown): T {
  try {
    return parser.parse(value);
  } catch (error) {
    const detail = error instanceof ZodError ? error.issues[0]?.message : "Unknown schema error";
    throw new EvidenceLoadError(key, `${evidenceManifest[key].label} failed validation: ${detail}`, {
      cause: error,
    });
  }
}

export const loadAggregate = cache(async (): Promise<Aggregate> =>
  validate("aggregate", aggregateSchema, await readArtifact("aggregate")),
);

export const loadSeedResults = cache(async (): Promise<SeedResult[]> =>
  validate("seedResults", seedResultSchema.array().length(5), await readArtifact("seedResults")),
);

export const loadCalibrationAudit = cache(async (): Promise<CalibrationAudit> =>
  validate("calibrationAudit", calibrationSchema, await readArtifact("calibrationAudit")),
);

export const loadPrevalenceMetrics = cache(async (): Promise<PrevalenceRow[]> =>
  validate("prevalenceMetrics", prevalenceRowSchema.array().min(1), await readArtifact("prevalenceMetrics")),
);

export const loadV2Diagnostics = cache(async (): Promise<DiagnosticRow[]> =>
  validate("v2Diagnostics", diagnosticRowSchema.array().min(1), await readArtifact("v2Diagnostics")),
);

export const loadAttackAtlas = cache(async (): Promise<AttackCard[]> =>
  validate("attackAtlas", attackCardSchema.array().length(8), await readArtifact("attackAtlas")),
);

export const loadRepresentativeCampaign = cache(async (): Promise<RepresentativeCampaign> =>
  validate(
    "representativeCampaign",
    representativeCampaignSchema,
    await readArtifact("representativeCampaign"),
  ),
);

export async function loadAllEvidence() {
  const [aggregate, seedResults, calibrationAudit, prevalenceMetrics, v2Diagnostics, attackAtlas, representativeCampaign] =
    await Promise.all([
      loadAggregate(),
      loadSeedResults(),
      loadCalibrationAudit(),
      loadPrevalenceMetrics(),
      loadV2Diagnostics(),
      loadAttackAtlas(),
      loadRepresentativeCampaign(),
    ]);
  return { aggregate, seedResults, calibrationAudit, prevalenceMetrics, v2Diagnostics, attackAtlas, representativeCampaign };
}

export async function evidenceHealth() {
  await loadAllEvidence();
  return evidenceKeys.map((key) => ({
    key,
    label: evidenceManifest[key].label,
    path: evidenceManifest[key].path,
    status: "ready" as const,
  }));
}
