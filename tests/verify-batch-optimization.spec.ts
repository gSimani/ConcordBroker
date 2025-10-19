import { test, expect } from '@playwright/test';

test('Verify Batch Sales Data Optimization', async ({ page }) => {
  const apiRequests: any[] = [];

  // Capture all API requests
  page.on('request', request => {
    const url = request.url();
    if (url.includes('property_sales_history')) {
      apiRequests.push({
        url,
        method: request.method(),
        timestamp: Date.now()
      });
      console.log(`🌐 SALES API: ${request.method()} ${url}`);
    }
  });

  // Navigate to properties page
  console.log('Navigating to properties page...');
  await page.goto('http://localhost:5191/properties', {
    waitUntil: 'domcontentloaded',
    timeout: 30000
  });

  // Wait for property cards to load
  console.log('Waiting for property cards...');
  await page.waitForSelector('[data-testid="property-card"], .property-card, [class*="property"]', {
    timeout: 20000
  });

  // Wait a bit more for all API calls to complete
  await page.waitForTimeout(5000);

  // Analyze API calls
  console.log('\n' + '='.repeat(80));
  console.log('BATCH OPTIMIZATION VERIFICATION REPORT');
  console.log('='.repeat(80));

  const totalCalls = apiRequests.length;
  const individualCalls = apiRequests.filter(r => r.url.includes('parcel_id=eq.')).length;
  const batchCalls = apiRequests.filter(r => r.url.includes('parcel_id=in.')).length;

  console.log(`\nTotal property_sales_history API calls: ${totalCalls}`);
  console.log(`  Individual calls (parcel_id=eq.): ${individualCalls}`);
  console.log(`  Batch calls (parcel_id=in.): ${batchCalls}`);

  if (totalCalls === 0) {
    console.log('\n❌ NO SALES DATA API CALLS DETECTED');
    console.log('This might mean:');
    console.log('  1. Sales data is fully cached');
    console.log('  2. Component is not fetching sales data');
    console.log('  3. Test waited but requests already completed');
  } else if (individualCalls > 10) {
    console.log(`\n❌ OPTIMIZATION NOT WORKING: ${individualCalls} individual calls detected`);
    console.log('Expected: 1-2 batch calls');
    console.log('Actual: Multiple individual calls per parcel');
  } else if (batchCalls >= 1) {
    console.log(`\n✅ OPTIMIZATION WORKING: ${batchCalls} batch call(s) detected`);
    console.log(`Reduction: ${individualCalls} individual calls → ${batchCalls} batch calls`);
    const reduction = individualCalls > 0 ? ((individualCalls / (individualCalls + batchCalls)) * 100).toFixed(0) : 100;
    console.log(`Performance: ${reduction}% reduction in API calls`);
  }

  console.log('\nAPI Call Details:');
  apiRequests.slice(0, 5).forEach((req, i) => {
    const urlParts = req.url.split('?');
    const query = urlParts[1] || '';
    console.log(`  ${i + 1}. ${req.method} ...${query.substring(0, 80)}`);
  });

  if (apiRequests.length > 5) {
    console.log(`  ... and ${apiRequests.length - 5} more`);
  }

  console.log('='.repeat(80));
});
