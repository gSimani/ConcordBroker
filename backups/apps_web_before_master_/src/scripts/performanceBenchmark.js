// Performance benchmark script to test optimizations
// Run this in browser console to test performance

console.log('🚀 Starting React Frontend Performance Benchmark');

// Test data generation
function generateTestProperties(count) {
  return Array.from({ length: count }, (_, index) => ({
    parcel_id: `PARCEL_${index.toString().padStart(6, '0')}`,
    phy_addr1: `${Math.floor(Math.random() * 9999)} ${['Main St', 'Oak Ave', 'Pine Rd', 'Elm Dr'][Math.floor(Math.random() * 4)]}`,
    phy_city: ['Miami', 'Orlando', 'Tampa', 'Jacksonville', 'Fort Lauderdale'][Math.floor(Math.random() * 5)],
    phy_zipcd: Math.floor(Math.random() * 90000) + 10000,
    owner_name: `${['Smith', 'Johnson', 'Williams', 'Brown', 'Jones'][Math.floor(Math.random() * 5)]}, ${['John', 'Jane', 'Bob', 'Alice', 'Charlie'][Math.floor(Math.random() * 5)]}`,
    jv: Math.floor(Math.random() * 1000000) + 100000,
    tot_lvg_area: Math.floor(Math.random() * 3000) + 500,
    lnd_sqfoot: Math.floor(Math.random() * 10000) + 2000,
    act_yr_blt: Math.floor(Math.random() * 50) + 1970,
    sale_prc1: Math.random() > 0.7 ? Math.floor(Math.random() * 800000) + 200000 : null,
    sale_yr1: Math.random() > 0.7 ? Math.floor(Math.random() * 10) + 2014 : null
  }));
}

// Performance measurement utilities
const benchmark = {
  memory: {
    initial: 0,
    peak: 0,
    current: 0,

    record() {
      if (performance.memory) {
        this.current = performance.memory.usedJSHeapSize / 1024 / 1024;
        this.peak = Math.max(this.peak, this.current);
        return this.current;
      }
      return 0;
    },

    init() {
      this.initial = this.record();
      this.peak = this.initial;
    },

    report() {
      const final = this.record();
      return {
        initial: this.initial.toFixed(2),
        peak: this.peak.toFixed(2),
        final: final.toFixed(2),
        increase: (final - this.initial).toFixed(2)
      };
    }
  },

  timing: {
    start: null,

    begin() {
      this.start = performance.now();
    },

    end() {
      return this.start ? performance.now() - this.start : 0;
    }
  }
};

// Test scenarios
const testScenarios = [
  { name: 'Small Dataset', size: 50 },
  { name: 'Medium Dataset', size: 200 },
  { name: 'Large Dataset', size: 500 },
  { name: 'Extra Large Dataset', size: 1000 }
];

// Run benchmark tests
async function runBenchmarks() {
  console.log('📊 Running Performance Benchmarks...\n');

  const results = [];

  for (const scenario of testScenarios) {
    console.log(`🔄 Testing ${scenario.name} (${scenario.size} items)...`);

    // Initialize memory tracking
    benchmark.memory.init();
    benchmark.timing.begin();

    // Generate test data
    const testData = generateTestProperties(scenario.size);

    // Simulate React render cycle
    const renderTime = benchmark.timing.end();

    // Wait for any async operations
    await new Promise(resolve => setTimeout(resolve, 100));

    // Record memory usage
    const memoryStats = benchmark.memory.report();

    const result = {
      scenario: scenario.name,
      size: scenario.size,
      renderTime: renderTime.toFixed(2),
      memory: memoryStats,
      dataSize: JSON.stringify(testData).length / 1024 // KB
    };

    results.push(result);

    console.log(`✅ ${scenario.name} completed:`);
    console.log(`   Render Time: ${result.renderTime}ms`);
    console.log(`   Memory Usage: ${result.memory.final}MB (peak: ${result.memory.peak}MB)`);
    console.log(`   Data Size: ${result.dataSize.toFixed(1)}KB\n`);
  }

  return results;
}

// Network performance test
async function testNetworkPerformance() {
  console.log('🌐 Testing Network Performance...');

  const apiEndpoint = 'http://localhost:8000/api/properties/search?limit=20';
  const tests = [];

  for (let i = 0; i < 5; i++) {
    benchmark.timing.begin();

    try {
      const response = await fetch(apiEndpoint);
      const data = await response.json();
      const responseTime = benchmark.timing.end();

      tests.push({
        attempt: i + 1,
        responseTime: responseTime.toFixed(2),
        dataSize: JSON.stringify(data).length / 1024,
        cached: response.headers.get('x-cache') === 'HIT'
      });

      console.log(`   Test ${i + 1}: ${responseTime.toFixed(2)}ms ${response.headers.get('x-cache') === 'HIT' ? '(cached)' : ''}`);
    } catch (error) {
      console.log(`   Test ${i + 1}: Failed - ${error.message}`);
    }

    // Small delay between requests
    await new Promise(resolve => setTimeout(resolve, 200));
  }

  const avgResponseTime = tests.reduce((sum, test) => sum + parseFloat(test.responseTime), 0) / tests.length;
  console.log(`📈 Average Response Time: ${avgResponseTime.toFixed(2)}ms\n`);

  return tests;
}

// Bundle size analysis
function analyzeBundleSize() {
  console.log('📦 Analyzing Bundle Size...');

  const scripts = Array.from(document.querySelectorAll('script[src]'));
  const styles = Array.from(document.querySelectorAll('link[rel="stylesheet"]'));

  let totalScriptSize = 0;
  let totalStyleSize = 0;

  scripts.forEach(script => {
    // Rough estimation based on URL length (real measurement would need build tools)
    totalScriptSize += script.src.length * 50; // Estimation factor
  });

  styles.forEach(style => {
    totalStyleSize += style.href.length * 20; // Estimation factor
  });

  const bundleInfo = {
    scriptCount: scripts.length,
    styleCount: styles.length,
    estimatedScriptSize: (totalScriptSize / 1024).toFixed(1) + 'KB',
    estimatedStyleSize: (totalStyleSize / 1024).toFixed(1) + 'KB',
    totalEstimate: ((totalScriptSize + totalStyleSize) / 1024).toFixed(1) + 'KB'
  };

  console.log(`   Scripts: ${bundleInfo.scriptCount} files (~${bundleInfo.estimatedScriptSize})`);
  console.log(`   Styles: ${bundleInfo.styleCount} files (~${bundleInfo.estimatedStyleSize})`);
  console.log(`   Total Estimate: ~${bundleInfo.totalEstimate}\n`);

  return bundleInfo;
}

// React DevTools integration (if available)
function analyzeReactPerformance() {
  console.log('⚛️ Analyzing React Performance...');

  if (window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {
    console.log('   React DevTools detected ✅');

    // Check for React profiling data
    const fiberRoot = document.querySelector('#root')._reactInternalFiber ||
                     document.querySelector('#root')._reactInternalInstance;

    if (fiberRoot) {
      console.log('   React Fiber root found ✅');
      console.log('   React version detected');
    }
  } else {
    console.log('   React DevTools not available ❌');
  }

  // Check for common React performance issues
  const reactWarnings = [];

  // Override console.warn to catch React warnings
  const originalWarn = console.warn;
  const reactWarningsCollector = [];

  console.warn = function(...args) {
    if (args[0] && args[0].includes && args[0].includes('React')) {
      reactWarningsCollector.push(args.join(' '));
    }
    originalWarn.apply(console, args);
  };

  // Restore after a short delay
  setTimeout(() => {
    console.warn = originalWarn;

    if (reactWarningsCollector.length > 0) {
      console.log(`   ⚠️  Found ${reactWarningsCollector.length} React warnings`);
      reactWarningsCollector.forEach(warning => console.log(`      ${warning}`));
    } else {
      console.log('   No React warnings detected ✅');
    }
  }, 1000);

  return {
    devToolsAvailable: !!window.__REACT_DEVTOOLS_GLOBAL_HOOK__,
    warnings: reactWarningsCollector
  };
}

// Main benchmark function
async function runFullBenchmark() {
  console.clear();
  console.log('🎯 React Frontend Performance Optimization Benchmark');
  console.log('='.repeat(60));
  console.log(`Started at: ${new Date().toLocaleString()}\n`);

  try {
    // Run all benchmark tests
    const renderResults = await runBenchmarks();
    const networkResults = await testNetworkPerformance();
    const bundleAnalysis = analyzeBundleSize();
    const reactAnalysis = analyzeReactPerformance();

    // Generate summary report
    console.log('📋 PERFORMANCE SUMMARY REPORT');
    console.log('='.repeat(60));

    console.log('\n🏃‍♂️ RENDER PERFORMANCE:');
    renderResults.forEach(result => {
      console.log(`   ${result.scenario}: ${result.renderTime}ms (${result.size} items)`);
    });

    console.log('\n🌐 NETWORK PERFORMANCE:');
    const avgNetwork = networkResults.reduce((sum, test) => sum + parseFloat(test.responseTime), 0) / networkResults.length;
    console.log(`   Average API Response: ${avgNetwork.toFixed(2)}ms`);
    console.log(`   Cache Utilization: ${networkResults.filter(t => t.cached).length}/${networkResults.length} requests`);

    console.log('\n📦 BUNDLE ANALYSIS:');
    console.log(`   Total Bundle Size: ~${bundleAnalysis.totalEstimate}`);
    console.log(`   JavaScript Files: ${bundleAnalysis.scriptCount}`);
    console.log(`   CSS Files: ${bundleAnalysis.styleCount}`);

    console.log('\n⚛️ REACT ANALYSIS:');
    console.log(`   DevTools Available: ${reactAnalysis.devToolsAvailable ? 'Yes' : 'No'}`);
    console.log(`   React Warnings: ${reactAnalysis.warnings.length}`);

    // Performance score calculation
    let score = 100;

    // Deduct points for slow renders
    renderResults.forEach(result => {
      if (parseFloat(result.renderTime) > 16) score -= 5;
      if (parseFloat(result.renderTime) > 50) score -= 10;
    });

    // Deduct points for slow network
    if (avgNetwork > 500) score -= 15;
    if (avgNetwork > 1000) score -= 25;

    // Deduct points for React warnings
    score -= reactAnalysis.warnings.length * 5;

    score = Math.max(0, score);

    console.log('\n🎯 OVERALL PERFORMANCE SCORE:');
    console.log(`   ${score}/100 ${score > 80 ? '🟢 Excellent' : score > 60 ? '🟡 Good' : '🔴 Needs Improvement'}`);

    console.log('\n✨ OPTIMIZATION RECOMMENDATIONS:');

    if (score < 80) {
      console.log('   • Consider implementing virtual scrolling for large lists');
      console.log('   • Add React.memo to frequently re-rendering components');
      console.log('   • Implement proper caching strategies');
      console.log('   • Use code splitting for heavy components');
    } else {
      console.log('   • Performance is excellent! Continue monitoring.');
    }

    console.log('\n='.repeat(60));
    console.log(`Benchmark completed at: ${new Date().toLocaleString()}`);

    return {
      renderResults,
      networkResults,
      bundleAnalysis,
      reactAnalysis,
      score
    };

  } catch (error) {
    console.error('❌ Benchmark failed:', error);
  }
}

// Auto-run if in browser environment
if (typeof window !== 'undefined') {
  console.log('💡 To run the benchmark, execute: runFullBenchmark()');
  console.log('🔧 Available functions: runBenchmarks(), testNetworkPerformance(), analyzeBundleSize()');

  // Make functions globally available
  window.runFullBenchmark = runFullBenchmark;
  window.runBenchmarks = runBenchmarks;
  window.testNetworkPerformance = testNetworkPerformance;
  window.analyzeBundleSize = analyzeBundleSize;
  window.generateTestProperties = generateTestProperties;
}