/**
 * ConcordBroker Cache Performance Dashboard
 * Real-time monitoring of cache performance across all layers
 * Target: Maintain 80%+ cache hit rate visualization
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Progress } from '../ui/progress';
import { Alert, AlertDescription } from '../ui/alert';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar
} from 'recharts';
import {
  Activity,
  Database,
  Globe,
  Server,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Clock,
  Zap,
  RefreshCw,
  Settings
} from 'lucide-react';

interface CacheMetrics {
  hitRate: number;
  missRate: number;
  totalRequests: number;
  cacheSize: number;
  avgResponseTime: number;
  errors: number;
  timestamp: string;
}

interface LayerMetrics {
  browser: CacheMetrics;
  serviceWorker: CacheMetrics;
  api: CacheMetrics;
  database: CacheMetrics;
}

interface PerformanceData {
  timestamp: string;
  overall_hit_rate: number;
  browser_hit_rate: number;
  api_hit_rate: number;
  db_hit_rate: number;
  response_time: number;
  total_requests: number;
}

interface InvalidationEvent {
  timestamp: string;
  pattern: string;
  trigger: string;
  entries_invalidated: number;
  reason: string;
}

interface CacheRecommendation {
  type: 'warning' | 'info' | 'success';
  title: string;
  description: string;
  action?: string;
}

export const CachePerformanceDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<LayerMetrics | null>(null);
  const [performanceHistory, setPerformanceHistory] = useState<PerformanceData[]>([]);
  const [invalidationEvents, setInvalidationEvents] = useState<InvalidationEvent[]>([]);
  const [recommendations, setRecommendations] = useState<CacheRecommendation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [selectedLayer, setSelectedLayer] = useState<string>('overall');

  // Fetch cache metrics from all layers
  const fetchMetrics = useCallback(async () => {
    try {
      // Browser layer metrics (from unified cache manager)
      const browserResponse = await fetch('/api/cache/browser/metrics');
      const browserMetrics = await browserResponse.json();

      // Service Worker metrics
      const swMetrics = await getServiceWorkerMetrics();

      // API layer metrics
      const apiResponse = await fetch('/api/cache/metrics');
      const apiMetrics = await apiResponse.json();

      // Database layer metrics
      const dbResponse = await fetch('/api/database/cache/metrics');
      const dbMetrics = await dbResponse.json();

      const layerMetrics: LayerMetrics = {
        browser: browserMetrics,
        serviceWorker: swMetrics,
        api: apiMetrics,
        database: dbMetrics
      };

      setMetrics(layerMetrics);

      // Calculate overall performance
      const overallHitRate = calculateOverallHitRate(layerMetrics);
      const performancePoint: PerformanceData = {
        timestamp: new Date().toISOString(),
        overall_hit_rate: overallHitRate,
        browser_hit_rate: browserMetrics.hitRate,
        api_hit_rate: apiMetrics.hitRate,
        db_hit_rate: dbMetrics.hitRate,
        response_time: calculateAvgResponseTime(layerMetrics),
        total_requests: calculateTotalRequests(layerMetrics)
      };

      setPerformanceHistory(prev => [...prev.slice(-29), performancePoint]);

      // Fetch invalidation events
      const invalidationResponse = await fetch('/api/cache/invalidation/events');
      const events = await invalidationResponse.json();
      setInvalidationEvents(events);

      // Generate recommendations
      const newRecommendations = generateRecommendations(layerMetrics, events);
      setRecommendations(newRecommendations);

    } catch (error) {
      console.error('Error fetching cache metrics:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Get Service Worker metrics
  const getServiceWorkerMetrics = async (): Promise<CacheMetrics> => {
    return new Promise((resolve) => {
      if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
        const channel = new MessageChannel();

        channel.port1.onmessage = (event) => {
          if (event.data.type === 'PERFORMANCE_REPORT') {
            const data = event.data.data;
            resolve({
              hitRate: data.hitRate || 0,
              missRate: 100 - (data.hitRate || 0),
              totalRequests: data.totalRequests || 0,
              cacheSize: data.cacheSize || 0,
              avgResponseTime: data.avgResponseTime || 0,
              errors: data.errors || 0,
              timestamp: new Date().toISOString()
            });
          }
        };

        navigator.serviceWorker.controller.postMessage(
          { type: 'GET_PERFORMANCE_REPORT' },
          [channel.port2]
        );
      } else {
        resolve({
          hitRate: 0,
          missRate: 100,
          totalRequests: 0,
          cacheSize: 0,
          avgResponseTime: 0,
          errors: 0,
          timestamp: new Date().toISOString()
        });
      }
    });
  };

  // Calculate overall cache hit rate across all layers
  const calculateOverallHitRate = (layerMetrics: LayerMetrics): number => {
    const layers = [layerMetrics.browser, layerMetrics.serviceWorker, layerMetrics.api, layerMetrics.database];
    const totalRequests = layers.reduce((sum, layer) => sum + layer.totalRequests, 0);

    if (totalRequests === 0) return 0;

    const totalHits = layers.reduce((sum, layer) => sum + (layer.totalRequests * layer.hitRate / 100), 0);
    return (totalHits / totalRequests) * 100;
  };

  const calculateAvgResponseTime = (layerMetrics: LayerMetrics): number => {
    const layers = [layerMetrics.browser, layerMetrics.serviceWorker, layerMetrics.api, layerMetrics.database];
    const avgTime = layers.reduce((sum, layer) => sum + layer.avgResponseTime, 0) / layers.length;
    return avgTime;
  };

  const calculateTotalRequests = (layerMetrics: LayerMetrics): number => {
    return Object.values(layerMetrics).reduce((sum, layer) => sum + layer.totalRequests, 0);
  };

  // Generate performance recommendations
  const generateRecommendations = (
    layerMetrics: LayerMetrics,
    events: InvalidationEvent[]
  ): CacheRecommendation[] => {
    const recommendations: CacheRecommendation[] = [];
    const overallHitRate = calculateOverallHitRate(layerMetrics);

    // Overall performance
    if (overallHitRate < 80) {
      recommendations.push({
        type: 'warning',
        title: 'Cache Hit Rate Below Target',
        description: `Current hit rate: ${overallHitRate.toFixed(1)}%. Target: 80%+`,
        action: 'Increase cache warming and optimize cache strategies'
      });
    } else if (overallHitRate >= 90) {
      recommendations.push({
        type: 'success',
        title: 'Excellent Cache Performance',
        description: `Hit rate: ${overallHitRate.toFixed(1)}%. Performance is optimal.`
      });
    }

    // Layer-specific recommendations
    if (layerMetrics.browser.hitRate < 70) {
      recommendations.push({
        type: 'warning',
        title: 'Browser Cache Underperforming',
        description: 'Consider increasing LocalStorage and IndexedDB usage',
        action: 'Optimize client-side caching strategies'
      });
    }

    if (layerMetrics.database.avgResponseTime > 100) {
      recommendations.push({
        type: 'warning',
        title: 'Slow Database Queries',
        description: `Average response time: ${layerMetrics.database.avgResponseTime.toFixed(1)}ms`,
        action: 'Review query performance and increase database caching'
      });
    }

    // Invalidation frequency
    const recentEvents = events.filter(event =>
      new Date(event.timestamp) > new Date(Date.now() - 60 * 60 * 1000) // Last hour
    );

    if (recentEvents.length > 50) {
      recommendations.push({
        type: 'warning',
        title: 'High Cache Invalidation Frequency',
        description: `${recentEvents.length} invalidations in the last hour`,
        action: 'Review invalidation rules and reduce unnecessary invalidations'
      });
    }

    return recommendations;
  };

  // Cache management actions
  const warmCache = async () => {
    try {
      await fetch('/api/cache/warm', { method: 'POST' });

      // Also warm service worker cache
      if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
        navigator.serviceWorker.controller.postMessage({ type: 'WARM_CACHE' });
      }

      fetchMetrics(); // Refresh metrics
    } catch (error) {
      console.error('Error warming cache:', error);
    }
  };

  const clearCache = async () => {
    try {
      await fetch('/api/cache/clear', { method: 'POST' });

      // Also clear service worker cache
      if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
        navigator.serviceWorker.controller.postMessage({ type: 'CLEAR_CACHE' });
      }

      fetchMetrics(); // Refresh metrics
    } catch (error) {
      console.error('Error clearing cache:', error);
    }
  };

  // Auto-refresh effect
  useEffect(() => {
    fetchMetrics();

    if (autoRefresh) {
      const interval = setInterval(fetchMetrics, 30000); // Every 30 seconds
      return () => clearInterval(interval);
    }
  }, [fetchMetrics, autoRefresh]);

  const formatBytes = (bytes: number): string => {
    const sizes = ['B', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${Math.round(bytes / Math.pow(1024, i) * 100) / 100} ${sizes[i]}`;
  };

  const getHitRateColor = (hitRate: number): string => {
    if (hitRate >= 80) return 'text-green-600';
    if (hitRate >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getHealthStatus = (hitRate: number): { icon: React.ReactNode; label: string; color: string } => {
    if (hitRate >= 80) {
      return { icon: <CheckCircle className="h-5 w-5" />, label: 'Healthy', color: 'text-green-600' };
    }
    if (hitRate >= 60) {
      return { icon: <AlertTriangle className="h-5 w-5" />, label: 'Warning', color: 'text-yellow-600' };
    }
    return { icon: <AlertTriangle className="h-5 w-5" />, label: 'Critical', color: 'text-red-600' };
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading cache metrics...</span>
      </div>
    );
  }

  if (!metrics) {
    return (
      <Alert>
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Unable to load cache metrics. Please check your connection and try again.
        </AlertDescription>
      </Alert>
    );
  }

  const overallHitRate = calculateOverallHitRate(metrics);
  const healthStatus = getHealthStatus(overallHitRate);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold">Cache Performance Dashboard</h2>
          <p className="text-gray-600">Real-time monitoring across all caching layers</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <Activity className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-pulse' : ''}`} />
            {autoRefresh ? 'Auto' : 'Manual'}
          </Button>
          <Button variant="outline" size="sm" onClick={warmCache}>
            <Zap className="h-4 w-4 mr-2" />
            Warm Cache
          </Button>
          <Button variant="outline" size="sm" onClick={clearCache}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Clear Cache
          </Button>
        </div>
      </div>

      {/* Overall Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Overall Hit Rate</p>
                <p className={`text-2xl font-bold ${getHitRateColor(overallHitRate)}`}>
                  {overallHitRate.toFixed(1)}%
                </p>
              </div>
              <div className={healthStatus.color}>
                {healthStatus.icon}
              </div>
            </div>
            <div className="mt-2">
              <Progress value={overallHitRate} className="h-2" />
              <p className="text-xs text-gray-500 mt-1">Target: 80%+</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Requests</p>
                <p className="text-2xl font-bold">{calculateTotalRequests(metrics).toLocaleString()}</p>
              </div>
              <Globe className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg Response Time</p>
                <p className="text-2xl font-bold">{calculateAvgResponseTime(metrics).toFixed(1)}ms</p>
              </div>
              <Clock className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Cache Size</p>
                <p className="text-2xl font-bold">
                  {formatBytes(Object.values(metrics).reduce((sum, layer) => sum + layer.cacheSize, 0))}
                </p>
              </div>
              <Database className="h-8 w-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <TrendingUp className="h-5 w-5 mr-2" />
              Performance Recommendations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recommendations.map((rec, index) => (
                <Alert key={index} className={`border-l-4 ${
                  rec.type === 'success' ? 'border-green-500' :
                  rec.type === 'warning' ? 'border-yellow-500' : 'border-red-500'
                }`}>
                  <AlertDescription>
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium">{rec.title}</p>
                        <p className="text-sm text-gray-600">{rec.description}</p>
                        {rec.action && (
                          <p className="text-sm text-blue-600 mt-1">{rec.action}</p>
                        )}
                      </div>
                      <Badge variant={rec.type === 'success' ? 'default' : 'destructive'}>
                        {rec.type}
                      </Badge>
                    </div>
                  </AlertDescription>
                </Alert>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Detailed Metrics */}
      <Tabs value={selectedLayer} onValueChange={setSelectedLayer} className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overall">Overall</TabsTrigger>
          <TabsTrigger value="browser">Browser</TabsTrigger>
          <TabsTrigger value="serviceWorker">Service Worker</TabsTrigger>
          <TabsTrigger value="api">API</TabsTrigger>
          <TabsTrigger value="database">Database</TabsTrigger>
        </TabsList>

        <TabsContent value="overall" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Performance Trends</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={performanceHistory}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                  />
                  <YAxis domain={[0, 100]} />
                  <Tooltip
                    labelFormatter={(value) => new Date(value).toLocaleString()}
                    formatter={(value: number) => [`${value.toFixed(1)}%`, 'Hit Rate']}
                  />
                  <Line
                    type="monotone"
                    dataKey="overall_hit_rate"
                    stroke="#10b981"
                    strokeWidth={2}
                    name="Overall Hit Rate"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Hit Rate by Layer</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={[
                    { name: 'Browser', hitRate: metrics.browser.hitRate },
                    { name: 'Service Worker', hitRate: metrics.serviceWorker.hitRate },
                    { name: 'API', hitRate: metrics.api.hitRate },
                    { name: 'Database', hitRate: metrics.database.hitRate }
                  ]}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis domain={[0, 100]} />
                    <Tooltip formatter={(value: number) => [`${value.toFixed(1)}%`, 'Hit Rate']} />
                    <Bar dataKey="hitRate" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Cache Size Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Browser', value: metrics.browser.cacheSize },
                        { name: 'Service Worker', value: metrics.serviceWorker.cacheSize },
                        { name: 'API', value: metrics.api.cacheSize },
                        { name: 'Database', value: metrics.database.cacheSize }
                      ]}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    >
                      {[
                        <Cell key="cell-0" fill="#3b82f6" />,
                        <Cell key="cell-1" fill="#10b981" />,
                        <Cell key="cell-2" fill="#f59e0b" />,
                        <Cell key="cell-3" fill="#ef4444" />
                      ]}
                    </Pie>
                    <Tooltip formatter={(value: number) => [formatBytes(value), 'Size']} />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Individual layer tabs would be implemented similarly */}
        {/* ... */}

      </Tabs>

      {/* Recent Invalidation Events */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <RefreshCw className="h-5 w-5 mr-2" />
            Recent Cache Invalidations
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {invalidationEvents.slice(0, 10).map((event, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium">{event.pattern}</p>
                  <p className="text-sm text-gray-600">{event.reason}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">{event.entries_invalidated} entries</p>
                  <p className="text-xs text-gray-500">
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};