import { evidenceManifest, type EvidenceKey } from "@/lib/evidence/manifest";
import {
  loadAggregate,
  loadAttackAtlas,
  loadCalibrationAudit,
  loadPrevalenceMetrics,
  loadRepresentativeCampaign,
  loadSeedResults,
  loadV2Diagnostics,
} from "@/lib/evidence/loader";

export const runtime = "nodejs";

const loaders: Record<EvidenceKey, () => Promise<unknown>> = {
  aggregate: loadAggregate,
  seedResults: loadSeedResults,
  calibrationAudit: loadCalibrationAudit,
  prevalenceMetrics: loadPrevalenceMetrics,
  v2Diagnostics: loadV2Diagnostics,
  attackAtlas: loadAttackAtlas,
  representativeCampaign: loadRepresentativeCampaign,
};

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ artifact: string }> },
) {
  const { artifact } = await params;
  if (!(artifact in evidenceManifest)) {
    return Response.json({ error: "Unknown evidence artifact." }, { status: 404 });
  }
  const key = artifact as EvidenceKey;
  try {
    const data = await loaders[key]();
    return Response.json(
      { source: evidenceManifest[key], data },
      { headers: { "Cache-Control": "public, max-age=0, s-maxage=3600" } },
    );
  } catch (error) {
    return Response.json(
      { error: error instanceof Error ? error.message : "Evidence load failed." },
      { status: 503 },
    );
  }
}
