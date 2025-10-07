const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  console.log('Testing Property Page UI Colors...');

  await page.goto('http://localhost:5180/property/1078130000370');
  await page.waitForTimeout(3000);

  // Check header text is visible
  const headerText = await page.$eval('.executive-header h1', el => {
    const style = window.getComputedStyle(el);
    return {
      text: el.textContent,
      color: style.color,
      background: window.getComputedStyle(el.parentElement).background
    };
  });

  console.log('\n✓ Header shows:', headerText.text);
  console.log('  Text color:', headerText.color);

  // Click on Core Property Info tab
  await page.click('button:has-text("Core Property Info")');
  await page.waitForTimeout(1000);

  // Check badge colors
  const badges = await page.$$eval('.bg-gold', elements => {
    return elements.map(el => {
      const style = window.getComputedStyle(el);
      return {
        text: el.textContent.trim(),
        textColor: style.color,
        background: style.backgroundColor
      };
    });
  });

  console.log('\n✓ Gold badges found:', badges.length);
  badges.forEach(badge => {
    console.log(`  "${badge.text}": text ${badge.textColor}`);
  });

  // Check Sales History section
  const salesHistory = await page.$eval('.card-executive:has-text("Sales History")', el => {
    const table = el.querySelector('table');
    return {
      hasTable: !!table,
      rowCount: table ? table.querySelectorAll('tbody tr').length : 0
    };
  });

  console.log('\n✓ Sales History section:');
  console.log('  Has table:', salesHistory.hasTable);
  console.log('  Row count:', salesHistory.rowCount);

  // Take screenshot
  await page.screenshot({ path: 'ui_colors_test.png', fullPage: false });
  console.log('\n✓ Screenshot saved: ui_colors_test.png');

  await browser.close();
  console.log('\n✅ Test complete!');
})();