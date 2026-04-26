import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  // Workers: 1 even locally — two synthesis-missing tests mutate
  // web/public/reports/en/latest.json and race with parallel tests on /en
  // that read it. Easier to serialize than to refactor tests to use
  // page.route() interception of server-side fs.readFile calls.
  workers: 1,
  reporter: process.env.CI ? "list" : [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    env: {
      // Disable basic-auth for local Playwright runs — set via env so production
      // deploys still gate /v2/* behind credentials.
      BASIC_AUTH_USER: "",
      BASIC_AUTH_PASS: "",
    },
  },
});
