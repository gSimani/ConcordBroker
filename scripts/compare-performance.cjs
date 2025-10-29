/**
 * Performance Comparison Script
 *
 * Compares two performance test results to show improvements.
 *
 * Usage: node scripts/compare-performance.js baseline.json after-phase1.json
 */

const fs = require('fs');
const path = require('path');

function loadResults(filename) {
  const filepath = path.resolve(filename);
  if (!fs.existsSync(filepath)) {
    console.error(`❌ File not found: ${filepath}`);
    process.exit(1);
  }
  return JSON.parse(fs.readFileSync(filepath, 'utf8'));
}

function compareResults(baseline, current) {
  console.log('═══════════════════════════════════════════════════════════');
  console.log('📊 PERFORMANCE COMPARISON');
  console.log('═══════════════════════════════════════════════════════════\n');

  console.log(`Baseline: ${baseline.metadata.testDate}`);
  console.log(`Current:  ${current.metadata.testDate}`);
  console.log(`Phase:    ${current.metadata.phase || 'unknown'}\n`);

  console.log('═══════════════════════════════════════════════════════════');
  console.log('Test Results:');
  console.log('═══════════════════════════════════════════════════════════\n');

  const improvements = [];
  const regressions = [];

  for (const testName in baseline.tests) {
    const baseTest = baseline.tests[testName];
    const currTest = current.tests[testName];

    if (!baseTest.success || !currTest.success) {
      console.log(`⚠️  ${testName}: SKIPPED (test failed in one or both runs)`);
      continue;
    }

    const baseTime = baseTest.duration;
    const currTime = currTest.duration;
    const improvement = ((baseTime - currTime) / baseTime) * 100;
    const speedup = baseTime / currTime;

    let emoji = '➡️ ';
    if (improvement > 50) emoji = '🚀';
    else if (improvement > 20) emoji = '✅';
    else if (improvement < -10) emoji = '🔴';

    console.log(`${emoji} ${testName}`);
    console.log(`   Before: ${baseTime}ms`);
    console.log(`   After:  ${currTime}ms`);

    if (improvement > 0) {
      console.log(`   Improvement: ${improvement.toFixed(1)}% faster (${speedup.toFixed(1)}x speedup)`);
      improvements.push({ name: testName, improvement, speedup });
    } else {
      console.log(`   Regression: ${Math.abs(improvement).toFixed(1)}% slower`);
      regressions.push({ name: testName, regression: Math.abs(improvement) });
    }
    console.log('');
  }

  // Summary
  console.log('═══════════════════════════════════════════════════════════');
  console.log('📈 SUMMARY');
  console.log('═══════════════════════════════════════════════════════════\n');

  if (improvements.length > 0) {
    console.log(`✅ Improvements: ${improvements.length} tests faster`);
    const avgImprovement = improvements.reduce((sum, i) => sum + i.improvement, 0) / improvements.length;
    const avgSpeedup = improvements.reduce((sum, i) => sum + i.speedup, 0) / improvements.length;
    console.log(`   Average improvement: ${avgImprovement.toFixed(1)}%`);
    console.log(`   Average speedup: ${avgSpeedup.toFixed(1)}x\n`);

    console.log('Top 3 Improvements:');
    improvements
      .sort((a, b) => b.improvement - a.improvement)
      .slice(0, 3)
      .forEach((imp, idx) => {
        console.log(`   ${idx + 1}. ${imp.name}: ${imp.improvement.toFixed(1)}% (${imp.speedup.toFixed(1)}x)`);
      });
  }

  if (regressions.length > 0) {
    console.log(`\n⚠️  Regressions: ${regressions.length} tests slower`);
    const avgRegression = regressions.reduce((sum, r) => sum + r.regression, 0) / regressions.length;
    console.log(`   Average regression: ${avgRegression.toFixed(1)}%\n`);

    console.log('Regressions:');
    regressions.forEach((reg, idx) => {
      console.log(`   ${idx + 1}. ${reg.name}: ${reg.regression.toFixed(1)}% slower`);
    });
  }

  console.log('\n═══════════════════════════════════════════════════════════\n');

  // Overall verdict
  if (improvements.length > regressions.length) {
    console.log('🎉 VERDICT: Overall performance IMPROVED!');
  } else if (regressions.length > improvements.length) {
    console.log('⚠️  VERDICT: Overall performance REGRESSED. Review changes.');
  } else {
    console.log('➡️  VERDICT: Performance roughly the same.');
  }

  console.log('\n═══════════════════════════════════════════════════════════\n');
}

// Main
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length !== 2) {
    console.log('Usage: node scripts/compare-performance.js <baseline.json> <current.json>');
    console.log('Example: node scripts/compare-performance.js BASELINE_PERFORMANCE.json after-phase1.json');
    process.exit(1);
  }

  const baseline = loadResults(args[0]);
  const current = loadResults(args[1]);

  compareResults(baseline, current);
}

module.exports = { compareResults };
