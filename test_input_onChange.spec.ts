import { test, expect } from '@playwright/test';

test('Test if inputs trigger onChange', async ({ page }) => {
  // Capture console logs
  const logs: string[] = [];
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('handleFilterChange') || text.includes('Filters state changed')) {
      logs.push(text);
      console.log(`📝 ${text}`);
    }
  });

  console.log('\\n=== Testing Input onChange ===\\n');

  // Navigate
  await page.goto('http://localhost:5178/properties', { timeout: 15000 });
  await page.waitForTimeout(2000);

  // Open Advanced Filters
  await page.locator('button:has-text("Advanced Filters")').click();
  await page.waitForTimeout(1000);
  console.log('✓ Advanced Filters opened');

  //  Clear logs before filling
  logs.length = 0;

  // Fill Min Building SqFt
  console.log('\\nFilling Min Building SqFt...');
  const minSection = page.locator('div').filter({ hasText: /^Min Building SqFt$/ });
  const minInput = minSection.getByRole('textbox');

  await minInput.click();
  await page.waitForTimeout(500);
  await minInput.fill('10000');
  await page.waitForTimeout(1000);

  console.log(`\\nLogs after filling Min: ${logs.length} logs`);
  logs.forEach(log => console.log(`  - ${log}`));

  // Clear logs
  logs.length = 0;

  // Fill Max Building SqFt
  console.log('\\nFilling Max Building SqFt...');
  const maxSection = page.locator('div').filter({ hasText: /^Max Building SqFt$/ });
  const maxInput = maxSection.getByRole('textbox');

  await maxInput.click();
  await page.waitForTimeout(500);
  await maxInput.fill('20000');
  await page.waitForTimeout(1000);

  console.log(`\\nLogs after filling Max: ${logs.length} logs`);
  logs.forEach(log => console.log(`  - ${log}`));

  // Blur the input to trigger any onBlur handlers
  await page.locator('body').click();
  await page.waitForTimeout(1000);

  console.log(`\\nTotal handleFilterChange logs: ${logs.filter(l => l.includes('handleFilterChange')).length}`);
  console.log(`Total state change logs: ${logs.filter(l => l.includes('Filters state changed')).length}`);

  // Now check the actual React state by evaluating in page context
  const filterState = await page.evaluate(() => {
    // Try to access React internals (this is a hack but works for debugging)
    const root = document.querySelector('#root');
    if (root && (root as any)._reactRootContainer) {
      return 'React state not directly accessible';
    }
    return 'Unable to read state';
  });

  console.log(`\\nReact state: ${filterState}`);

  console.log('\\n=== Test Complete ===');
});
