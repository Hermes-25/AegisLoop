import { evidenceHealth } from "@/lib/evidence/loader";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const artifacts = await evidenceHealth();
    return Response.json(
      { status: "ready", artifacts },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch (error) {
    return Response.json(
      {
        status: "degraded",
        message: error instanceof Error ? error.message : "Evidence validation failed.",
      },
      { status: 503, headers: { "Cache-Control": "no-store" } },
    );
  }
}
