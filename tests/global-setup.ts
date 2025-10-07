import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('🚀 Setting up Playwright tests...');

  // Launch browser and do any global setup
  const browser = await chromium.launch();
  const page = await browser.newPage();

  // Check if the application is running
  try {
    await page.goto('http://localhost:5174', { timeout: 30000 });
    console.log('✅ Application is running and accessible');
  } catch (error) {
    console.error('❌ Application is not accessible:', error);
    console.log('Make sure the web server is running on port 5174');
  }

  await browser.close();
  console.log('🏁 Global setup complete');
}

export default globalSetup;