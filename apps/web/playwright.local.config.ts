import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/playwright',
  timeout: 30_000,
  retries: 0,
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:5173',
    viewport: { width: 1280, height: 720 },
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: {
    command: 'node ../../scripts/serve-dist.cjs',
    env: {
      DIST_DIR: process.env.DIST_DIR || 'apps/web/live-dist',
      API_PROXY: process.env.API_PROXY || 'https://api.concordbroker.com',
    },
    port: 5173,
    reuseExistingServer: true,
    timeout: 60_000,
  },
});

