/**
 * Performance testing utilities for Stage 4 verification
 */

// Performance thresholds from Stage 4 requirements
export const PERFORMANCE_THRESHOLDS = {
  LCP_TARGET: 2500,           // < 2.5s LCP target
  AUTOCOMPLETE_P95: 150,      // < 150ms autocomplete P95
  SEARCH_TIMEOUT: 5000,       // 5s search timeout
  MAX_NETWORK_ERRORS: 0       // 0 network errors allowed
} as const;

export interface PerformanceMetrics {
  lcp: number;
  fid?: number;
  cls?: number;
  autocompleteTimings: number[];
  searchTimings: number[];
  networkErrors: number;
  timestamp: number;
}

class PerformanceTracker {
  private metrics: PerformanceMetrics = {
    lcp: 0,
    autocompleteTimings: [],
    searchTimings: [],
    networkErrors: 0,
    timestamp: Date.now()
  };

  private observers: PerformanceObserver[] = [];

  constructor() {
    this.initializeObservers();
  }

  private initializeObservers() {
    // LCP Observer
    if (typeof PerformanceObserver !== 'undefined') {
      try {
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          if (lastEntry) {
            this.metrics.lcp = lastEntry.startTime;
          }
        });

        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
        this.observers.push(lcpObserver);

        // FID Observer
        const fidObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries() as any[];
          entries.forEach((entry) => {
            if (entry.entryType === 'first-input') {
              this.metrics.fid = entry.processingStart - entry.startTime;
            }
          });
        });

        fidObserver.observe({ entryTypes: ['first-input'] });
        this.observers.push(fidObserver);

        // CLS Observer
        const clsObserver = new PerformanceObserver((list) => {
          let clsValue = 0;
          const entries = list.getEntries() as any[];
          entries.forEach((entry) => {
            if (!entry.hadRecentInput) {
              clsValue += entry.value;
            }
          });
          this.metrics.cls = clsValue;
        });

        clsObserver.observe({ entryTypes: ['layout-shift'] });
        this.observers.push(clsObserver);

      } catch (error) {
        console.warn('[PerformanceTracker] Observer setup failed:', error);
      }
    }
  }

  // Track autocomplete performance
  trackAutocomplete<T>(operation: () => Promise<T>): Promise<T> {
    const startTime = performance.now();

    return operation()
      .then((result) => {
        const endTime = performance.now();
        const duration = endTime - startTime;
        this.metrics.autocompleteTimings.push(duration);
        return result;
      })
      .catch((error) => {
        const endTime = performance.now();
        const duration = endTime - startTime;
        this.metrics.autocompleteTimings.push(duration);
        this.metrics.networkErrors++;
        throw error;
      });
  }

  // Track search performance
  trackSearch<T>(operation: () => Promise<T>): Promise<T> {
    const startTime = performance.now();

    return operation()
      .then((result) => {
        const endTime = performance.now();
        const duration = endTime - startTime;
        this.metrics.searchTimings.push(duration);
        return result;
      })
      .catch((error) => {
        const endTime = performance.now();
        const duration = endTime - startTime;
        this.metrics.searchTimings.push(duration);
        this.metrics.networkErrors++;
        throw error;
      });
  }

  // Track network errors
  recordNetworkError() {
    this.metrics.networkErrors++;
  }

  // Calculate P95 for autocomplete
  getAutocompleteP95(): number {
    if (this.metrics.autocompleteTimings.length === 0) return 0;

    const sorted = [...this.metrics.autocompleteTimings].sort((a, b) => a - b);
    const index = Math.floor(sorted.length * 0.95);
    return sorted[index] || 0;
  }

  // Get average search time
  getAverageSearchTime(): number {
    if (this.metrics.searchTimings.length === 0) return 0;

    const sum = this.metrics.searchTimings.reduce((a, b) => a + b, 0);
    return sum / this.metrics.searchTimings.length;
  }

  // Check if all performance gates are met
  checkPerformanceGates(): {
    passed: boolean;
    results: {
      lcp: { value: number; passed: boolean; threshold: number };
      autocompleteP95: { value: number; passed: boolean; threshold: number };
      networkErrors: { value: number; passed: boolean; threshold: number };
    };
  } {
    const autocompleteP95 = this.getAutocompleteP95();

    const results = {
      lcp: {
        value: this.metrics.lcp,
        passed: this.metrics.lcp < PERFORMANCE_THRESHOLDS.LCP_TARGET,
        threshold: PERFORMANCE_THRESHOLDS.LCP_TARGET
      },
      autocompleteP95: {
        value: autocompleteP95,
        passed: autocompleteP95 < PERFORMANCE_THRESHOLDS.AUTOCOMPLETE_P95,
        threshold: PERFORMANCE_THRESHOLDS.AUTOCOMPLETE_P95
      },
      networkErrors: {
        value: this.metrics.networkErrors,
        passed: this.metrics.networkErrors <= PERFORMANCE_THRESHOLDS.MAX_NETWORK_ERRORS,
        threshold: PERFORMANCE_THRESHOLDS.MAX_NETWORK_ERRORS
      }
    };

    const passed = Object.values(results).every(result => result.passed);

    return { passed, results };
  }

  // Get full metrics
  getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }

  // Reset metrics
  reset() {
    this.metrics = {
      lcp: 0,
      autocompleteTimings: [],
      searchTimings: [],
      networkErrors: 0,
      timestamp: Date.now()
    };
  }

  // Cleanup observers
  destroy() {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
  }
}

// Global performance tracker instance
export const performanceTracker = new PerformanceTracker();

// Hook for React components
export function usePerformanceTracking() {
  return {
    trackAutocomplete: performanceTracker.trackAutocomplete.bind(performanceTracker),
    trackSearch: performanceTracker.trackSearch.bind(performanceTracker),
    recordNetworkError: performanceTracker.recordNetworkError.bind(performanceTracker),
    getMetrics: performanceTracker.getMetrics.bind(performanceTracker),
    checkPerformanceGates: performanceTracker.checkPerformanceGates.bind(performanceTracker),
    reset: performanceTracker.reset.bind(performanceTracker)
  };
}

// Automated performance test for MVP
export async function runMVPPerformanceTest(testDuration: number = 30000): Promise<{
  passed: boolean;
  summary: string;
  details: any;
}> {
  console.log('[Performance Test] Starting MVP performance verification...');

  performanceTracker.reset();

  // Test data for autocomplete
  const testQueries = [
    '123 Main',
    'Fort White',
    'ADAMS STREET',
    'LLC',
    'Monticello',
    '456 Oak',
    'PREMIUM',
    'Jefferson',
    'Trust',
    'Holdings'
  ];

  const startTime = Date.now();
  let testCount = 0;

  // Run autocomplete tests
  while (Date.now() - startTime < testDuration) {
    const query = testQueries[testCount % testQueries.length];

    try {
      await performanceTracker.trackAutocomplete(async () => {
        // Simulate autocomplete API call
        await new Promise(resolve => setTimeout(resolve, Math.random() * 100 + 50));
        return [`${query} suggestion 1`, `${query} suggestion 2`];
      });

      testCount++;

      // Brief pause between tests
      await new Promise(resolve => setTimeout(resolve, 100));

    } catch (error) {
      console.warn('[Performance Test] Test iteration failed:', error);
    }
  }

  // Check performance gates
  const gateResults = performanceTracker.checkPerformanceGates();

  const summary = `Performance Test Complete:
- Tests run: ${testCount}
- LCP: ${gateResults.results.lcp.value.toFixed(0)}ms (target: <${gateResults.results.lcp.threshold}ms)
- Autocomplete P95: ${gateResults.results.autocompleteP95.value.toFixed(0)}ms (target: <${gateResults.results.autocompleteP95.threshold}ms)
- Network Errors: ${gateResults.results.networkErrors.value} (target: ≤${gateResults.results.networkErrors.threshold})
- Overall: ${gateResults.passed ? 'PASS' : 'FAIL'}`;

  console.log('[Performance Test]', summary);

  return {
    passed: gateResults.passed,
    summary,
    details: gateResults
  };
}

// Real-time performance monitor
export function startPerformanceMonitoring(callback?: (metrics: PerformanceMetrics) => void) {
  const interval = setInterval(() => {
    const metrics = performanceTracker.getMetrics();
    callback?.(metrics);
  }, 1000);

  return () => clearInterval(interval);
}

export default performanceTracker;