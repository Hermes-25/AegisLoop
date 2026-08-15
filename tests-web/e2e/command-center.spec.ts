import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const routes = ["/", "/identify", "/generate", "/adapt", "/defend", "/reality-check", "/evidence", "/benchmark", "/methodology"];

for (const route of routes) {
  test(`${route} renders without WCAG A/AA violations`, async ({ page }) => {
    await page.goto(route);
    await expect(page.locator("main h1")).toBeVisible();
    const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
    expect(results.violations).toEqual([]);
  });
}

test("Generate explains behavioural and graph signals in plain English", async ({ page }) => {
  await page.goto("/generate");
  await expect(page.getByText("Payment attempts linked to this customer in the previous hour")).toBeVisible();
  await expect(page.getByText("The same attempt count in the tighter ten-minute window")).toBeVisible();
  await expect(page.getByText("Devices, merchants or beneficiaries this event shares with other campaign events")).toBeVisible();
  await expect(page.getByText("The number of direct entity connections around this event")).toBeVisible();
  await expect(page.getByText("Each value counts prior uses of that device or beneficiary")).toBeVisible();
});
