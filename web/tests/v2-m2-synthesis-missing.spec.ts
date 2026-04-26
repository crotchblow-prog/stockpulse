import { test, expect } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

/**
 * Graceful degrade test: the JSON sidecar's `synthesis` field can be absent
 * (Phase 2 Commit 7 normalization). The hero must render without crashing
 * and just omit the today's-read sentence — no error boundary, no blank
 * page, no exception in the console.
 *
 * Strategy: mock the JSON file by writing a temp `latest.json` without
 * synthesis, navigate, assert hero structure renders and console is clean.
 * Restores the original file in teardown.
 */
test("synthesis-missing case renders without crashing", async ({ page }) => {
  const reportsDir = path.resolve("public/reports/en");
  const latest = path.join(reportsDir, "latest.json");
  const backup = path.join(reportsDir, "latest.json.test-backup");

  const original = await fs.readFile(latest, "utf8");
  await fs.writeFile(backup, original);

  try {
    const parsed = JSON.parse(original);
    delete parsed.synthesis;
    await fs.writeFile(latest, JSON.stringify(parsed, null, 2));

    const consoleErrors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") consoleErrors.push(msg.text());
    });

    await page.goto("/v2/en", { waitUntil: "networkidle" });

    // Hero present (data-tier set), no exceptions in console.
    await expect(page.locator("[data-tier]").first()).toBeVisible();
    expect(consoleErrors, `errors: ${consoleErrors.join("; ")}`).toEqual([]);

    // The "today's read" paragraph specifically should NOT be in the hero.
    // We assert by checking that the hero doesn't contain a long-form
    // sentence with "VIX at" — the synthesis prose marker.
    const heroText = await page.locator("[data-tier]").first().innerText();
    expect(heroText).not.toMatch(/VIX at \d/);
  } finally {
    await fs.copyFile(backup, latest);
    await fs.unlink(backup);
  }
});
