const playwright = require('playwright');

(async () => {
  const browser = await playwright.chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  // Capture ALL console messages
  const messages = [];
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('Error fetching') || 
        text.includes('Using mock') || 
        text.includes('Search term') ||
        text.includes('064210010010')) {
      messages.push(text);
    }
  });
  
  console.log('Opening property page for parcel: 064210010010');
  await page.goto('http://localhost:5174/property/064210010010');
  await page.waitForTimeout(3000);
  
  console.log('\n=== Relevant Console Messages ===');
  if (messages.length > 0) {
    messages.forEach(msg => console.log(msg));
  } else {
    console.log('No relevant messages found');
  }
  
  // Check page content
  const content = await page.content();
  const hasOceanProperties = content.includes('Ocean Properties');
  const hasParcelId = content.includes('064210010010');
  const hasMockAddress = content.includes('1234 Ocean Boulevard');
  
  console.log('\n=== Page Content Check ===');
  console.log('Has "Ocean Properties":', hasOceanProperties);
  console.log('Has parcel "064210010010":', hasParcelId);
  console.log('Has "1234 Ocean Boulevard":', hasMockAddress);
  
  await browser.close();
})();