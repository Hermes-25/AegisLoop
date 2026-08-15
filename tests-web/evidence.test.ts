import { readFile } from "node:fs/promises";
import { parse } from "csv-parse/sync";
import { describe, expect, it } from "vitest";

import {
  aggregateSchema,
  attackCardSchema,
  calibrationSchema,
  diagnosticRowSchema,
  prevalenceRowSchema,
  representativeCampaignSchema,
  seedResultSchema,
} from "@/lib/evidence/schemas";
import { summarizeV2CampaignDiagnostics } from "@/lib/evidence/diagnostics";

async function json(path: string) {
  return JSON.parse(await readFile(path, "utf8"));
}
async function csv(path: string) {
  return parse(await readFile(path, "utf8"), { columns: true, skip_empty_lines: true, trim: true });
}

describe("approved evidence contract", () => {
  it("validates every manifest artifact", async () => {
    expect(aggregateSchema.parse(await json("artifacts/full_multiseed/aggregate.json")).n_seeds).toBe(5);
    expect(seedResultSchema.array().length(5).parse(await csv("artifacts/full_multiseed/seed_results.csv"))).toHaveLength(5);
    expect(calibrationSchema.parse(await json("artifacts/precomputed/calibration_audit.json")).test_rows_used_for_threshold_selection).toBe(false);
    expect(prevalenceRowSchema.array().parse(await csv("artifacts/precomputed/prevalence_metrics.csv"))).toHaveLength(9);
    expect(diagnosticRowSchema.array().parse(await csv("artifacts/precomputed/v2_campaign_diagnostics.csv"))).toHaveLength(360);
    expect(attackCardSchema.array().length(8).parse(await json("artifacts/precomputed/attack_atlas.json"))).toHaveLength(8);
    expect(representativeCampaignSchema.parse(await json("artifacts/precomputed/representative_campaign.json")).fidelity.valid).toBe(true);
  });

  it("reconciles every valid V2 reward from logged terms", async () => {
    const rows = diagnosticRowSchema.array().parse(await csv("artifacts/precomputed/v2_campaign_diagnostics.csv"));
    for (const row of rows) {
      const preFidelity = row.value_term + row.evasion_term + row.detection_cost_term + row.resource_cost_term + row.novelty_term;
      expect(Math.abs(preFidelity - row.pre_fidelity_reward)).toBeLessThan(1e-12);
      expect(Math.abs(preFidelity * row.fidelity - row.reward)).toBeLessThan(1e-12);
    }
  });

  it("derives the matched-pool card from validity and detection fields", async () => {
    const rows = diagnosticRowSchema.array().parse(await csv("artifacts/precomputed/v2_campaign_diagnostics.csv"));
    expect(summarizeV2CampaignDiagnostics(rows)).toMatchObject({
      totalCampaigns: 360,
      validCampaigns: 360,
      fullyDetectedCampaigns: 360,
      qualifyingCampaigns: 360,
      totalSeeds: 5,
      passingSeeds: 5,
    });

    const failedDetection = rows.map((row, index) => index === 0 ? { ...row, detection_rate: 0.5 } : row);
    expect(summarizeV2CampaignDiagnostics(failedDetection)).toMatchObject({
      totalCampaigns: 360,
      qualifyingCampaigns: 359,
      passingSeeds: 4,
    });
  });

  it("keeps the representative rollout chronological and stateful", async () => {
    const campaign = representativeCampaignSchema.parse(await json("artifacts/precomputed/representative_campaign.json"));
    const timestamps = campaign.events.map((event) => Date.parse(event.timestamp));
    expect([...timestamps].sort((a, b) => a - b)).toEqual(timestamps);
    expect(campaign.events).toHaveLength(9);
    expect(new Set(campaign.events.map((event) => event.customer_id)).size).toBe(campaign.summary.unique_customers);
    expect(new Set(campaign.events.map((event) => event.device_id)).size).toBe(campaign.summary.unique_devices);
    expect(new Set(campaign.events.map((event) => event.merchant_id)).size).toBe(campaign.summary.unique_merchants);
    expect(new Set(campaign.events.map((event) => event.beneficiary_id)).size).toBe(campaign.summary.unique_beneficiaries);
    expect(campaign.summary).toMatchObject({
      event_count: 9,
      unique_devices: 8,
      unique_merchants: 5,
      unique_beneficiaries: 7,
    });
    expect(new Set(campaign.events.map((event) => event.graph_shared_entities)).size).toBeGreaterThan(1);
  });
});
