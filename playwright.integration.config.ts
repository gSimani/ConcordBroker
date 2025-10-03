import { defineConfig, devices } from '@playwright/test';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config({ path: 'apps/web/.env.local' });

/**
 * Integration Testing Configuration
 * Tests all data flow and endpoint integrations
 */
export default defineConfig({
  testDir: './tests/e2e',
  testMatch: '**/*.spec.ts',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  workers: process.env.CI ? 1 : 4,
  reporter: [
    ['html', { outputFolder: 'test-results/integration-report' }],
    ['json', { outputFile: 'test-results/integration-results.json' }],
    ['list'],
  ],
  use: {
    baseURL: process.env.FRONTEND_URL || 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],

  /* Run dev server before tests if not already running */
  webServer: process.env.CI
    ? undefined
    : {
        command: 'cd apps/web && npm run dev',
        url: 'http://localhost:5173',
        reuseExistingServer: true,
        timeout: 120 * 1000,
      },
});
