/**
 * Enhanced Real User Monitoring (RUM) and Core Web Vitals Tracking
 * Comprehensive client-side performance monitoring
 */

interface WebVitalsMetric {
  name: string;
  value: number;
  delta: number;
  id: string;
  navigationType: string;
  rating: 'good' | 'needs-improvement' | 'poor';
}

interface RUMMetric {
  timestamp: number;
  sessionId: string;
  pageUrl: string;
  referrer: string;
  userAgent: string;
  deviceType: 'mobile' | 'tablet' | 'desktop';
  connectionType: string;
  screenResolution: string;
  viewport: string;

  // Core Web Vitals
  lcp?: number;
  fid?: number;
  cls?: number;
  fcp?: number;
  ttfb?: number;

  // Additional metrics
  domContentLoaded?: number;
  windowLoaded?: number;
  firstPaint?: number;
  resourceLoadTime?: number;

  // Custom business metrics
  searchTime?: number;
  propertyViewTime?: number;
  imageLoadTime?: number;

  // User interaction
  clickCount: number;
  scrollDepth: number;
  timeOnPage: number;

  // Error tracking
  jsErrors: Array<{
    message: string;
    filename: string;
    lineno: number;
    colno: number;
    timestamp: number;
  }>;

  // Performance issues
  longTasks: Array<{
    duration: number;
    startTime: number;
  }>;

  // Memory usage
  memoryUsage?: {
    used: number;
    total: number;
    limit: number;
  };
}

class RealUserMonitoring {
  private sessionId: string;
  private metrics: RUMMetric;
  private observers: PerformanceObserver[] = [];
  private startTime: number;
  private clickCount = 0;
  private maxScrollDepth = 0;
  private jsErrors: Array<any> = [];
  private longTasks: Array<any> = [];
  private isRecording = true;
  private sendInterval: number | null = null;
  private pendingMetrics: Partial<RUMMetric>[] = [];

  // Configuration
  private config = {
    apiEndpoint: '/api/monitoring/metric/web-vitals',
    batchSize: 10,
    sendInterval: 30000, // 30 seconds
    maxRetries: 3,
    enableDetailedTracking: true,
    enableLongTaskTracking: true,
    enableMemoryTracking: true,
    enableErrorTracking: true,
  };

  constructor(config?: Partial<typeof this.config>) {
    this.config = { ...this.config, ...config };
    this.sessionId = this.generateSessionId();
    this.startTime = performance.now();

    this.initializeMetrics();
    this.setupEventListeners();
    this.setupPerformanceObservers();
    this.startPeriodicSending();

    console.log('🎯 RUM Monitoring initialized with session:', this.sessionId);
  }

  private generateSessionId(): string {
    return `rum_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private initializeMetrics(): void {
    this.metrics = {
      timestamp: Date.now(),
      sessionId: this.sessionId,
      pageUrl: window.location.href,
      referrer: document.referrer,
      userAgent: navigator.userAgent,
      deviceType: this.getDeviceType(),
      connectionType: this.getConnectionType(),
      screenResolution: `${screen.width}x${screen.height}`,
      viewport: `${window.innerWidth}x${window.innerHeight}`,
      clickCount: 0,
      scrollDepth: 0,
      timeOnPage: 0,
      jsErrors: [],
      longTasks: []
    };
  }

  private getDeviceType(): 'mobile' | 'tablet' | 'desktop' {
    const width = window.innerWidth;
    if (width < 768) return 'mobile';
    if (width < 1024) return 'tablet';
    return 'desktop';
  }

  private getConnectionType(): string {
    const connection = (navigator as any).connection;
    if (connection) {
      return connection.effectiveType || connection.type || 'unknown';
    }
    return 'unknown';
  }

  private setupEventListeners(): void {
    // Track clicks
    document.addEventListener('click', () => {
      this.clickCount++;
      this.metrics.clickCount = this.clickCount;
    });

    // Track scroll depth
    document.addEventListener('scroll', this.throttle(() => {
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      const windowHeight = window.innerHeight;
      const documentHeight = document.documentElement.scrollHeight;

      const scrollPercent = Math.round((scrollTop + windowHeight) / documentHeight * 100);
      this.maxScrollDepth = Math.max(this.maxScrollDepth, scrollPercent);
      this.metrics.scrollDepth = this.maxScrollDepth;
    }, 250));

    // Track visibility changes
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.recordTimeOnPage();
        this.sendMetrics(); // Send immediately when page becomes hidden
      }
    });

    // Track page unload
    window.addEventListener('beforeunload', () => {
      this.recordTimeOnPage();
      this.sendMetrics();
    });

    // Track errors
    if (this.config.enableErrorTracking) {
      window.addEventListener('error', (event) => {
        this.jsErrors.push({
          message: event.message,
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
          timestamp: performance.now()
        });
        this.metrics.jsErrors = this.jsErrors;
      });

      window.addEventListener('unhandledrejection', (event) => {
        this.jsErrors.push({
          message: `Unhandled Promise Rejection: ${event.reason}`,
          filename: 'promise',
          lineno: 0,
          colno: 0,
          timestamp: performance.now()
        });
        this.metrics.jsErrors = this.jsErrors;
      });
    }
  }

  private setupPerformanceObservers(): void {
    if (!('PerformanceObserver' in window)) {
      console.warn('PerformanceObserver not supported');
      return;
    }

    try {
      // Core Web Vitals observers
      this.observeLCP();
      this.observeFID();
      this.observeCLS();
      this.observeFCP();
      this.observeTTFB();

      // Additional performance observers
      if (this.config.enableDetailedTracking) {
        this.observeNavigation();
        this.observeResource();
        this.observePaint();
      }

      if (this.config.enableLongTaskTracking) {
        this.observeLongTasks();
      }

    } catch (error) {
      console.warn('Error setting up performance observers:', error);
    }
  }

  private observeLCP(): void {
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1];

      this.metrics.lcp = lastEntry.startTime;

      // Send immediately for critical metric
      this.sendSingleMetric('lcp', lastEntry.startTime);
    });

    try {
      observer.observe({ entryTypes: ['largest-contentful-paint'] });
      this.observers.push(observer);
    } catch (e) {
      console.warn('LCP observation not supported');
    }
  }

  private observeFID(): void {
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      for (const entry of entries) {
        const fid = (entry as any).processingStart - entry.startTime;
        this.metrics.fid = fid;

        // Send immediately for critical metric
        this.sendSingleMetric('fid', fid);
      }
    });

    try {
      observer.observe({ entryTypes: ['first-input'] });
      this.observers.push(observer);
    } catch (e) {
      console.warn('FID observation not supported');
    }
  }

  private observeCLS(): void {
    let clsValue = 0;

    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (!(entry as any).hadRecentInput) {
          clsValue += (entry as any).value;
          this.metrics.cls = clsValue;
        }
      }
    });

    try {
      observer.observe({ entryTypes: ['layout-shift'] });
      this.observers.push(observer);
    } catch (e) {
      console.warn('CLS observation not supported');
    }
  }

  private observeFCP(): void {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.name === 'first-contentful-paint') {
          this.metrics.fcp = entry.startTime;
        }
      }
    });

    try {
      observer.observe({ entryTypes: ['paint'] });
      this.observers.push(observer);
    } catch (e) {
      console.warn('FCP observation not supported');
    }
  }

  private observeTTFB(): void {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'navigation') {
          const navEntry = entry as PerformanceNavigationTiming;
          this.metrics.ttfb = navEntry.responseStart - navEntry.requestStart;
        }
      }
    });

    try {
      observer.observe({ entryTypes: ['navigation'] });
      this.observers.push(observer);
    } catch (e) {
      console.warn('TTFB observation not supported');
    }
  }

  private observeNavigation(): void {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        const navEntry = entry as PerformanceNavigationTiming;

        this.metrics.domContentLoaded = navEntry.domContentLoadedEventEnd - navEntry.navigationStart;
        this.metrics.windowLoaded = navEntry.loadEventEnd - navEntry.navigationStart;
      }
    });

    try {
      observer.observe({ entryTypes: ['navigation'] });
      this.observers.push(observer);
    } catch (e) {
      console.warn('Navigation observation not supported');
    }
  }

  private observeResource(): void {
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();

      let totalResourceTime = 0;
      let imageLoadTime = 0;

      for (const entry of entries) {
        const resourceEntry = entry as PerformanceResourceTiming;
        const loadTime = resourceEntry.responseEnd - resourceEntry.startTime;
        totalResourceTime += loadTime;

        // Track image loading separately
        if (resourceEntry.initiatorType === 'img') {
          imageLoadTime = Math.max(imageLoadTime, loadTime);
        }
      }

      this.metrics.resourceLoadTime = totalResourceTime;
      this.metrics.imageLoadTime = imageLoadTime;
    });

    try {
      observer.observe({ entryTypes: ['resource'] });
      this.observers.push(observer);
    } catch (e) {
      console.warn('Resource observation not supported');
    }
  }

  private observePaint(): void {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.name === 'first-paint') {
          this.metrics.firstPaint = entry.startTime;
        }
      }
    });

    try {
      observer.observe({ entryTypes: ['paint'] });
      this.observers.push(observer);
    } catch (e) {
      console.warn('Paint observation not supported');
    }
  }

  private observeLongTasks(): void {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        this.longTasks.push({
          duration: entry.duration,
          startTime: entry.startTime
        });
      }
      this.metrics.longTasks = this.longTasks;
    });

    try {
      observer.observe({ entryTypes: ['longtask'] });
      this.observers.push(observer);
    } catch (e) {
      console.warn('Long task observation not supported');
    }
  }

  // Custom business metric tracking
  public trackSearchTime(searchTime: number): void {
    this.metrics.searchTime = searchTime;
  }

  public trackPropertyViewTime(viewTime: number): void {
    this.metrics.propertyViewTime = viewTime;
  }

  // Memory tracking
  private updateMemoryUsage(): void {
    if (!this.config.enableMemoryTracking) return;

    if ('memory' in performance) {
      const memory = (performance as any).memory;
      this.metrics.memoryUsage = {
        used: memory.usedJSHeapSize,
        total: memory.totalJSHeapSize,
        limit: memory.jsHeapSizeLimit
      };
    }
  }

  private recordTimeOnPage(): void {
    this.metrics.timeOnPage = performance.now() - this.startTime;
  }

  private async sendSingleMetric(name: string, value: number): Promise<void> {
    const payload = {
      timestamp: new Date().toISOString(),
      session_id: this.sessionId,
      page_url: window.location.href,
      [name]: value,
      device_type: this.metrics.deviceType,
      connection_type: this.metrics.connectionType,
      user_agent: this.metrics.userAgent
    };

    try {
      await fetch(this.config.apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
    } catch (error) {
      console.warn('Failed to send single metric:', error);
      // Add to pending queue for retry
      this.pendingMetrics.push(payload);
    }
  }

  private async sendMetrics(): Promise<void> {
    if (!this.isRecording) return;

    this.recordTimeOnPage();
    this.updateMemoryUsage();

    const payload = {
      ...this.metrics,
      timestamp: new Date().toISOString()
    };

    try {
      await fetch(this.config.apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
        keepalive: true // Important for page unload
      });

      console.log('📊 RUM metrics sent successfully');

      // Send any pending metrics
      if (this.pendingMetrics.length > 0) {
        for (const pending of this.pendingMetrics) {
          await fetch(this.config.apiEndpoint, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(pending),
          });
        }
        this.pendingMetrics = [];
      }

    } catch (error) {
      console.warn('Failed to send RUM metrics:', error);
      // Store for retry
      this.pendingMetrics.push(payload);
    }
  }

  private startPeriodicSending(): void {
    this.sendInterval = window.setInterval(() => {
      this.sendMetrics();
    }, this.config.sendInterval);
  }

  private throttle(func: Function, delay: number): Function {
    let timeoutId: number | null = null;
    let lastExecTime = 0;

    return function (this: any, ...args: any[]) {
      const currentTime = Date.now();

      if (currentTime - lastExecTime > delay) {
        func.apply(this, args);
        lastExecTime = currentTime;
      } else {
        if (timeoutId) clearTimeout(timeoutId);
        timeoutId = window.setTimeout(() => {
          func.apply(this, args);
          lastExecTime = Date.now();
        }, delay - (currentTime - lastExecTime));
      }
    };
  }

  // Public API
  public stop(): void {
    this.isRecording = false;

    // Send final metrics
    this.sendMetrics();

    // Clear interval
    if (this.sendInterval) {
      clearInterval(this.sendInterval);
      this.sendInterval = null;
    }

    // Disconnect observers
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];

    console.log('🛑 RUM Monitoring stopped');
  }

  public getSessionId(): string {
    return this.sessionId;
  }

  public getCurrentMetrics(): RUMMetric {
    this.recordTimeOnPage();
    this.updateMemoryUsage();
    return { ...this.metrics };
  }

  public forceSync(): void {
    this.sendMetrics();
  }
}

// Export class and create singleton instance
export { RealUserMonitoring, type RUMMetric, type WebVitalsMetric };

// Auto-initialize if in browser environment
let globalRUM: RealUserMonitoring | null = null;

if (typeof window !== 'undefined') {
  // Wait for page to be interactive
  const initRUM = () => {
    if (!globalRUM) {
      globalRUM = new RealUserMonitoring({
        enableDetailedTracking: true,
        enableLongTaskTracking: true,
        enableMemoryTracking: true,
        enableErrorTracking: true,
      });

      // Make available globally for debugging
      (window as any).__RUM__ = globalRUM;
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initRUM);
  } else {
    initRUM();
  }
}

export default globalRUM;