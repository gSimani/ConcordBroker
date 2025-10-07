const { chromium } = require("playwright");

async function debugPropertiesPage() {
  console.log("Starting properties page debug...");
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await context.newPage();

  try {
    console.log("1. Navigating to http://localhost:5173/properties...");
    await page.goto("http://localhost:5173/properties");
    await page.waitForLoadState("networkidle");

    await page.screenshot({ path: "debug-properties-initial.png", fullPage: true });
    console.log("   Initial screenshot saved");

    await page.waitForTimeout(5000);
    
    const title = await page.title();
    const url = page.url();
    console.log(`   Page title: ${title}`);
    console.log(`   Page URL: ${url}`);

    const pageText = await page.textContent("body");
    console.log("   Page text (first 500 chars):", pageText.substring(0, 500));

    const allDivs = await page.locator("div").all();
    console.log(`   Found ${allDivs.length} div elements`);

  } catch (error) {
    console.error("Error:", error.message);
    await page.screenshot({ path: "debug-error.png", fullPage: true });
  } finally {
    await browser.close();
  }
}

debugPropertiesPage().catch(console.error);
