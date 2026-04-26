import { test, expect } from "@playwright/test";

/**
 * Phase 3.1 acceptance: TodaysTake / TierAction / UniverseScanner are now
 * rendered between Hero and WatchList on /[lang] and /[lang]/[date] routes.
 * /learn and /zh/learn pick up the v2 chrome via the (learn) route group.
 */

test("/en renders all 3 Phase 3.1 sections", async ({ page }) => {
  await page.goto("/en");
  await expect(page.locator("[data-component='todays-take']")).toBeVisible();
  await expect(page.locator("[data-component='tier-action']")).toBeVisible();
  await expect(page.locator("[data-component='universe-scanner']")).toBeVisible();
});

test("/zh renders all 3 Phase 3.1 sections with Chinese headings", async ({ page }) => {
  await page.goto("/zh");
  const todays = page.locator("[data-component='todays-take']");
  await expect(todays).toBeVisible();
  expect(await todays.innerText()).toContain("今日觀點");
  const tierAction = page.locator("[data-component='tier-action']");
  await expect(tierAction).toBeVisible();
  expect(await tierAction.innerText()).toContain("Tier 行動");
  const scanner = page.locator("[data-component='universe-scanner']");
  await expect(scanner).toBeVisible();
  expect(await scanner.innerText()).toContain("標的掃描");
});

test("TodaysTake shows market read + devil's advocate + position calls when populated", async ({ page }) => {
  await page.goto("/en");
  const tt = page.locator("[data-component='todays-take']");
  // Both subsections present:
  await expect(tt.locator("[data-subsection='devils-advocate']")).toBeVisible();
  await expect(tt.locator("[data-subsection='position-calls']")).toBeVisible();
  // At least one position card.
  const positions = tt.locator("[data-position]");
  expect(await positions.count()).toBeGreaterThan(0);
});

test("TodaysTake position cards expose action + confidence as data attrs", async ({ page }) => {
  await page.goto("/en");
  const cards = page.locator("[data-position]");
  const count = await cards.count();
  expect(count).toBeGreaterThan(0);
  for (let i = 0; i < count; i++) {
    const action = await cards.nth(i).getAttribute("data-action");
    const confidence = await cards.nth(i).getAttribute("data-confidence");
    expect(action).toMatch(/^(add|hold|trim|exit|watch)$/);
    expect(confidence).toMatch(/^(low|medium|high)$/);
  }
});

// Note: the synthesis-missing TodaysTake empty-state test mutates
// web/public/reports/en/latest.json — placed in v2-m2-synthesis-missing.spec.ts
// (its own spec file, runs serial) to avoid racing with parallel tests on
// /en that depend on synthesis being present (e.g. TierAction annotation).

test("TierAction buy_list annotates held tickers with action", async ({ page }) => {
  await page.goto("/en");
  const buyList = page.locator("[data-subsection='buy-list']");
  await expect(buyList).toBeVisible();
  // TSM is in the tier 2 buy list AND a current holding (today's snapshot).
  // It should show with `(action)` annotation.
  const tsm = buyList.locator("[data-ticker='TSM']");
  if (await tsm.count() > 0) {
    expect(await tsm.getAttribute("data-held")).toBe("true");
    expect(await tsm.innerText()).toMatch(/^TSM\s*\((add|hold|trim|exit|watch)\)/);
  }
  // GOOGL is on the buy list but NOT held (Carina exited it). Plain chip.
  const googl = buyList.locator("[data-ticker='GOOGL']");
  if (await googl.count() > 0) {
    expect(await googl.getAttribute("data-held")).toBe("false");
    expect((await googl.innerText()).trim()).toBe("GOOGL");
  }
});

test("UniverseScanner renders 3 sub-regions with rows", async ({ page }) => {
  await page.goto("/en");
  const scanner = page.locator("[data-component='universe-scanner']");
  await expect(scanner).toBeVisible();
  // Each region should have at least one row OR an empty placeholder italic.
  const addRows = scanner.locator("[data-region='add']");
  const watchRows = scanner.locator("[data-region='watch']");
  const avoidRows = scanner.locator("[data-region='avoid']");
  // Today: 5 high_normal tier-2 names → Add region populated.
  expect(await addRows.count()).toBeGreaterThan(0);
  // 9 mean_reverter names → Watch region populated.
  expect(await watchRows.count()).toBeGreaterThan(0);
  // 5 crisis_alpha names → Avoid region populated.
  expect(await avoidRows.count()).toBeGreaterThan(0);
});

test("UniverseScanner heading includes tier action in parens", async ({ page }) => {
  await page.goto("/en");
  const scanner = page.locator("[data-component='universe-scanner']");
  // Today's tier is 2 → action 觀察.
  expect(await scanner.locator("h2").innerText()).toContain("Tier 2");
  expect(await scanner.locator("h2").innerText()).toContain("觀察");
});

test("/learn renders under v2 chrome with [data-v2-root]", async ({ page }) => {
  await page.goto("/learn");
  const root = page.locator("[data-v2-root][data-area='learn']");
  await expect(root).toBeVisible();
  // VIXPulse brand link in the v2-style header.
  const brand = page.getByRole("link", { name: /VIXPulse/ });
  expect(await brand.count()).toBeGreaterThan(0);
});

test("/zh/learn renders under v2 chrome", async ({ page }) => {
  await page.goto("/zh/learn");
  const root = page.locator("[data-v2-root][data-area='learn']");
  await expect(root).toBeVisible();
});

test("/learn body uses Inter font family", async ({ page }) => {
  await page.goto("/learn");
  const body = page.locator("[data-area='learn']");
  const ff = await body.evaluate((el) => getComputedStyle(el).fontFamily);
  // next/font self-hosts Inter under hashed names; check for substring.
  expect(ff.toLowerCase()).toMatch(/inter/);
});
