import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright configuration for E2E tests.
 * 
 * These tests require both backend and frontend servers to be running.
 * Start them manually or use a test setup script.
 */
export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "html",
  use: {
    baseURL: "http://localhost:5173",
    trace: "on-first-retry",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  // Run your local dev server before starting the tests
  // webServer: [
  //   {
  //     command: "cd frontend && npm run dev",
  //     url: "http://localhost:5173",
  //     reuseExistingServer: !process.env.CI,
  //   },
  //   {
  //     command: "uvicorn app.main:app --reload",
  //     url: "http://localhost:8000",
  //     reuseExistingServer: !process.env.CI,
  //   },
  // ],
});

