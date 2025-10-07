const https = require('https');

const PRODUCTION_URL = 'https://www.concordbroker.com';
const API_URL = 'https://concordbroker-production.up.railway.app';

const checks = [
  {
    name: 'Website loads',
    test: () => checkUrl(PRODUCTION_URL),
    expected: 200
  },
  {
    name: 'Properties page loads',
    test: () => checkUrl(`${PRODUCTION_URL}/properties`),
    expected: 200
  },
  {
    name: 'API health check',
    test: () => checkUrl(`${API_URL}/health`),
    expected: 200
  },
  {
    name: 'Property search API',
    test: () => checkUrl(`${API_URL}/api/properties?county=BROWARD&limit=10`),
    expected: 200
  }
];

function checkUrl(url) {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    https.get(url, (res) => {
      const duration = Date.now() - startTime;
      resolve({
        status: res.statusCode,
        duration,
        headers: res.headers
      });
    }).on('error', reject);
  });
}

async function runChecks() {
  console.log('🚀 Production Deployment Verification\n');
  console.log('=' .repeat(60));

  let passed = 0;
  let failed = 0;

  for (const check of checks) {
    try {
      const result = await check.test();
      const success = result.status === check.expected;

      if (success) {
        console.log(`✅ ${check.name}`);
        console.log(`   Status: ${result.status} | Time: ${result.duration}ms`);
        passed++;
      } else {
        console.log(`❌ ${check.name}`);
        console.log(`   Expected: ${check.expected} | Got: ${result.status}`);
        failed++;
      }
    } catch (err) {
      console.log(`❌ ${check.name}`);
      console.log(`   Error: ${err.message}`);
      failed++;
    }
    console.log('');
  }

  console.log('=' .repeat(60));
  console.log(`\n📊 Results: ${passed} passed, ${failed} failed`);

  if (failed === 0) {
    console.log('\n✅ All checks passed! Deployment successful.');
    process.exit(0);
  } else {
    console.log('\n⚠️  Some checks failed. Review above for details.');
    process.exit(1);
  }
}

runChecks();
