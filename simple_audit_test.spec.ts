import { test, expect } from '@playwright/test';

test('Quick ConcordBroker Audit', async ({ page }) => {
  console.log('🔍 Starting quick audit...\n');

  // Set longer timeout
  test.setTimeout(60000);

  const consoleMessages = [];
  const errors = [];
  const networkCalls = [];

  // Capture console
  page.on('console', msg => {
    const text = msg.text();
    consoleMessages.push({ type: msg.type(), text });
    if (msg.type() === 'error') {
      errors.push(text);
      console.log('❌ Console Error:', text);
    }
  });

  // Capture all network calls
  page.on('request', request => {
    if (request.url().includes('properties') || request.url().includes('supabase')) {
      networkCalls.push({
        url: request.url(),
        method: request.method()
      });
      console.log('📡 Network:', request.method(), request.url().substring(0, 100));
    }
  });

  page.on('response', async response => {
    if (response.url().includes('properties') || response.url().includes('supabase')) {
      const status = response.status();
      console.log(`   → ${status}`, response.url().substring(0, 100));

      if (status === 200 && response.url().includes('florida_parcels')) {
        try {
          const text = await response.text();
          console.log(`   ✅ Supabase Response Length: ${text.length} chars`);
        } catch(e) {
          // ignore
        }
      }
    }
  });

  console.log('\n🌐 Navigating to http://localhost:5181/properties...');

  try {
    await page.goto('http://localhost:5181/properties', {
      waitUntil: 'domcontentloaded',
      timeout: 20000
    });

    console.log('✅ Page loaded (DOMContentLoaded)');

    // Wait a bit for React to render
    await page.waitForTimeout(5000);

    // Check for property cards
    const cards = await page.locator('[data-testid="property-card"], .property-card, [class*="MiniPropertyCard"]').count();
    console.log(`\n📊 Property cards found: ${cards}`);

    // Check for loading state
    const loading = await page.locator('[data-loading="true"], .loading, .spinner').count();
    console.log(`⏳ Loading indicators: ${loading}`);

    // Check for "0 Properties" text
    const zeroProperties = await page.textContent('body');
    if (zeroProperties?.includes('0 Properties') || zeroProperties?.includes('No properties')) {
      console.log('⚠️ "0 Properties" or "No properties" text found');
    }

    // Take screenshot
    await page.screenshot({ path: 'quick_audit.png', fullPage: true });
    console.log('📸 Screenshot saved: quick_audit.png');

    // Get total results text
    const totalText = await page.locator('text=/\\d+[KM]?\\s*Properties/i').first().textContent().catch(() => null);
    console.log(`📈 Total results text: ${totalText || 'Not found'}`);

    console.log(`\n📝 Console errors: ${errors.length}`);
    console.log(`🌐 Network calls: ${networkCalls.length}`);

  } catch (error) {
    console.log('❌ Error:', error.message);
  }

  console.log('\n✅ Audit complete');
});
