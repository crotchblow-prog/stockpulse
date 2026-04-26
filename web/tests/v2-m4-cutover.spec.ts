import { test, expect } from "@playwright/test";

/**
 * M4 cutover smoke. /v2/* is gone, / is the new design, /legacy/* is
 * the Phase 1 escape hatch.
 */

test("/v2/en is gone (404 or redirect to /en)", async ({ page, request }) => {
  const res = await request.get("/v2/en", { maxRedirects: 0 });
  expect([404, 301, 302, 308].includes(res.status())).toBeTruthy();
});

test("/legacy/ renders Phase 1 markdown view", async ({ page }) => {
  await page.goto("/legacy");
  // Legacy chrome marker
  await expect(page.locator("[data-legacy-root]")).toBeVisible();
  // The Phase 1 chrome contains the SiteNav link to /zh
  const text = await page.locator("body").innerText();
  expect(text).toContain("VIX Pulse");
});

test("/legacy/zh renders Phase 1 zh markdown view", async ({ page }) => {
  await page.goto("/legacy/zh");
  await expect(page.locator("[data-legacy-root]")).toBeVisible();
});

test("/learn still serves the explainer", async ({ page }) => {
  await page.goto("/learn");
  // (learn) route group chrome — Phase 3.1 picks up v2 design tokens.
  await expect(page.locator("[data-v2-root][data-area='learn']")).toBeVisible();
  // Some content from the proofread:
  const text = await page.locator("body").innerText();
  expect(text).toMatch(/VIX Pulse|Wall Street/);
});

test("/zh/learn still serves the Chinese explainer", async ({ page }) => {
  await page.goto("/zh/learn");
  await expect(page.locator("[data-v2-root][data-area='learn']")).toBeVisible();
  const text = await page.locator("body").innerText();
  expect(text).toMatch(/(華爾街|VIX Pulse)/);
});

test("/archive permanent-redirects to /legacy/archive", async ({ page }) => {
  await page.goto("/archive");
  await expect(page).toHaveURL(/\/legacy\/archive\/?$/);
});

test("/zh/archive permanent-redirects to /legacy/zh/archive", async ({ page }) => {
  await page.goto("/zh/archive");
  await expect(page).toHaveURL(/\/legacy\/zh\/archive\/?$/);
});
