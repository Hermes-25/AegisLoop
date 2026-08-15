export const evidenceManifest = {
  aggregate: {
    label: "Full five-seed aggregate",
    path: "artifacts/full_multiseed/aggregate.json",
    format: "json",
  },
  seedResults: {
    label: "Full five-seed results",
    path: "artifacts/full_multiseed/seed_results.csv",
    format: "csv",
  },
  calibrationAudit: {
    label: "Leakage-free calibration audit",
    path: "artifacts/precomputed/calibration_audit.json",
    format: "json",
  },
  prevalenceMetrics: {
    label: "Seed-specific prevalence stress test",
    path: "artifacts/precomputed/prevalence_metrics.csv",
    format: "csv",
  },
  v2Diagnostics: {
    label: "V2 matched-pool campaign diagnostics",
    path: "artifacts/precomputed/v2_campaign_diagnostics.csv",
    format: "csv",
  },
  attackAtlas: {
    label: "Attack atlas",
    path: "artifacts/precomputed/attack_atlas.json",
    format: "json",
  },
  representativeCampaign: {
    label: "Versioned representative campaign rollout",
    path: "artifacts/precomputed/representative_campaign.json",
    format: "json",
  },
} as const;

export type EvidenceKey = keyof typeof evidenceManifest;

export const evidenceKeys = Object.keys(evidenceManifest) as EvidenceKey[];
