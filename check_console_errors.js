const playwright = require('playwright');

(async () => {
  const browser = await playwright.chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  // Capture console messages
  const consoleMessages = [];
  page.on('console', msg => {
    consoleMessages.push(`[${msg.type().toUpperCase()}] ${msg.text()}`);
  });
  
  // Capture page errors
  page.on('pageerror', error => {
    consoleMessages.push(`[PAGE ERROR] ${error.message}`);
  });
  
  console.log('Loading property page for parcel: 064210010010');
  
  await page.goto('http://localhost:5174/property/064210010010');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);
  
  if (consoleMessages.length > 0) {
    console.log('\n=== Console Messages ===');
    consoleMessages.forEach(msg => console.log(msg));
  } else {
    console.log('\nNo console messages');
  }
  
  await browser.close();
})();