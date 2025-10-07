const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function compareWebsites() {
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
  });

  const results = {
    timestamp: new Date().toISOString(),
    comparisons: []
  };

  try {
    console.log('🔍 Starting production website comparison...\n');

    // Test 1: Production Website
    console.log('📸 Capturing PRODUCTION website (https://www.concordbroker.com)...');
    const prodPage = await context.newPage();
    await prodPage.goto('https://www.concordbroker.com', {
      waitUntil: 'networkidle',
      timeout: 30000
    });
    await prodPage.waitForTimeout(3000);

    const prodContent = {
      title: await prodPage.title(),
      url: prodPage.url(),
      bodyText: await prodPage.evaluate(() => document.body?.innerText?.substring(0, 500) || ''),
      hasReactRoot: await prodPage.evaluate(() => !!document.getElementById('root')),
      mainHeading: await prodPage.evaluate(() => document.querySelector('h1')?.innerText || ''),
      navigation: await prodPage.evaluate(() => {
        const navItems = Array.from(document.querySelectorAll('nav a, header a'));
        return navItems.slice(0, 10).map(a => ({ text: a.innerText, href: a.href }));
      }),
      hasPropertySearch: await prodPage.evaluate(() => {
        return !!document.querySelector('input[placeholder*="property"], input[placeholder*="address"], input[placeholder*="search"]');
      }),
      scriptSources: await prodPage.evaluate(() => {
        return Array.from(document.querySelectorAll('script[src]'))
          .map(s => s.src)
          .filter(src => !src.includes('google') && !src.includes('analytics'))
          .slice(0, 5);
      })
    };

    await prodPage.screenshot({ path: 'production-site.png', fullPage: false });
    console.log('✅ Production site captured\n');

    results.comparisons.push({
      name: 'PRODUCTION',
      url: 'https://www.concordbroker.com',
      ...prodContent
    });

    // Test 2: Local Development (Main Website 1A)
    console.log('📸 Capturing LOCAL development (http://localhost:5173)...');
    const localPage = await context.newPage();

    try {
      await localPage.goto('http://localhost:5173', {
        waitUntil: 'networkidle',
        timeout: 15000
      });
      await localPage.waitForTimeout(2000);

      const localContent = {
        title: await localPage.title(),
        url: localPage.url(),
        bodyText: await localPage.evaluate(() => document.body?.innerText?.substring(0, 500) || ''),
        hasReactRoot: await localPage.evaluate(() => !!document.getElementById('root')),
        mainHeading: await localPage.evaluate(() => document.querySelector('h1')?.innerText || ''),
        navigation: await localPage.evaluate(() => {
          const navItems = Array.from(document.querySelectorAll('nav a, header a'));
          return navItems.slice(0, 10).map(a => ({ text: a.innerText, href: a.href }));
        }),
        hasPropertySearch: await localPage.evaluate(() => {
          return !!document.querySelector('input[placeholder*="property"], input[placeholder*="address"], input[placeholder*="search"]');
        }),
        scriptSources: await localPage.evaluate(() => {
          return Array.from(document.querySelectorAll('script[src]'))
            .map(s => s.src)
            .filter(src => !src.includes('google') && !src.includes('analytics'))
            .slice(0, 5);
        })
      };

      await localPage.screenshot({ path: 'local-site.png', fullPage: false });
      console.log('✅ Local site captured\n');

      results.comparisons.push({
        name: 'LOCAL (WEBSITE 1A)',
        url: 'http://localhost:5173',
        ...localContent
      });
    } catch (error) {
      console.log('⚠️ Local dev server not running or accessible\n');
      results.comparisons.push({
        name: 'LOCAL (WEBSITE 1A)',
        url: 'http://localhost:5173',
        error: error.message
      });
    }

    // Test 3: Check built files
    console.log('📁 Checking built dist files...');
    const distIndexPath = path.join(__dirname, 'apps', 'web', 'dist', 'index.html');
    const backupDistPath = path.join(__dirname, 'backups', 'apps_web_before_master_', 'dist', 'index.html');

    if (fs.existsSync(distIndexPath)) {
      const distContent = fs.readFileSync(distIndexPath, 'utf8');
      console.log('✅ Main dist/index.html exists');
      results.distFiles = {
        main: {
          exists: true,
          size: distContent.length,
          hasViteScript: distContent.includes('vite') || distContent.includes('module'),
          title: distContent.match(/<title>(.*?)<\/title>/)?.[1] || ''
        }
      };
    }

    if (fs.existsSync(backupDistPath)) {
      const backupContent = fs.readFileSync(backupDistPath, 'utf8');
      console.log('✅ Backup dist/index.html exists');
      results.distFiles = results.distFiles || {};
      results.distFiles.backup = {
        exists: true,
        size: backupContent.length,
        hasViteScript: backupContent.includes('vite') || backupContent.includes('module'),
        title: backupContent.match(/<title>(.*?)<\/title>/)?.[1] || ''
      };
    }

    // Compare results
    console.log('\n' + '='.repeat(60));
    console.log('📊 COMPARISON RESULTS:');
    console.log('='.repeat(60) + '\n');

    const prod = results.comparisons.find(c => c.name === 'PRODUCTION');
    const local = results.comparisons.find(c => c.name === 'LOCAL (WEBSITE 1A)');

    if (prod && local && !local.error) {
      console.log('Title Match:', prod.title === local.title ? '✅ YES' : '❌ NO');
      console.log('  Production:', prod.title);
      console.log('  Local:', local.title);
      console.log();

      console.log('React App:', prod.hasReactRoot && local.hasReactRoot ? '✅ Both React' : '❌ Different');
      console.log('  Production has React root:', prod.hasReactRoot);
      console.log('  Local has React root:', local.hasReactRoot);
      console.log();

      console.log('Main Heading Match:', prod.mainHeading === local.mainHeading ? '✅ YES' : '❌ NO');
      console.log('  Production:', prod.mainHeading || '(no h1)');
      console.log('  Local:', local.mainHeading || '(no h1)');
      console.log();

      console.log('Property Search:',
        prod.hasPropertySearch && local.hasPropertySearch ? '✅ Both have search' :
        !prod.hasPropertySearch && !local.hasPropertySearch ? '⚠️ Neither has search' :
        '❌ Different');
      console.log();

      const contentSimilarity = calculateSimilarity(prod.bodyText, local.bodyText);
      console.log('Content Similarity:', contentSimilarity > 80 ? '✅' : contentSimilarity > 50 ? '⚠️' : '❌',
        `${contentSimilarity.toFixed(1)}%`);

      // Overall verdict
      console.log('\n' + '='.repeat(60));
      const matches = prod.title === local.title &&
                     prod.hasReactRoot === local.hasReactRoot &&
                     contentSimilarity > 70;

      console.log('🎯 VERDICT:', matches ?
        '✅ LOCAL WEBSITE 1A MATCHES PRODUCTION' :
        '❌ LOCAL DOES NOT MATCH PRODUCTION');
      console.log('='.repeat(60));

      results.verdict = {
        matches,
        similarity: contentSimilarity,
        titleMatch: prod.title === local.title,
        reactMatch: prod.hasReactRoot === local.hasReactRoot
      };
    } else if (prod) {
      console.log('❌ Could not compare - local server not accessible');
      console.log('Production site info:');
      console.log('  Title:', prod.title);
      console.log('  React App:', prod.hasReactRoot);
      console.log('  Has Search:', prod.hasPropertySearch);
    }

    // Save results
    fs.writeFileSync('website-comparison-results.json', JSON.stringify(results, null, 2));
    console.log('\n📄 Full results saved to website-comparison-results.json');
    console.log('📸 Screenshots saved: production-site.png, local-site.png');

  } catch (error) {
    console.error('❌ Error during comparison:', error.message);
    results.error = error.message;
  } finally {
    await browser.close();
  }

  return results;
}

function calculateSimilarity(str1, str2) {
  if (!str1 || !str2) return 0;

  const longer = str1.length > str2.length ? str1 : str2;
  const shorter = str1.length > str2.length ? str2 : str1;

  if (longer.length === 0) return 100;

  const editDistance = levenshteinDistance(longer, shorter);
  return ((longer.length - editDistance) / longer.length) * 100;
}

function levenshteinDistance(str1, str2) {
  const matrix = [];

  for (let i = 0; i <= str2.length; i++) {
    matrix[i] = [i];
  }

  for (let j = 0; j <= str1.length; j++) {
    matrix[0][j] = j;
  }

  for (let i = 1; i <= str2.length; i++) {
    for (let j = 1; j <= str1.length; j++) {
      if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j] + 1
        );
      }
    }
  }

  return matrix[str2.length][str1.length];
}

// Run the comparison
compareWebsites()
  .then(() => console.log('\n✅ Comparison complete!'))
  .catch(error => console.error('\n❌ Fatal error:', error));