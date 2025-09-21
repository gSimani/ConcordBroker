/**
 * Advanced Resource Preloading System
 * Intelligent preloading of critical resources for optimal performance
 */

interface PreloadOptions {
  priority?: 'high' | 'medium' | 'low';
  timeout?: number;
  retry?: number;
  preloadIf?: () => boolean;
}

interface PreloadResult {
  success: boolean;
  error?: Error;
  loadTime: number;
  fromCache: boolean;
}

interface RoutePreloadConfig {
  route: string;
  resources: {
    scripts?: string[];
    styles?: string[];
    images?: string[];
    data?: string[];
    fonts?: string[];
  };
  condition?: () => boolean;
}

class ResourcePreloader {
  private preloadCache = new Map<string, Promise<PreloadResult>>();
  private prefetchCache = new Map<string, boolean>();
  private performanceMetrics = {
    totalPreloads: 0,
    successfulPreloads: 0,
    cacheHits: 0,
    avgLoadTime: 0,
  };

  // Preload JavaScript modules
  async preloadScript(url: string, options: PreloadOptions = {}): Promise<PreloadResult> {
    const cacheKey = `script:${url}`;

    if (this.preloadCache.has(cacheKey)) {
      this.performanceMetrics.cacheHits++;
      return this.preloadCache.get(cacheKey)!;
    }

    const startTime = performance.now();
    const promise = this.loadScript(url, options);
    this.preloadCache.set(cacheKey, promise);

    const result = await promise;
    this.updateMetrics(result.loadTime, result.success);

    return result;
  }

  private async loadScript(url: string, options: PreloadOptions): Promise<PreloadResult> {
    return new Promise((resolve) => {
      const startTime = performance.now();
      const link = document.createElement('link');

      link.rel = 'modulepreload';
      link.href = url;
      if (options.priority === 'high') {
        link.setAttribute('fetchpriority', 'high');
      }

      link.onload = () => {
        const loadTime = performance.now() - startTime;
        resolve({
          success: true,
          loadTime,
          fromCache: false,
        });
      };

      link.onerror = () => {
        const loadTime = performance.now() - startTime;
        resolve({
          success: false,
          error: new Error(`Failed to preload script: ${url}`),
          loadTime,
          fromCache: false,
        });
      };

      // Set timeout
      if (options.timeout) {
        setTimeout(() => {
          link.remove();
          resolve({
            success: false,
            error: new Error(`Preload timeout: ${url}`),
            loadTime: performance.now() - startTime,
            fromCache: false,
          });
        }, options.timeout);
      }

      document.head.appendChild(link);
    });
  }

  // Preload CSS stylesheets
  async preloadStyle(url: string, options: PreloadOptions = {}): Promise<PreloadResult> {
    const cacheKey = `style:${url}`;

    if (this.preloadCache.has(cacheKey)) {
      this.performanceMetrics.cacheHits++;
      return this.preloadCache.get(cacheKey)!;
    }

    const startTime = performance.now();
    const promise = this.loadStyle(url, options);
    this.preloadCache.set(cacheKey, promise);

    const result = await promise;
    this.updateMetrics(result.loadTime, result.success);

    return result;
  }

  private async loadStyle(url: string, options: PreloadOptions): Promise<PreloadResult> {
    return new Promise((resolve) => {
      const startTime = performance.now();
      const link = document.createElement('link');

      link.rel = 'preload';
      link.as = 'style';
      link.href = url;

      if (options.priority === 'high') {
        link.setAttribute('fetchpriority', 'high');
      }

      link.onload = () => {
        const loadTime = performance.now() - startTime;
        // Apply the stylesheet
        const styleLink = document.createElement('link');
        styleLink.rel = 'stylesheet';
        styleLink.href = url;
        document.head.appendChild(styleLink);

        resolve({
          success: true,
          loadTime,
          fromCache: false,
        });
      };

      link.onerror = () => {
        resolve({
          success: false,
          error: new Error(`Failed to preload style: ${url}`),
          loadTime: performance.now() - startTime,
          fromCache: false,
        });
      };

      document.head.appendChild(link);
    });
  }

  // Preload images with modern format support
  async preloadImage(url: string, options: PreloadOptions = {}): Promise<PreloadResult> {
    const cacheKey = `image:${url}`;

    if (this.preloadCache.has(cacheKey)) {
      this.performanceMetrics.cacheHits++;
      return this.preloadCache.get(cacheKey)!;
    }

    const startTime = performance.now();
    const promise = this.loadImage(url, options);
    this.preloadCache.set(cacheKey, promise);

    const result = await promise;
    this.updateMetrics(result.loadTime, result.success);

    return result;
  }

  private async loadImage(url: string, options: PreloadOptions): Promise<PreloadResult> {
    return new Promise((resolve) => {
      const startTime = performance.now();
      const img = new Image();

      // Set modern image attributes
      img.loading = 'eager';
      img.decoding = 'sync';

      if (options.priority === 'high') {
        img.fetchPriority = 'high';
      }

      img.onload = () => {
        resolve({
          success: true,
          loadTime: performance.now() - startTime,
          fromCache: false,
        });
      };

      img.onerror = () => {
        resolve({
          success: false,
          error: new Error(`Failed to preload image: ${url}`),
          loadTime: performance.now() - startTime,
          fromCache: false,
        });
      };

      img.src = url;
    });
  }

  // Preload API data
  async preloadData(url: string, options: PreloadOptions = {}): Promise<PreloadResult> {
    const cacheKey = `data:${url}`;

    if (this.preloadCache.has(cacheKey)) {
      this.performanceMetrics.cacheHits++;
      return this.preloadCache.get(cacheKey)!;
    }

    const startTime = performance.now();
    const promise = this.loadData(url, options);
    this.preloadCache.set(cacheKey, promise);

    const result = await promise;
    this.updateMetrics(result.loadTime, result.success);

    return result;
  }

  private async loadData(url: string, options: PreloadOptions): Promise<PreloadResult> {
    const startTime = performance.now();

    try {
      const controller = new AbortController();

      if (options.timeout) {
        setTimeout(() => controller.abort(), options.timeout);
      }

      const response = await fetch(url, {
        signal: controller.signal,
        priority: options.priority === 'high' ? 'high' : 'auto',
      } as RequestInit);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // Cache the response
      const data = await response.json();

      // Store in cache if it has React Query
      if (window.__REACT_QUERY_CACHE__) {
        window.__REACT_QUERY_CACHE__.set(url, data);
      }

      return {
        success: true,
        loadTime: performance.now() - startTime,
        fromCache: false,
      };
    } catch (error) {
      return {
        success: false,
        error: error as Error,
        loadTime: performance.now() - startTime,
        fromCache: false,
      };
    }
  }

  // Preload fonts
  async preloadFont(url: string, options: PreloadOptions = {}): Promise<PreloadResult> {
    const cacheKey = `font:${url}`;

    if (this.preloadCache.has(cacheKey)) {
      this.performanceMetrics.cacheHits++;
      return this.preloadCache.get(cacheKey)!;
    }

    const startTime = performance.now();
    const promise = this.loadFont(url, options);
    this.preloadCache.set(cacheKey, promise);

    const result = await promise;
    this.updateMetrics(result.loadTime, result.success);

    return result;
  }

  private async loadFont(url: string, options: PreloadOptions): Promise<PreloadResult> {
    return new Promise((resolve) => {
      const startTime = performance.now();
      const link = document.createElement('link');

      link.rel = 'preload';
      link.as = 'font';
      link.href = url;
      link.crossOrigin = 'anonymous';

      if (options.priority === 'high') {
        link.setAttribute('fetchpriority', 'high');
      }

      link.onload = () => {
        resolve({
          success: true,
          loadTime: performance.now() - startTime,
          fromCache: false,
        });
      };

      link.onerror = () => {
        resolve({
          success: false,
          error: new Error(`Failed to preload font: ${url}`),
          loadTime: performance.now() - startTime,
          fromCache: false,
        });
      };

      document.head.appendChild(link);
    });
  }

  // Batch preload multiple resources
  async preloadResources(resources: {
    scripts?: string[];
    styles?: string[];
    images?: string[];
    data?: string[];
    fonts?: string[];
  }, options: PreloadOptions = {}): Promise<PreloadResult[]> {
    const promises: Promise<PreloadResult>[] = [];

    // Preload in order of priority: fonts, styles, scripts, data, images
    if (resources.fonts) {
      resources.fonts.forEach(url => {
        promises.push(this.preloadFont(url, { ...options, priority: 'high' }));
      });
    }

    if (resources.styles) {
      resources.styles.forEach(url => {
        promises.push(this.preloadStyle(url, { ...options, priority: 'high' }));
      });
    }

    if (resources.scripts) {
      resources.scripts.forEach(url => {
        promises.push(this.preloadScript(url, options));
      });
    }

    if (resources.data) {
      resources.data.forEach(url => {
        promises.push(this.preloadData(url, options));
      });
    }

    if (resources.images) {
      resources.images.forEach(url => {
        promises.push(this.preloadImage(url, { ...options, priority: 'low' }));
      });
    }

    return Promise.all(promises);
  }

  // Route-based preloading
  async preloadRoute(routeConfig: RoutePreloadConfig): Promise<PreloadResult[]> {
    if (routeConfig.condition && !routeConfig.condition()) {
      return [];
    }

    console.log(`[Preloader] Preloading resources for route: ${routeConfig.route}`);

    return this.preloadResources(routeConfig.resources, {
      priority: 'medium',
      timeout: 5000,
    });
  }

  // Intelligent prefetching based on user behavior
  async prefetchOnHover(element: HTMLElement, resources: string[]): Promise<void> {
    const handleMouseEnter = () => {
      resources.forEach(async (url) => {
        if (!this.prefetchCache.has(url)) {
          this.prefetchCache.set(url, true);
          await this.preloadScript(url, { priority: 'low', timeout: 3000 });
        }
      });
    };

    element.addEventListener('mouseenter', handleMouseEnter, { once: true });
  }

  // Preload based on viewport intersection
  async prefetchOnVisible(element: HTMLElement, resources: string[]): Promise<void> {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(async (entry) => {
          if (entry.isIntersecting) {
            resources.forEach(async (url) => {
              if (!this.prefetchCache.has(url)) {
                this.prefetchCache.set(url, true);
                await this.preloadScript(url, { priority: 'low' });
              }
            });
            observer.disconnect();
          }
        });
      },
      { threshold: 0.1 }
    );

    observer.observe(element);
  }

  // Network-aware preloading
  shouldPreload(): boolean {
    const connection = (navigator as any).connection;

    if (!connection) return true; // Default to preload if no network info

    // Don't preload on slow connections
    if (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g') {
      return false;
    }

    // Don't preload if user has data saver enabled
    if (connection.saveData) {
      return false;
    }

    return true;
  }

  // Memory-aware preloading
  shouldPreloadMemory(): boolean {
    const memory = (performance as any).memory;

    if (!memory) return true; // Default to preload if no memory info

    // Don't preload if memory usage is high
    const memoryUsageRatio = memory.usedJSHeapSize / memory.jsHeapSizeLimit;

    return memoryUsageRatio < 0.8; // Only preload if less than 80% memory used
  }

  // Get performance metrics
  getMetrics() {
    return {
      ...this.performanceMetrics,
      cacheSize: this.preloadCache.size,
      cacheHitRate: this.performanceMetrics.cacheHits / this.performanceMetrics.totalPreloads,
    };
  }

  // Clear cache
  clearCache(): void {
    this.preloadCache.clear();
    this.prefetchCache.clear();
  }

  private updateMetrics(loadTime: number, success: boolean): void {
    this.performanceMetrics.totalPreloads++;

    if (success) {
      this.performanceMetrics.successfulPreloads++;

      const currentAvg = this.performanceMetrics.avgLoadTime;
      const count = this.performanceMetrics.successfulPreloads;
      this.performanceMetrics.avgLoadTime = ((currentAvg * (count - 1)) + loadTime) / count;
    }
  }
}

// Singleton instance
export const preloader = new ResourcePreloader();

// Route-based preloading configurations
export const routePreloadConfigs: RoutePreloadConfig[] = [
  {
    route: '/properties',
    resources: {
      scripts: [
        '/src/pages/properties/PropertySearch.tsx',
        '/src/components/property/MiniPropertyCard.tsx',
      ],
      data: [
        '/api/counties',
        '/api/property-types',
      ],
      images: [
        '/assets/icons/property-placeholder.svg',
      ],
    },
    condition: () => preloader.shouldPreload(),
  },
  {
    route: '/property/:id',
    resources: {
      scripts: [
        '/src/pages/property/EnhancedPropertyProfile.tsx',
        '/src/components/property/PropertyMap.tsx',
      ],
      styles: [
        '/src/styles/elegant-property.css',
      ],
    },
    condition: () => preloader.shouldPreload() && preloader.shouldPreloadMemory(),
  },
  {
    route: '/admin',
    resources: {
      scripts: [
        '/src/pages/admin/dashboard.tsx',
        '/src/components/performance/PerformanceMonitor.tsx',
      ],
    },
    condition: () => false, // Only preload admin for authenticated users
  },
];

// React hook for component-level preloading
export function usePreloader() {
  const preloadRoute = async (route: string) => {
    const config = routePreloadConfigs.find(c => c.route === route);
    if (config) {
      return preloader.preloadRoute(config);
    }
    return [];
  };

  const preloadResources = async (urls: string[], type: 'script' | 'style' | 'image' | 'data' = 'script') => {
    const promises = urls.map(url => {
      switch (type) {
        case 'script':
          return preloader.preloadScript(url);
        case 'style':
          return preloader.preloadStyle(url);
        case 'image':
          return preloader.preloadImage(url);
        case 'data':
          return preloader.preloadData(url);
        default:
          return preloader.preloadScript(url);
      }
    });

    return Promise.all(promises);
  };

  return {
    preloadRoute,
    preloadResources,
    metrics: preloader.getMetrics(),
  };
}

// Initialize critical resource preloading
export function initializeCriticalPreloading() {
  // Preload critical fonts
  preloader.preloadFont('https://fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hiA.woff2', {
    priority: 'high',
  });

  // Preload critical API endpoints
  if (preloader.shouldPreload()) {
    preloader.preloadData('/api/config', { priority: 'high' });
  }

  console.log('[Preloader] Critical resources preloading initialized');
}

export default preloader;