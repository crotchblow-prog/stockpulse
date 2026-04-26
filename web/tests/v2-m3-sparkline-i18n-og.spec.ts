import { test, expect } from "@playwright/test";

/**
 * M3 acceptance suite: VIX sparkline + i18n toggle + dynamic OG card.
 */

test("sparkline component renders + has tier data attribute", async ({ page }) => {
  await page.goto("/v2/en");
  // Sparkline is lazy-loaded — wait for it to hydrate.
  const spark = page.locator("[data-component='vix-sparkline']");
  await expect(spark).toBeVisible({ timeout: 10_000 });
  // Tier attribute matches the report's tier (currently tier 2).
  const tier = await spark.getAttribute("data-tier");
  expect(tier).toMatch(/^[0-5]$/);
});

test("sparkline renders today's value in the legend", async ({ page }) => {
  await page.goto("/v2/en");
  const spark = page.locator("[data-component='vix-sparkline']");
  await expect(spark).toBeVisible({ timeout: 10_000 });
  // Legend "today" entry contains a numeric VIX (XX.XX or X.XX).
  const text = await spark.innerText();
  expect(text).toMatch(/today:?\s*\d+\.\d{2}/i);
});

test("language toggle is present and clicking 中 changes URL", async ({ page }) => {
  await page.goto("/v2/en");
  const toggle = page.locator("nav[aria-label='Language']");
  await expect(toggle).toBeVisible();
  // Scope the click to the v2 LangToggle (root layout's Phase 1 SiteNav also
  // contains a 中 link pointing at /zh, which would match a top-level locator).
  await toggle.getByRole("link", { name: "中" }).click();
  await expect(page).toHaveURL(/\/v2\/zh\/?$/);
});

test("EN active style differs from inactive", async ({ page }) => {
  await page.goto("/v2/en");
  const toggle = page.locator("nav[aria-label='Language']");
  const enLink = toggle.getByRole("link", { name: "EN", exact: true });
  // Active EN has aria-current="page".
  await expect(enLink).toHaveAttribute("aria-current", "page");
  const zhLink = toggle.getByRole("link", { name: "中" });
  await expect(zhLink).not.toHaveAttribute("aria-current", "page");
});

test("OG image route returns 200 + image content-type", async ({ request }) => {
  // Today's date for the dated route — also serves as the dated OG.
  const today = new Date().toISOString().slice(0, 10);
  const res = await request.get(`/v2/en/${today}/opengraph-image`);
  expect(res.status()).toBe(200);
  const ct = res.headers()["content-type"];
  expect(ct).toMatch(/^image\/(png|jpeg)/);
});
