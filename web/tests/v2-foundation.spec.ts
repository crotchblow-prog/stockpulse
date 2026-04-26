import { test, expect } from "@playwright/test";

/**
 * M1 foundation smoke test. Asserts:
 * 1. /en boots without console errors.
 * 2. The v2 root wrapper renders with --bg-base (rgb(10, 10, 11)).
 *
 * Note: ARIA's brief asked to assert `body` background, but the root
 * Next.js layout owns body and is shared with Phase 1 routes (which use a
 * different bg #0b0e14). To avoid breaking Phase 1's visual, the v2 layout
 * applies --bg-base to a `[data-v2-root]` wrapper inside body. Asserting
 * on that wrapper is the equivalent guarantee for v2 routes.
 */
test("/en boots clean with --bg-base on the v2 root wrapper", async ({ page }) => {
  const consoleErrors: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });

  await page.goto("/en");
  await page.waitForLoadState("networkidle");

  expect(consoleErrors, `console errors: ${consoleErrors.join("; ")}`).toEqual([]);

  const wrapper = page.locator("[data-v2-root]").first();
  await expect(wrapper).toBeVisible();
  const bg = await wrapper.evaluate((el) => getComputedStyle(el).backgroundColor);
  expect(bg).toBe("rgb(10, 10, 11)");
});

test("/ redirects to /en", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/en\/?$/);
});
