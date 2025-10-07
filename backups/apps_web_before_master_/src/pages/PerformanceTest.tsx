import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  usePerformanceMonitor,
  withPerformanceTracking,
  performanceUtils
} from '@/utils/performanceMonitor';
import {
  Activity,
  Clock,
  Database,
  Zap,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Download,
  AlertTriangle,
  CheckCircle2
} from 'lucide-react';

// Test components for performance comparison
const RegularComponent = ({ items }: { items: any[] }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {items.map((item, index) => (
        <div key={index} className="p-4 border rounded-lg">
          <h3 className="font-semibold">{item.title}</h3>
          <p className="text-sm text-gray-600">{item.description}</p>
          <div className="mt-2 text-xs text-gray-500">{item.timestamp}</div>
        </div>
      ))}
    </div>
  );
};

const OptimizedComponent = withPerformanceTracking(
  React.memo(({ items }: { items: any[] }) => {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map((item, index) => (
          <div key={item.id || index} className="p-4 border rounded-lg">
            <h3 className="font-semibold">{item.title}</h3>
            <p className="text-sm text-gray-600">{item.description}</p>
            <div className="mt-2 text-xs text-gray-500">{item.timestamp}</div>
          </div>
        ))}
      </div>
    );
  }),
  'OptimizedComponent'
);

export function PerformanceTest() {
  const {
    metrics,
    trackRender,
    getComponentStats,
    getRecommendations,
    generateReport,
    updateMetrics
  } = usePerformanceMonitor();

  const [testData, setTestData] = useState<any[]>([]);
  const [testMode, setTestMode] = useState<'regular' | 'optimized'>('regular');
  const [testResults, setTestResults] = useState<any[]>([]);
  const [isRunningTest, setIsRunningTest] = useState(false);

  // Generate test data
  const generateTestData = useCallback((count: number) => {
    return Array.from({ length: count }, (_, index) => ({
      id: index,
      title: `Property ${index + 1}`,
      description: `Property description for item ${index + 1}. This is a longer description to simulate real data.`,
      timestamp: new Date(Date.now() - Math.random() * 10000000000).toISOString(),
      value: Math.floor(Math.random() * 1000000) + 100000,
      address: `${Math.floor(Math.random() * 9999)} Main St`,
      city: ['Miami', 'Orlando', 'Tampa', 'Jacksonville'][Math.floor(Math.random() * 4)]
    }));
  }, []);

  // Initialize test data
  useEffect(() => {
    setTestData(generateTestData(100));
  }, [generateTestData]);

  // Run performance comparison test
  const runPerformanceTest = useCallback(async () => {
    setIsRunningTest(true);
    const results: any[] = [];

    try {
      // Test with different data sizes
      const testSizes = [50, 100, 500, 1000];

      for (const size of testSizes) {
        const data = generateTestData(size);

        // Test regular component
        const regularTime = performanceUtils.measureRenderTime(() => {
          setTestData(data);
          setTestMode('regular');
        });

        // Wait for render
        await new Promise(resolve => setTimeout(resolve, 100));

        // Test optimized component
        const optimizedTime = performanceUtils.measureRenderTime(() => {
          setTestData(data);
          setTestMode('optimized');
        });

        // Wait for render
        await new Promise(resolve => setTimeout(resolve, 100));

        results.push({
          size,
          regularTime,
          optimizedTime,
          improvement: ((regularTime - optimizedTime) / regularTime) * 100,
          memoryUsage: metrics.memoryUsage
        });
      }

      setTestResults(results);
    } catch (error) {
      console.error('Performance test failed:', error);
    } finally {
      setIsRunningTest(false);
    }
  }, [generateTestData, metrics.memoryUsage]);

  // Format time for display
  const formatTime = (ms: number) => {
    if (ms < 1) return `${(ms * 1000).toFixed(0)}μs`;
    if (ms < 1000) return `${ms.toFixed(2)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  // Format memory for display
  const formatMemory = (mb: number) => {
    if (mb < 1) return `${(mb * 1024).toFixed(0)}KB`;
    return `${mb.toFixed(2)}MB`;
  };

  // Get performance score
  const getPerformanceScore = () => {
    let score = 100;

    if (metrics.firstContentfulPaint > 1800) score -= 20;
    if (metrics.largestContentfulPaint > 2500) score -= 20;
    if (metrics.memoryUsage > 100) score -= 15;
    if (metrics.cacheHitRate < 70) score -= 15;

    const slowComponents = getComponentStats().filter(stat => stat.renderTime > 16);
    score -= slowComponents.length * 5;

    return Math.max(0, score);
  };

  const performanceScore = getPerformanceScore();

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Performance Testing Dashboard</h1>
              <p className="text-gray-600 mt-1">Monitor and optimize React application performance</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{performanceScore}</div>
                <div className="text-sm text-gray-500">Performance Score</div>
              </div>
              <Button onClick={updateMetrics} size="sm" variant="outline">
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
            </div>
          </div>
        </div>

        {/* Core Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 flex items-center">
                <Clock className="w-4 h-4 mr-2" />
                First Contentful Paint
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatTime(metrics.firstContentfulPaint)}
              </div>
              <Badge
                variant={metrics.firstContentfulPaint < 1800 ? "default" : "destructive"}
                className="mt-2"
              >
                {metrics.firstContentfulPaint < 1800 ? "Good" : "Needs Improvement"}
              </Badge>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 flex items-center">
                <Zap className="w-4 h-4 mr-2" />
                Largest Contentful Paint
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatTime(metrics.largestContentfulPaint)}
              </div>
              <Badge
                variant={metrics.largestContentfulPaint < 2500 ? "default" : "destructive"}
                className="mt-2"
              >
                {metrics.largestContentfulPaint < 2500 ? "Good" : "Poor"}
              </Badge>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 flex items-center">
                <Activity className="w-4 h-4 mr-2" />
                Memory Usage
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatMemory(metrics.memoryUsage)}
              </div>
              <Badge
                variant={metrics.memoryUsage < 50 ? "default" : metrics.memoryUsage < 100 ? "secondary" : "destructive"}
                className="mt-2"
              >
                {metrics.memoryUsage < 50 ? "Excellent" : metrics.memoryUsage < 100 ? "Good" : "High"}
              </Badge>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 flex items-center">
                <Database className="w-4 h-4 mr-2" />
                Cache Hit Rate
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {metrics.cacheHitRate.toFixed(1)}%
              </div>
              <Badge
                variant={metrics.cacheHitRate > 80 ? "default" : metrics.cacheHitRate > 60 ? "secondary" : "destructive"}
                className="mt-2"
              >
                {metrics.cacheHitRate > 80 ? "Excellent" : metrics.cacheHitRate > 60 ? "Good" : "Poor"}
              </Badge>
            </CardContent>
          </Card>
        </div>

        {/* Detailed Analysis */}
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList className="bg-white border">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="components">Components</TabsTrigger>
            <TabsTrigger value="testing">Performance Testing</TabsTrigger>
            <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Performance Overview</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>Performance Score</span>
                        <span>{performanceScore}/100</span>
                      </div>
                      <Progress value={performanceScore} className="h-2" />
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <div className="text-gray-600">Network Requests</div>
                        <div className="font-semibold">{metrics.networkRequests}</div>
                      </div>
                      <div>
                        <div className="text-gray-600">Bundle Size</div>
                        <div className="font-semibold">{metrics.bundleSize.toFixed(1)}KB</div>
                      </div>
                      <div>
                        <div className="text-gray-600">Components</div>
                        <div className="font-semibold">{metrics.componentCount}</div>
                      </div>
                      <div>
                        <div className="text-gray-600">Memory</div>
                        <div className="font-semibold">{formatMemory(metrics.memoryUsage)}</div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Real-time Metrics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>FCP:</span>
                      <span className="font-mono">{formatTime(metrics.firstContentfulPaint)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>LCP:</span>
                      <span className="font-mono">{formatTime(metrics.largestContentfulPaint)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>TTI:</span>
                      <span className="font-mono">{formatTime(metrics.timeToInteractive)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Cache Hit Rate:</span>
                      <span className="font-mono">{metrics.cacheHitRate.toFixed(1)}%</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="components" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Component Performance Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {getComponentStats().slice(0, 10).map((stat, index) => (
                    <div key={stat.componentName} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <div className="font-medium">{stat.componentName}</div>
                        <div className="text-sm text-gray-600">
                          {stat.rerenderCount} renders
                          {stat.propsChanged && <span className="ml-2 text-orange-600">• Props changed</span>}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-mono text-sm">{formatTime(stat.renderTime)}</div>
                        <Badge variant={stat.renderTime > 16 ? "destructive" : "default"} className="text-xs">
                          {stat.renderTime > 16 ? "Slow" : "Fast"}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="testing" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  Performance Testing
                  <Button
                    onClick={runPerformanceTest}
                    disabled={isRunningTest}
                    size="sm"
                  >
                    {isRunningTest ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        Running...
                      </>
                    ) : (
                      'Run Test'
                    )}
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {testResults.length > 0 && (
                  <div className="space-y-4">
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left p-2">Items</th>
                            <th className="text-right p-2">Regular</th>
                            <th className="text-right p-2">Optimized</th>
                            <th className="text-right p-2">Improvement</th>
                            <th className="text-right p-2">Memory</th>
                          </tr>
                        </thead>
                        <tbody>
                          {testResults.map((result, index) => (
                            <tr key={index} className="border-b">
                              <td className="p-2">{result.size} items</td>
                              <td className="p-2 text-right font-mono">{formatTime(result.regularTime)}</td>
                              <td className="p-2 text-right font-mono">{formatTime(result.optimizedTime)}</td>
                              <td className="p-2 text-right">
                                <Badge variant={result.improvement > 0 ? "default" : "destructive"}>
                                  {result.improvement > 0 ? '+' : ''}{result.improvement.toFixed(1)}%
                                </Badge>
                              </td>
                              <td className="p-2 text-right font-mono">{formatMemory(result.memoryUsage)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    <div className="mt-6">
                      <h4 className="font-medium mb-3">Test Preview</h4>
                      <div className="border rounded-lg p-4 bg-gray-50">
                        <div className="mb-2 text-sm text-gray-600">
                          Mode: {testMode} • {testData.length} items
                        </div>
                        {testMode === 'regular' ? (
                          <RegularComponent items={testData.slice(0, 9)} />
                        ) : (
                          <OptimizedComponent items={testData.slice(0, 9)} />
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="recommendations" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Optimization Recommendations</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {getRecommendations().map((recommendation, index) => (
                    <div key={index} className="flex items-start space-x-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
                      <div className="text-sm text-gray-800">{recommendation}</div>
                    </div>
                  ))}

                  {getRecommendations().length === 0 && (
                    <div className="flex items-center space-x-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                      <CheckCircle2 className="w-5 h-5 text-green-600" />
                      <div className="text-sm text-gray-800">
                        No performance issues detected. Your application is well optimized!
                      </div>
                    </div>
                  )}
                </div>

                <div className="mt-6 pt-6 border-t">
                  <Button
                    onClick={() => {
                      const report = generateReport();
                      const blob = new Blob([report], { type: 'text/markdown' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `performance-report-${Date.now()}.md`;
                      a.click();
                      URL.revokeObjectURL(url);
                    }}
                    variant="outline"
                    size="sm"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Download Report
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}