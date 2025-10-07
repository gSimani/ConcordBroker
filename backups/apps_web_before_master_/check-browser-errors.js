const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();

  const errors = [];
  
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });
  
  page.on('pageerror', error => {
    errors.push('PAGE ERROR: ' + error.message);
  });

  try {
    await page.goto('http://localhost:5178/properties', { waitUntil: 'networkidle0', timeout: 10000 });
  } catch (e) {
    console.log('Navigation error:', e.message);
  }

  const hasContent = await page.evaluate(() => {
    const root = document.getElementById('root');
    return root ? root.innerHTML.length : 0;
  });

  console.log('Root element content length:', hasContent);

  if (errors.length > 0) {
    console.log('
=== ERRORS FOUND ===');
    errors.forEach(err => console.log(err));
  }

  await browser.close();
})();