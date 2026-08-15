import type { DiagnosticRow } from "./schemas";

export function summarizeV2CampaignDiagnostics(rows: DiagnosticRow[]) {
  const perSeed = new Map<number, { total: number; qualifying: number }>();
  let validCampaigns = 0;
  let fullyDetectedCampaigns = 0;
  let qualifyingCampaigns = 0;

  for (const row of rows) {
    const isFullyDetected = row.detection_rate === 1;
    const qualifies = row.valid && isFullyDetected;
    validCampaigns += Number(row.valid);
    fullyDetectedCampaigns += Number(isFullyDetected);
    qualifyingCampaigns += Number(qualifies);

    const seed = perSeed.get(row.seed) ?? { total: 0, qualifying: 0 };
    seed.total += 1;
    seed.qualifying += Number(qualifies);
    perSeed.set(row.seed, seed);
  }

  const passingSeeds = [...perSeed.values()].filter((seed) => seed.total === seed.qualifying).length;
  return {
    totalCampaigns: rows.length,
    validCampaigns,
    fullyDetectedCampaigns,
    qualifyingCampaigns,
    totalSeeds: perSeed.size,
    passingSeeds,
  };
}
