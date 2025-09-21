/**
 * Performance Monitoring Dashboard
 * Real-time performance metrics and optimization insights
 */

import React, { useState, useEffect, useCallback, memo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Activity,
  Clock,
  Database,
  Gauge,
  Network,
  Zap,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Download,
  Eye,
  Server,
} from 'lucide-react';

interface PerformanceMetrics {
  // Core Web Vitals
  lcp: number; // Largest Contentful Paint
  fid: number; // First Input Delay
  cls: number; // Cumulative Layout Shift
  fcp: number; // First Contentful Paint
  ttfb: number; // Time to First Byte

  // Custom metrics
  searchResponseTime: number;
  cacheHitRate: number;
  errorRate: number;
  totalRequests: number;
  bundleSize: number;
  imageOptimization: number;

  // Network
  networkSpeed: 'slow-2g' | 'slow-3g' | '3g' | '4g' | '5g' | 'unknown';
  isOnline: boolean;

  // Memory
  usedJSHeapSize: number;
  totalJSHeapSize: number;
  jsHeapSizeLimit: number;
}

interface ComponentMetrics {
  name: string;
  renderCount: number;
  avgRenderTime: number;
  lastRenderTime: number;
  props: Record<string, any>;
  isOptimized: boolean;
}

interface ServiceWorkerMetrics {
  isRegistered: boolean;
  isActive: boolean;
  cacheSize: number;
  cacheHits: number;
  cacheMisses: number;
  version: string;
}

export const PerformanceMonitor = memo(function PerformanceMonitor() {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [componentMetrics, setComponentMetrics] = useState<ComponentMetrics[]>([]);
  const [swMetrics, setSwMetrics] = useState<ServiceWorkerMetrics | null>(null);
  const [isCollecting, setIsCollecting] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Collect Core Web Vitals
  const collectCoreWebVitals = useCallback(() => {
    return new Promise<Partial<PerformanceMetrics>>((resolve) => {
      const metrics: Partial<PerformanceMetrics> = {};

      // Use Performance Observer API for accurate measurements
      if (typeof PerformanceObserver !== 'undefined') {
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            switch (entry.entryType) {
              case 'largest-contentful-paint':
                metrics.lcp = entry.startTime;
                break;
              case 'first-input':
                metrics.fid = (entry as any).processingStart - entry.startTime;
                break;
              case 'layout-shift':
                if (!(entry as any).hadRecentInput) {
                  metrics.cls = (metrics.cls || 0) + (entry as any).value;
                }
                break;
              case 'paint':
                if (entry.name === 'first-contentful-paint') {
                  metrics.fcp = entry.startTime;
                }
                break;
              case 'navigation':
                metrics.ttfb = (entry as any).responseStart;
                break;
            }
          }
        });

        try {
          observer.observe({ entryTypes: ['largest-contentful-paint', 'first-input', 'layout-shift', 'paint', 'navigation'] });

          // Collect what we can immediately
          setTimeout(() => {
            observer.disconnect();
            resolve(metrics);
          }, 1000);
        } catch (error) {
          console.warn('Performance Observer not fully supported:', error);
          resolve(metrics);
        }
      } else {
        // Fallback to performance.timing
        const timing = performance.timing;
        metrics.ttfb = timing.responseStart - timing.navigationStart;
        metrics.fcp = timing.loadEventEnd - timing.navigationStart;
        resolve(metrics);
      }
    });
  }, []);

  // Collect custom application metrics
  const collectAppMetrics = useCallback(async () => {
    const metrics: Partial<PerformanceMetrics> = {};

    // Memory usage
    if ((performance as any).memory) {
      const memory = (performance as any).memory;
      metrics.usedJSHeapSize = memory.usedJSHeapSize;
      metrics.totalJSHeapSize = memory.totalJSHeapSize;
      metrics.jsHeapSizeLimit = memory.jsHeapSizeLimit;
    }

    // Network information
    const connection = (navigator as any).connection;
    if (connection) {
      const effectiveType = connection.effectiveType;
      metrics.networkSpeed = effectiveType;
    }
    metrics.isOnline = navigator.onLine;

    // Cache metrics from React Query
    try {
      const cacheData = localStorage.getItem('concordbroker-query-cache');
      if (cacheData) {
        const cache = JSON.parse(cacheData);
        const queries = cache.clientState?.queries || [];
        const hitRate = queries.filter((q: any) => q.state?.data).length / queries.length;
        metrics.cacheHitRate = hitRate * 100;
        metrics.totalRequests = queries.length;
      }
    } catch (error) {
      metrics.cacheHitRate = 0;
      metrics.totalRequests = 0;
    }

    // Error rate (from console errors)
    const errorCount = parseInt(sessionStorage.getItem('performance-error-count') || '0');
    metrics.errorRate = (errorCount / metrics.totalRequests) * 100;

    return metrics;
  }, []);

  // Collect Service Worker metrics
  const collectServiceWorkerMetrics = useCallback(async () => {
    if (!('serviceWorker' in navigator)) {
      return null;
    }

    const registration = await navigator.serviceWorker.getRegistration();
    if (!registration) {
      return null;
    }

    return new Promise<ServiceWorkerMetrics>((resolve) => {
      const channel = new MessageChannel();

      channel.port1.onmessage = (event) => {
        const { type, size } = event.data;
        if (type === 'CACHE_SIZE') {
          resolve({
            isRegistered: true,
            isActive: registration.active !== null,
            cacheSize: size,
            cacheHits: 0, // Would need to be tracked in SW
            cacheMisses: 0,
            version: 'v1.2.0',
          });
        }
      };

      registration.active?.postMessage(
        { type: 'GET_CACHE_SIZE' },
        [channel.port2]
      );

      // Timeout fallback
      setTimeout(() => {
        resolve({
          isRegistered: true,
          isActive: registration.active !== null,
          cacheSize: 0,
          cacheHits: 0,
          cacheMisses: 0,
          version: 'v1.2.0',
        });
      }, 1000);
    });
  }, []);

  // Analyze bundle size
  const analyzeBundleSize = useCallback(() => {
    const scripts = Array.from(document.querySelectorAll('script[src]'));
    const styles = Array.from(document.querySelectorAll('link[rel="stylesheet"]'));

    let totalSize = 0;

    // Estimate from Resource Timing API
    const resources = performance.getEntriesByType('resource');
    for (const resource of resources) {
      if (resource.name.includes('.js') || resource.name.includes('.css')) {
        totalSize += (resource as any).transferSize || 0;
      }
    }

    return totalSize;
  }, []);

  // Collect all metrics
  const collectAllMetrics = useCallback(async () => {
    setIsCollecting(true);

    try {
      const [coreVitals, appMetrics, swMetrics] = await Promise.all([
        collectCoreWebVitals(),
        collectAppMetrics(),
        collectServiceWorkerMetrics(),
      ]);

      const bundleSize = analyzeBundleSize();

      const combinedMetrics: PerformanceMetrics = {
        // Defaults
        lcp: 0,
        fid: 0,
        cls: 0,
        fcp: 0,
        ttfb: 0,
        searchResponseTime: 0,
        cacheHitRate: 0,
        errorRate: 0,
        totalRequests: 0,
        bundleSize,
        imageOptimization: 85, // Assume good optimization
        networkSpeed: 'unknown',
        isOnline: true,
        usedJSHeapSize: 0,
        totalJSHeapSize: 0,
        jsHeapSizeLimit: 0,
        // Merge collected metrics
        ...coreVitals,
        ...appMetrics,
      };

      setMetrics(combinedMetrics);
      setSwMetrics(swMetrics);
    } catch (error) {
      console.error('Failed to collect performance metrics:', error);
    } finally {
      setIsCollecting(false);
    }
  }, [collectCoreWebVitals, collectAppMetrics, collectServiceWorkerMetrics, analyzeBundleSize]);

  // Auto-refresh metrics
  useEffect(() => {
    collectAllMetrics();

    if (autoRefresh) {
      const interval = setInterval(collectAllMetrics, 5000); // Every 5 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh, collectAllMetrics]);

  // Track console errors
  useEffect(() => {
    const originalError = console.error;
    console.error = (...args) => {
      const count = parseInt(sessionStorage.getItem('performance-error-count') || '0');
      sessionStorage.setItem('performance-error-count', (count + 1).toString());
      originalError.apply(console, args);
    };

    return () => {
      console.error = originalError;
    };
  }, []);

  // Performance score calculation
  const calculateScore = useCallback((metrics: PerformanceMetrics) => {
    let score = 100;

    // Core Web Vitals scoring
    if (metrics.lcp > 2500) score -= 20;
    else if (metrics.lcp > 1200) score -= 10;

    if (metrics.fid > 100) score -= 20;
    else if (metrics.fid > 50) score -= 10;

    if (metrics.cls > 0.25) score -= 20;
    else if (metrics.cls > 0.1) score -= 10;

    if (metrics.fcp > 1800) score -= 15;
    else if (metrics.fcp > 900) score -= 8;

    if (metrics.ttfb > 800) score -= 15;
    else if (metrics.ttfb > 400) score -= 8;

    // Application metrics
    if (metrics.cacheHitRate < 70) score -= 10;
    if (metrics.errorRate > 5) score -= 15;
    if (metrics.bundleSize > 1024 * 1024) score -= 10; // 1MB

    return Math.max(0, Math.round(score));
  }, []);

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600 bg-green-50';
    if (score >= 70) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatTime = (ms: number) => {
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  if (!metrics) {
    return (
      <Card className="w-full">
        <CardContent className="flex items-center justify-center h-48">
          <div className="flex items-center gap-2 text-gray-500">
            <RefreshCw className="w-4 h-4 animate-spin" />
            Collecting performance metrics...
          </div>
        </CardContent>
      </Card>
    );
  }

  const score = calculateScore(metrics);

  return (
    <div className="space-y-4">
      {/* Performance Score Overview */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Gauge className="w-5 h-5" />
            Performance Score
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={collectAllMetrics}
              disabled={isCollecting}
            >
              <RefreshCw className={`w-4 h-4 ${isCollecting ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button
              size="sm"
              variant={autoRefresh ? 'default' : 'outline'}
              onClick={() => setAutoRefresh(!autoRefresh)}
            >
              <Activity className="w-4 h-4" />
              Auto
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div className={`text-4xl font-bold px-4 py-2 rounded-lg ${getScoreColor(score)}`}>
              {score}
            </div>
            <div className="flex-1">
              <div className="text-sm text-gray-600 mb-1">Overall Performance</div>
              <div className="text-lg font-semibold">
                {score >= 90 ? 'Excellent' : score >= 70 ? 'Good' : 'Needs Improvement'}
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-600">Network</div>
              <Badge variant={metrics.isOnline ? 'default' : 'destructive'}>
                {metrics.isOnline ? 'Online' : 'Offline'}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Metrics */}
      <Tabs defaultValue="vitals" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="vitals">Core Web Vitals</TabsTrigger>
          <TabsTrigger value="app">Application</TabsTrigger>
          <TabsTrigger value="caching">Caching</TabsTrigger>
          <TabsTrigger value="resources">Resources</TabsTrigger>
        </TabsList>

        <TabsContent value="vitals" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* LCP */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Largest Contentful Paint
                </CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatTime(metrics.lcp)}</div>
                <p className="text-xs text-muted-foreground">
                  {metrics.lcp <= 1200 ? 'Good' : metrics.lcp <= 2500 ? 'Needs Improvement' : 'Poor'}
                </p>
              </CardContent>
            </Card>

            {/* FID */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  First Input Delay
                </CardTitle>
                <Zap className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatTime(metrics.fid)}</div>
                <p className="text-xs text-muted-foreground">
                  {metrics.fid <= 50 ? 'Good' : metrics.fid <= 100 ? 'Needs Improvement' : 'Poor'}
                </p>
              </CardContent>
            </Card>

            {/* CLS */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Cumulative Layout Shift
                </CardTitle>
                <Eye className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.cls.toFixed(3)}</div>
                <p className="text-xs text-muted-foreground">
                  {metrics.cls <= 0.1 ? 'Good' : metrics.cls <= 0.25 ? 'Needs Improvement' : 'Poor'}
                </p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="app" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Search Performance</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm">Response Time</span>
                  <span className="font-medium">{formatTime(metrics.searchResponseTime)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Total Requests</span>
                  <span className="font-medium">{metrics.totalRequests}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Error Rate</span>
                  <span className="font-medium">{metrics.errorRate.toFixed(1)}%</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Memory Usage</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm">Used Heap</span>
                  <span className="font-medium">{formatBytes(metrics.usedJSHeapSize)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Total Heap</span>
                  <span className="font-medium">{formatBytes(metrics.totalJSHeapSize)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Heap Limit</span>
                  <span className="font-medium">{formatBytes(metrics.jsHeapSizeLimit)}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="caching" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Database className="w-4 h-4" />
                  React Query Cache
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm">Hit Rate</span>
                  <span className="font-medium">{metrics.cacheHitRate.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${metrics.cacheHitRate}%` }}
                  />
                </div>
              </CardContent>
            </Card>

            {swMetrics && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Server className="w-4 h-4" />
                    Service Worker
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm">Status</span>
                    <Badge variant={swMetrics.isActive ? 'default' : 'secondary'}>
                      {swMetrics.isActive ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Cache Size</span>
                    <span className="font-medium">{formatBytes(swMetrics.cacheSize)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Version</span>
                    <span className="font-medium">{swMetrics.version}</span>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="resources" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Bundle Analysis</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm">Total Size</span>
                  <span className="font-medium">{formatBytes(metrics.bundleSize)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Optimization</span>
                  <Badge variant={metrics.bundleSize < 1024 * 1024 ? 'default' : 'destructive'}>
                    {metrics.bundleSize < 1024 * 1024 ? 'Good' : 'Large'}
                  </Badge>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Network</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm">Connection</span>
                  <span className="font-medium capitalize">{metrics.networkSpeed}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Status</span>
                  <Badge variant={metrics.isOnline ? 'default' : 'destructive'}>
                    {metrics.isOnline ? 'Online' : 'Offline'}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
});

export default PerformanceMonitor;