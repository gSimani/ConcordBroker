// Performance monitoring utilities for React optimizations

interface PerformanceMetrics {
  renderTime: number;
  componentCount: number;
  memoryUsage: number;
  bundleSize: number;
  firstContentfulPaint: number;
  largestContentfulPaint: number;
  timeToInteractive: number;
  cacheHitRate: number;
  networkRequests: number;
}

interface ComponentRenderTime {
  componentName: string;
  renderTime: number;
  rerenderCount: number;
  propsChanged: boolean;
}

class PerformanceMonitor {
  private metrics: PerformanceMetrics;
  private renderTimes: Map<string, ComponentRenderTime> = new Map();
  private networkRequestCount = 0;
  private cacheHits = 0;
  private cacheMisses = 0;
  private observers: PerformanceObserver[] = [];

  constructor() {
    this.metrics = {
      renderTime: 0,
      componentCount: 0,
      memoryUsage: 0,
      bundleSize: 0,
      firstContentfulPaint: 0,
      largestContentfulPaint: 0,
      timeToInteractive: 0,
      cacheHitRate: 0,
      networkRequests: 0
    };

    this.setupPerformanceObservers();
    this.trackNetworkRequests();
  }

  // Setup Web Performance API observers
  private setupPerformanceObservers() {
    if ('PerformanceObserver' in window) {
      // First Contentful Paint
      const fcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          if (entry.name === 'first-contentful-paint') {
            this.metrics.firstContentfulPaint = entry.startTime;
          }
        });
      });
      fcpObserver.observe({ entryTypes: ['paint'] });
      this.observers.push(fcpObserver);

      // Largest Contentful Paint
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        this.metrics.largestContentfulPaint = lastEntry.startTime;
      });
      lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
      this.observers.push(lcpObserver);

      // Layout shifts
      const clsObserver = new PerformanceObserver((list) => {
        let clsValue = 0;
        for (const entry of list.getEntries()) {
          if (!(entry as any).hadRecentInput) {
            clsValue += (entry as any).value;
          }
        }
        console.log('Cumulative Layout Shift:', clsValue);
      });
      clsObserver.observe({ entryTypes: ['layout-shift'] });
      this.observers.push(clsObserver);
    }
  }

  // Track network requests for caching analysis
  private trackNetworkRequests() {
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      this.networkRequestCount++;
      const response = await originalFetch(...args);

      // Check if response is from cache
      if (response.headers.get('x-cache') === 'HIT' ||
          response.headers.get('cache-control')?.includes('max-age')) {
        this.cacheHits++;
      } else {
        this.cacheMisses++;
      }

      this.updateCacheHitRate();
      return response;
    };
  }

  // Track component render times
  trackComponentRender(componentName: string, renderTime: number, propsChanged: boolean = false) {
    const existing = this.renderTimes.get(componentName);

    if (existing) {
      existing.renderTime = (existing.renderTime + renderTime) / 2; // Average
      existing.rerenderCount++;
      existing.propsChanged = propsChanged;
    } else {
      this.renderTimes.set(componentName, {
        componentName,
        renderTime,
        rerenderCount: 1,
        propsChanged
      });
    }
  }

  // Get memory usage
  getMemoryUsage(): number {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      return memory.usedJSHeapSize / 1024 / 1024; // MB
    }
    return 0;
  }

  // Calculate bundle size (estimated)
  getBundleSize(): number {
    const scripts = Array.from(document.querySelectorAll('script[src]'));
    let totalSize = 0;

    scripts.forEach((script: any) => {
      // This is an estimation - in real scenarios you'd get this from build tools
      totalSize += script.src.length * 100; // Rough estimate
    });

    return totalSize / 1024; // KB
  }

  // Update cache hit rate
  private updateCacheHitRate() {
    const total = this.cacheHits + this.cacheMisses;
    this.metrics.cacheHitRate = total > 0 ? (this.cacheHits / total) * 100 : 0;
  }

  // Get performance snapshot
  getMetrics(): PerformanceMetrics {
    this.metrics.memoryUsage = this.getMemoryUsage();
    this.metrics.bundleSize = this.getBundleSize();
    this.metrics.networkRequests = this.networkRequestCount;
    this.metrics.componentCount = this.renderTimes.size;

    return { ...this.metrics };
  }

  // Get component render statistics
  getComponentStats(): ComponentRenderTime[] {
    return Array.from(this.renderTimes.values()).sort((a, b) => b.renderTime - a.renderTime);
  }

  // Get optimization recommendations
  getOptimizationRecommendations(): string[] {
    const recommendations: string[] = [];
    const stats = this.getComponentStats();
    const metrics = this.getMetrics();

    // Check for slow components
    stats.forEach(stat => {
      if (stat.renderTime > 16) { // More than one frame
        recommendations.push(`${stat.componentName} is rendering slowly (${stat.renderTime.toFixed(2)}ms). Consider optimizing with React.memo or useMemo.`);
      }

      if (stat.rerenderCount > 10 && stat.propsChanged) {
        recommendations.push(`${stat.componentName} is re-rendering frequently (${stat.rerenderCount} times). Check prop stability.`);
      }
    });

    // Check memory usage
    if (metrics.memoryUsage > 100) {
      recommendations.push(`High memory usage detected (${metrics.memoryUsage.toFixed(2)}MB). Consider implementing virtual scrolling or component cleanup.`);
    }

    // Check cache performance
    if (metrics.cacheHitRate < 60) {
      recommendations.push(`Low cache hit rate (${metrics.cacheHitRate.toFixed(1)}%). Improve caching strategy for better performance.`);
    }

    // Check LCP
    if (metrics.largestContentfulPaint > 2500) {
      recommendations.push(`Largest Contentful Paint is slow (${metrics.largestContentfulPaint.toFixed(0)}ms). Consider code splitting and lazy loading.`);
    }

    return recommendations;
  }

  // Generate performance report
  generateReport(): string {
    const metrics = this.getMetrics();
    const stats = this.getComponentStats();
    const recommendations = this.getOptimizationRecommendations();

    return `
# Frontend Performance Report

## Core Web Vitals
- First Contentful Paint: ${metrics.firstContentfulPaint.toFixed(0)}ms
- Largest Contentful Paint: ${metrics.largestContentfulPaint.toFixed(0)}ms
- Time to Interactive: ${metrics.timeToInteractive.toFixed(0)}ms

## Resource Usage
- Memory Usage: ${metrics.memoryUsage.toFixed(2)}MB
- Bundle Size: ${metrics.bundleSize.toFixed(2)}KB
- Network Requests: ${metrics.networkRequests}
- Cache Hit Rate: ${metrics.cacheHitRate.toFixed(1)}%

## Component Performance
${stats.slice(0, 5).map(stat =>
  `- ${stat.componentName}: ${stat.renderTime.toFixed(2)}ms (${stat.rerenderCount} renders)`
).join('\n')}

## Optimization Recommendations
${recommendations.map(rec => `- ${rec}`).join('\n')}

Generated at: ${new Date().toISOString()}
    `.trim();
  }

  // Clean up observers
  destroy() {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
  }
}

// React hook for performance monitoring
export function usePerformanceMonitor() {
  const [monitor] = React.useState(() => new PerformanceMonitor());
  const [metrics, setMetrics] = React.useState<PerformanceMetrics>(() => monitor.getMetrics());

  const updateMetrics = React.useCallback(() => {
    setMetrics(monitor.getMetrics());
  }, [monitor]);

  React.useEffect(() => {
    const interval = setInterval(updateMetrics, 5000); // Update every 5 seconds
    return () => {
      clearInterval(interval);
      monitor.destroy();
    };
  }, [monitor, updateMetrics]);

  const trackRender = React.useCallback((componentName: string, renderTime: number, propsChanged?: boolean) => {
    monitor.trackComponentRender(componentName, renderTime, propsChanged);
  }, [monitor]);

  return {
    metrics,
    trackRender,
    getComponentStats: () => monitor.getComponentStats(),
    getRecommendations: () => monitor.getOptimizationRecommendations(),
    generateReport: () => monitor.generateReport(),
    updateMetrics
  };
}

// HOC for tracking component performance
export function withPerformanceTracking<T extends object>(
  WrappedComponent: React.ComponentType<T>,
  componentName?: string
) {
  const displayName = componentName || WrappedComponent.displayName || WrappedComponent.name;

  const PerformanceTrackedComponent = React.memo((props: T) => {
    const renderStartTime = React.useRef(performance.now());
    const { trackRender } = usePerformanceMonitor();
    const previousProps = React.useRef<T>(props);

    React.useEffect(() => {
      const renderTime = performance.now() - renderStartTime.current;
      const propsChanged = JSON.stringify(previousProps.current) !== JSON.stringify(props);

      trackRender(displayName, renderTime, propsChanged);
      previousProps.current = props;
    });

    renderStartTime.current = performance.now();

    return <WrappedComponent {...props} />;
  });

  PerformanceTrackedComponent.displayName = `withPerformanceTracking(${displayName})`;

  return PerformanceTrackedComponent;
}

// Performance testing utilities
export const performanceUtils = {
  measureRenderTime: (fn: () => void): number => {
    const start = performance.now();
    fn();
    return performance.now() - start;
  },

  measureAsyncOperation: async (fn: () => Promise<void>): Promise<number> => {
    const start = performance.now();
    await fn();
    return performance.now() - start;
  },

  simulateSlowNetwork: (delay: number = 1000) => {
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      await new Promise(resolve => setTimeout(resolve, delay));
      return originalFetch(...args);
    };
  }
};

// Export singleton instance
export const performanceMonitor = new PerformanceMonitor();

// Add React import
import React from 'react';