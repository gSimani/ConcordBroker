const puppeteer = require('puppeteer');

(async () => {
  console.log('Starting browser debug...');

  const browser = await puppeteer.launch({
    headless: false,  // Show browser window
    devtools: true    // Auto-open DevTools
  });

  const page = await browser.newPage();

  // Capture console logs
  page.on('console', msg => {
    for (let i = 0; i < msg.args().length; ++i)
      console.log(`CONSOLE [${msg.type().toUpperCase()}]: ${msg.args()[i]}`);
  });

  // Capture page errors
  page.on('pageerror', error => {
    console.error('PAGE ERROR:', error.message);
  });

  // Capture response errors
  page.on('response', response => {
    if (!response.ok() && !response.url().includes('favicon')) {
      console.log(`HTTP ${response.status()} - ${response.url()}`);
    }
  });

  console.log('Navigating to http://localhost:5178/properties ...');

  try {
    await page.goto('http://localhost:5178/properties', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });

    // Wait a bit for React to mount
    await page.waitForTimeout(2000);

    // Check if React mounted
    const rootContent = await page.evaluate(() => {
      const root = document.getElementById('root');
      return {
        exists: !!root,
        hasContent: root ? root.innerHTML.length > 0 : false,
        contentLength: root ? root.innerHTML.length : 0,
        innerHTML: root ? root.innerHTML.substring(0, 100) : null
      };
    });

    console.log('\n=== ROOT ELEMENT STATUS ===');
    console.log('Root exists:', rootContent.exists);
    console.log('Has content:', rootContent.hasContent);
    console.log('Content length:', rootContent.contentLength);
    console.log('First 100 chars:', rootContent.innerHTML);

    // Check for React
    const reactInfo = await page.evaluate(() => {
      return {
        reactInWindow: !!window.React,
        reactVersion: window.React ? window.React.version : null,
        reactDevTools: !!window.__REACT_DEVTOOLS_GLOBAL_HOOK__,
        reactRoot: !!(document.getElementById('root')._reactRootContainer)
      };
    });

    console.log('\n=== REACT STATUS ===');
    console.log('React in window:', reactInfo.reactInWindow);
    console.log('React version:', reactInfo.reactVersion);
    console.log('DevTools hook:', reactInfo.reactDevTools);
    console.log('React root container:', reactInfo.reactRoot);

    console.log('\nBrowser window is open. Check the DevTools Console tab for errors.');
    console.log('Press Ctrl+C to close when done inspecting.');

    // Keep browser open for inspection
    await new Promise(() => {});

  } catch (error) {
    console.error('Navigation error:', error.message);
  }
})();