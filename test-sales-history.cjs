const { chromium } = require('playwright');

async function analyzeSalesHistory() {
  const browser = await chromium.launch({
    headless: false,
    devtools: true
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  // Enable console logging
  page.on('console', msg => {
    console.log(`BROWSER CONSOLE [${msg.type()}]:`, msg.text());
  });

  // Listen for network requests
  const requests = [];
  page.on('request', request => {
    requests.push({
      url: request.url(),
      method: request.method(),
      headers: request.headers()
    });
  });

  // Listen for responses
  const responses = [];
  page.on('response', async response => {
    const url = response.url();
    const status = response.status();

    // Capture API responses
    if (url.includes('/api/') || url.includes('property') || url.includes('sales')) {
      try {
        const body = await response.text();
        responses.push({
          url,
          status,
          body: body.substring(0, 1000) // First 1000 chars to avoid huge logs
        });
        console.log(`API RESPONSE: ${url} - Status: ${status}`);
        if (body.length < 1000) {
          console.log('Response body:', body);
        }
      } catch (e) {
        responses.push({
          url,
          status,
          body: 'Error reading response body'
        });
      }
    }
  });

  try {
    console.log('Navigating to property page...');
    await page.goto('http://localhost:5176/property/3040190012860', {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    console.log('Page loaded, waiting for content...');
    await page.waitForTimeout(3000);

    // Take initial screenshot
    await page.screenshot({ path: 'sales-history-initial.png', fullPage: true });
    console.log('Initial screenshot saved as sales-history-initial.png');

    // Check if the sales history section exists
    console.log('\n=== CHECKING SALES HISTORY SECTION ===');
    const salesHistorySection = page.locator('[data-testid*="sales"], [id*="sales"], .sales-history, [class*="sales"]');
    const salesSectionExists = await salesHistorySection.count();
    console.log(`Sales history sections found: ${salesSectionExists}`);

    if (salesSectionExists > 0) {
      console.log('Sales history section found, checking content...');
      const salesContent = await salesHistorySection.first().textContent();
      console.log('Sales section content:', salesContent);

      // Check for specific sales-related elements
      const salesElements = await page.locator('*').evaluateAll(elements => {
        return elements.filter(el => {
          const text = el.textContent?.toLowerCase() || '';
          const className = el.className?.toLowerCase() || '';
          const id = el.id?.toLowerCase() || '';
          return text.includes('sales') || text.includes('history') ||
                 className.includes('sales') || id.includes('sales');
        }).map(el => ({
          tagName: el.tagName,
          className: el.className,
          id: el.id,
          textContent: el.textContent?.substring(0, 100)
        }));
      });

      console.log('Sales-related elements:', JSON.stringify(salesElements, null, 2));
    }

    // Check for tabs
    console.log('\n=== CHECKING TABS ===');
    const tabs = page.locator('[role="tab"], .tab, [data-testid*="tab"]');
    const tabCount = await tabs.count();
    console.log(`Tabs found: ${tabCount}`);

    if (tabCount > 0) {
      for (let i = 0; i < tabCount; i++) {
        const tab = tabs.nth(i);
        const tabText = await tab.textContent();
        console.log(`Tab ${i}: "${tabText}"`);

        if (tabText?.toLowerCase().includes('sales') || tabText?.toLowerCase().includes('history')) {
          console.log(`Found sales-related tab: ${tabText}`);
          await tab.click();
          await page.waitForTimeout(1000);

          // Take screenshot after clicking sales tab
          await page.screenshot({ path: 'sales-history-tab-clicked.png', fullPage: true });
          console.log('Screenshot after clicking sales tab saved');
          break;
        }
      }
    }

    // Check React DevTools data if available
    console.log('\n=== CHECKING REACT STATE ===');
    try {
      const reactData = await page.evaluate(() => {
        // Try to find React fiber data
        const findReactFiber = (dom) => {
          const key = Object.keys(dom).find(key => key.startsWith('__reactFiber') || key.startsWith('__reactInternalInstance'));
          return dom[key];
        };

        // Look for property data in window or React components
        return {
          windowPropertyData: window.propertyData || null,
          windowSalesData: window.salesData || null,
          reactFiberFound: !!document.querySelector('[data-reactroot]'),
          bodyKeys: Object.keys(document.body).filter(k => k.includes('react'))
        };
      });

      console.log('React state data:', JSON.stringify(reactData, null, 2));
    } catch (e) {
      console.log('Could not access React state:', e.message);
    }

    // Check local storage and session storage
    console.log('\n=== CHECKING STORAGE ===');
    const localStorage = await page.evaluate(() => {
      const items = {};
      for (let i = 0; i < window.localStorage.length; i++) {
        const key = window.localStorage.key(i);
        items[key] = window.localStorage.getItem(key);
      }
      return items;
    });
    console.log('localStorage:', JSON.stringify(localStorage, null, 2));

    // Wait for any async operations
    await page.waitForTimeout(2000);

    // Final screenshot
    await page.screenshot({ path: 'sales-history-final.png', fullPage: true });
    console.log('Final screenshot saved as sales-history-final.png');

    // Print network analysis
    console.log('\n=== NETWORK ANALYSIS ===');
    console.log(`Total requests: ${requests.length}`);
    console.log(`Total responses: ${responses.length}`);

    // Filter for property/sales related requests
    const propertyRequests = requests.filter(r =>
      r.url.includes('property') || r.url.includes('sales') || r.url.includes('3040190012860')
    );

    console.log('\nProperty-related requests:');
    propertyRequests.forEach((req, idx) => {
      console.log(`${idx + 1}. ${req.method} ${req.url}`);
    });

    console.log('\nProperty-related responses:');
    responses.forEach((resp, idx) => {
      console.log(`${idx + 1}. ${resp.status} ${resp.url}`);
      if (resp.body && resp.body !== 'Error reading response body') {
        console.log(`   Body preview: ${resp.body.substring(0, 200)}...`);
      }
    });

  } catch (error) {
    console.error('Error during analysis:', error);
    await page.screenshot({ path: 'sales-history-error.png', fullPage: true });
  } finally {
    await browser.close();
  }
}

analyzeSalesHistory().catch(console.error);
