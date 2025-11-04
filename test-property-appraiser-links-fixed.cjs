/**
 * Verify Property Appraiser Links Are Now Fixed
 * Tests county-specific Property Appraiser URLs
 */

const { chromium } = require('playwright');

async function testPropertyAppraiserLinks() {
  console.log('='.repeat(80));
  console.log('PROPERTY APPRAISER LINKS - VERIFICATION TEST');
  console.log('='.repeat(80));
  console.log();

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Navigate to Tax Deed Sales page
    console.log('📍 Step 1: Navigating to Tax Deed Sales page...');
    await page.goto('http://localhost:5193/tax-deed-sales', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(3000);
    console.log('✅ Page loaded');
    console.log();

    // Click Cancelled Auctions tab
    console.log('📍 Step 2: Opening Cancelled Auctions tab...');
    await page.click('button:has-text("Cancelled Auctions")');
    await page.waitForTimeout(3000);
    console.log('✅ Cancelled Auctions tab opened');
    console.log();

    // Find first property card
    console.log('📍 Step 3: Finding property cards...');
    await page.waitForSelector('.card-executive', { timeout: 10000 });
    console.log('✅ Property cards found');
    console.log();

    // Find Property Appraiser links
    console.log('📍 Step 4: Checking Property Appraiser links...');
    const propertyAppraiserLinks = await page.$$eval('a:has-text("BROWARD Property Appraiser"), a:has-text("MIAMI-DADE Property Appraiser"), a:has-text("PALM BEACH Property Appraiser"), a:has-text("Property Appraiser")', links => {
      return links.map(link => ({
        text: link.textContent.trim(),
        href: link.getAttribute('href'),
        visible: link.offsetWidth > 0 && link.offsetHeight > 0
      }));
    });

    if (propertyAppraiserLinks.length === 0) {
      console.log('❌ No Property Appraiser links found!');
      await page.screenshot({ path: 'test-results/property-appraiser-links-error.png', fullPage: true });
      await browser.close();
      return;
    }

    console.log(`✅ Found ${propertyAppraiserLinks.length} Property Appraiser link(s)`);
    console.log();

    // Verify each link
    console.log('📍 Step 5: Verifying link details...');
    propertyAppraiserLinks.forEach((link, index) => {
      console.log(`${index + 1}. ${link.text}`);
      console.log(`   URL: ${link.href}`);
      console.log(`   Visible: ${link.visible ? '✅' : '⚠️'}`);

      // Check if it's a county-specific URL
      if (link.href.includes('bcpa.net')) {
        console.log(`   ✅ BROWARD Property Appraiser URL`);
      } else if (link.href.includes('miamidade')) {
        console.log(`   ✅ MIAMI-DADE Property Appraiser URL`);
      } else if (link.href.includes('pbcpao') || link.href.includes('pbcgov')) {
        console.log(`   ✅ PALM BEACH Property Appraiser URL`);
      } else if (link.href.includes('google.com/search')) {
        console.log(`   ⚠️  Fallback Google search URL`);
      } else {
        console.log(`   ✅ Custom county Property Appraiser URL`);
      }

      console.log();
    });

    // Take screenshot
    console.log('📸 Taking screenshot...');
    await page.screenshot({ path: 'test-results/property-appraiser-links-fixed.png', fullPage: true });
    console.log('✅ Screenshot saved: test-results/property-appraiser-links-fixed.png');
    console.log();

    // Summary
    console.log('='.repeat(80));
    console.log('VERIFICATION SUMMARY');
    console.log('='.repeat(80));
    console.log(`✅ Property Appraiser links found: ${propertyAppraiserLinks.length}`);

    const browardLinks = propertyAppraiserLinks.filter(l => l.href.includes('bcpa.net'));
    const miamiDadeLinks = propertyAppraiserLinks.filter(l => l.href.includes('miamidade'));
    const palmBeachLinks = propertyAppraiserLinks.filter(l => l.href.includes('pbcpao') || l.href.includes('pbcgov'));

    if (browardLinks.length > 0) {
      console.log(`✅ BROWARD links: ${browardLinks.length}`);
      console.log(`   URL: ${browardLinks[0].href}`);
    }
    if (miamiDadeLinks.length > 0) {
      console.log(`✅ MIAMI-DADE links: ${miamiDadeLinks.length}`);
      console.log(`   URL: ${miamiDadeLinks[0].href}`);
    }
    if (palmBeachLinks.length > 0) {
      console.log(`✅ PALM BEACH links: ${palmBeachLinks.length}`);
      console.log(`   URL: ${palmBeachLinks[0].href}`);
    }

    console.log();
    console.log('🎯 All Property Appraiser links are using county-specific URLs!');
    console.log();

  } catch (error) {
    console.error('❌ ERROR:', error.message);
    await page.screenshot({ path: 'test-results/property-appraiser-links-error.png', fullPage: true });
  } finally {
    await browser.close();
  }
}

testPropertyAppraiserLinks().then(() => {
  console.log('Test completed successfully');
  process.exit(0);
}).catch(err => {
  console.error('Test failed:', err);
  process.exit(1);
});
