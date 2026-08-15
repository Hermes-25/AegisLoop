import { describe, expect, it } from "vitest";

function luminance(hex: string) {
  const channels = [1, 3, 5].map((index) => Number.parseInt(hex.slice(index, index + 2), 16) / 255).map((value) => value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4);
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}
function contrast(a: string, b: string) {
  const [lighter, darker] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (lighter + 0.05) / (darker + 0.05);
}

describe("visual tokens", () => {
  it("passes normal-text AA for ink on both AegisLoop orange tokens", () => {
    expect(contrast("#0A1B30", "#E45A21")).toBeGreaterThanOrEqual(4.5);
    expect(contrast("#0A1B30", "#FF7A3D")).toBeGreaterThanOrEqual(4.5);
  });
});
