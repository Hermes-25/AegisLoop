import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  poweredByHeader: false,
  reactStrictMode: true,
  serverExternalPackages: ["csv-parse"],
  experimental: {
    optimizePackageImports: ["lucide-react", "recharts"],
  },
  outputFileTracingIncludes: {
    "/*": [
      "./artifacts/full_multiseed/aggregate.json",
      "./artifacts/full_multiseed/seed_results.csv",
      "./artifacts/precomputed/calibration_audit.json",
      "./artifacts/precomputed/prevalence_metrics.csv",
      "./artifacts/precomputed/v2_campaign_diagnostics.csv",
      "./artifacts/precomputed/attack_atlas.json",
      "./artifacts/precomputed/representative_campaign.json",
      "./AegisLoop_Solution_Walkthrough.pdf"
    ],
  },
};

export default nextConfig;
