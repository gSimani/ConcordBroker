/**
 * Comprehensive Real-time Performance Monitoring Dashboard
 * Live visualizations across all performance layers
 */

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  Database,
  Globe,
  HardDrive,
  MemoryStick,
  Monitor,
  Network,
  Server,
  TrendingDown,
  TrendingUp,
  Users,
  Wifi,
  Zap,
  Eye,
  Target,
  Gauge,
  Bell,
  BellOff,
  RefreshCw,
  Download,
  Settings,
  Play,
  Pause,
  BarChart3,
  LineChart,
  PieChart,
  Cpu,
  WifiOff
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart as RechartsLineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart as RechartsPieChart,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine
} from 'recharts';

// Types
interface RealTimeMetrics {
  timestamp: number;
  application: ApplicationMetrics;
  infrastructure: InfrastructureMetrics;
  webVitals: WebVitalsMetrics;
  business: BusinessMetrics;
  alerts: AlertMetrics;
}

interface ApplicationMetrics {
  requestsPerMinute: number;
  avgResponseTime: number;
  errorRate: number;
  cacheHitRate: number;
  activeUsers: number;
  databaseLatency: number;
  redisLatency: number;
  responseTimePercentiles: {
    p50: number;
    p95: number;
    p99: number;
  };
}

interface InfrastructureMetrics {
  cpu: number;
  memory: number;
  disk: number;
  network: {
    in: number;
    out: number;
    connections: number;
  };
  database: {
    connections: number;
    maxConnections: number;
    queryTime: number;
  };
  redis: {
    memory: number;
    connections: number;
    opsPerSec: number;
  };
}

interface WebVitalsMetrics {
  lcp: number;
  fid: number;
  cls: number;
  fcp: number;
  ttfb: number;
  score: number;
}

interface BusinessMetrics {
  conversionRate: number;
  searchSuccessRate: number;
  userEngagement: number;
  revenueImpact: number;
  sessionDuration: number;
}

interface AlertMetrics {
  active: number;
  critical: number;
  warning: number;
  resolved24h: number;
  avgResolutionTime: number;
}

interface TimeSeriesData {
  timestamp: number;
  [key: string]: number;
}

export const RealtimeMonitoringDashboard: React.FC = () => {
  // State
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(true);
  const [currentMetrics, setCurrentMetrics] = useState<RealTimeMetrics | null>(null);
  const [timeSeriesData, setTimeSeriesData] = useState<TimeSeriesData[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [selectedTimeRange, setSelectedTimeRange] = useState('1h');
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Refs
  const wsRef = useRef<WebSocket | null>(null);
  const chartDataRef = useRef<Map<string, TimeSeriesData[]>>(new Map());

  // WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/monitoring`;

        wsRef.current = new WebSocket(wsUrl);

        wsRef.current.onopen = () => {
          setIsConnected(true);
          console.log('📡 Connected to monitoring WebSocket');
        };

        wsRef.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        wsRef.current.onclose = () => {
          setIsConnected(false);
          console.log('📡 Monitoring WebSocket disconnected');

          // Attempt to reconnect after 5 seconds
          setTimeout(connectWebSocket, 5000);
        };

        wsRef.current.onerror = (error) => {
          console.error('WebSocket error:', error);
        };

      } catch (error) {
        console.error('Failed to connect to WebSocket:', error);
        setTimeout(connectWebSocket, 5000);
      }
    };

    if (autoRefresh) {
      connectWebSocket();
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [autoRefresh]);

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((data: any) => {
    if (!isRecording) return;

    switch (data.type) {
      case 'metric_update':
        handleMetricUpdate(data);
        break;
      case 'alert':
        handleAlertUpdate(data);
        break;
      case 'dashboard_data':
        handleDashboardData(data);
        break;
    }
  }, [isRecording]);

  const handleMetricUpdate = useCallback((data: any) => {
    const timestamp = Date.now();

    // Update time series data
    setTimeSeriesData(prev => {
      const newData = [...prev, { timestamp, ...data.data }].slice(-1000); // Keep last 1000 points
      return newData;
    });
  }, []);

  const handleAlertUpdate = useCallback((data: any) => {
    setAlerts(prev => [data.alert, ...prev.slice(0, 99)]); // Keep last 100 alerts
  }, []);

  const handleDashboardData = useCallback((data: any) => {
    setCurrentMetrics(data.data);
  }, []);

  // Fetch initial data
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const response = await fetch('/api/monitoring/dashboard');
        const data = await response.json();
        setCurrentMetrics(data);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      }
    };

    fetchDashboardData();

    // Set up periodic fetch if WebSocket is not connected
    const interval = setInterval(() => {
      if (!isConnected && autoRefresh) {
        fetchDashboardData();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [isConnected, autoRefresh]);

  // Chart data processing
  const chartData = useMemo(() => {
    const ranges = {
      '5m': 5 * 60 * 1000,
      '15m': 15 * 60 * 1000,
      '1h': 60 * 60 * 1000,
      '6h': 6 * 60 * 60 * 1000,
      '24h': 24 * 60 * 60 * 1000
    };

    const range = ranges[selectedTimeRange as keyof typeof ranges] || ranges['1h'];
    const cutoffTime = Date.now() - range;

    return timeSeriesData.filter(d => d.timestamp > cutoffTime);
  }, [timeSeriesData, selectedTimeRange]);

  // Status indicators
  const getHealthStatus = (value: number, thresholds: { good: number; warning: number }) => {
    if (value <= thresholds.good) return 'good';
    if (value <= thresholds.warning) return 'warning';
    return 'critical';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good': return 'text-green-600 bg-green-50';
      case 'warning': return 'text-yellow-600 bg-yellow-50';
      case 'critical': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  // Format helpers
  const formatNumber = (num: number, decimals = 1) => {
    if (num >= 1e9) return `${(num / 1e9).toFixed(decimals)}B`;
    if (num >= 1e6) return `${(num / 1e6).toFixed(decimals)}M`;
    if (num >= 1e3) return `${(num / 1e3).toFixed(decimals)}K`;
    return num.toFixed(decimals);
  };

  const formatTime = (ms: number) => {
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const formatPercent = (value: number) => `${value.toFixed(1)}%`;

  if (!currentMetrics) {
    return (
      <Card className="w-full h-96">
        <CardContent className="flex items-center justify-center h-full">
          <div className="flex items-center gap-2 text-gray-500">
            <RefreshCw className="w-6 h-6 animate-spin" />
            Loading monitoring dashboard...
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="w-full space-y-6">
      {/* Header Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-3xl font-bold">Performance Monitoring</h1>
          <Badge variant={isConnected ? 'default' : 'destructive'} className="flex items-center gap-1">
            {isConnected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
            {isConnected ? 'Live' : 'Disconnected'}
          </Badge>
        </div>

        <div className="flex items-center gap-2">
          {/* Time Range Selector */}
          <select
            value={selectedTimeRange}
            onChange={(e) => setSelectedTimeRange(e.target.value)}
            className="px-3 py-1 border rounded-md"
          >
            <option value="5m">5 minutes</option>
            <option value="15m">15 minutes</option>
            <option value="1h">1 hour</option>
            <option value="6h">6 hours</option>
            <option value="24h">24 hours</option>
          </select>

          {/* Control Buttons */}
          <Button
            size="sm"
            variant={isRecording ? 'default' : 'outline'}
            onClick={() => setIsRecording(!isRecording)}
          >
            {isRecording ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            {isRecording ? 'Recording' : 'Paused'}
          </Button>

          <Button
            size="sm"
            variant={autoRefresh ? 'default' : 'outline'}
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin' : ''}`} />
            Auto Refresh
          </Button>

          <Button size="sm" variant="outline">
            <Download className="w-4 h-4" />
            Export
          </Button>
        </div>
      </div>

      {/* Active Alerts Bar */}
      {alerts.length > 0 && (
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertDescription className="flex items-center justify-between">
            <span>
              {currentMetrics.alerts.active} active alerts
              ({currentMetrics.alerts.critical} critical, {currentMetrics.alerts.warning} warning)
            </span>
            <Button size="sm" variant="outline">View All</Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Response Time */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Response Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatTime(currentMetrics.application.avgResponseTime)}
            </div>
            <div className="flex items-center space-x-2 text-xs text-muted-foreground">
              <span>P95: {formatTime(currentMetrics.application.responseTimePercentiles.p95)}</span>
              <span>P99: {formatTime(currentMetrics.application.responseTimePercentiles.p99)}</span>
            </div>
          </CardContent>
        </Card>

        {/* Requests per Minute */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Requests/min</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatNumber(currentMetrics.application.requestsPerMinute)}
            </div>
            <p className="text-xs text-muted-foreground">
              {currentMetrics.application.activeUsers} active users
            </p>
          </CardContent>
        </Card>

        {/* Error Rate */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Error Rate</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatPercent(currentMetrics.application.errorRate)}
            </div>
            <Badge variant={currentMetrics.application.errorRate < 1 ? 'default' : 'destructive'}>
              {currentMetrics.application.errorRate < 1 ? 'Good' : 'High'}
            </Badge>
          </CardContent>
        </Card>

        {/* Cache Hit Rate */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cache Hit Rate</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatPercent(currentMetrics.application.cacheHitRate)}
            </div>
            <Progress value={currentMetrics.application.cacheHitRate} className="mt-2" />
          </CardContent>
        </Card>
      </div>

      {/* Main Dashboard Tabs */}
      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="application">Application</TabsTrigger>
          <TabsTrigger value="infrastructure">Infrastructure</TabsTrigger>
          <TabsTrigger value="web-vitals">Web Vitals</TabsTrigger>
          <TabsTrigger value="business">Business</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Response Time Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Response Time Trend</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RechartsLineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                    />
                    <YAxis />
                    <Tooltip
                      labelFormatter={(value) => new Date(value).toLocaleString()}
                      formatter={(value: number) => [formatTime(value), 'Response Time']}
                    />
                    <Line
                      type="monotone"
                      dataKey="avgResponseTime"
                      stroke="#8884d8"
                      strokeWidth={2}
                      dot={false}
                    />
                    <ReferenceLine y={500} stroke="red" strokeDasharray="5 5" />
                  </RechartsLineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* System Health */}
            <Card>
              <CardHeader>
                <CardTitle>System Health</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Cpu className="w-4 h-4" />
                    <span>CPU Usage</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono">{formatPercent(currentMetrics.infrastructure.cpu)}</span>
                    <Badge className={getStatusColor(getHealthStatus(currentMetrics.infrastructure.cpu, { good: 70, warning: 85 }))}>
                      {getHealthStatus(currentMetrics.infrastructure.cpu, { good: 70, warning: 85 })}
                    </Badge>
                  </div>
                </div>
                <Progress value={currentMetrics.infrastructure.cpu} />

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <MemoryStick className="w-4 h-4" />
                    <span>Memory Usage</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono">{formatPercent(currentMetrics.infrastructure.memory)}</span>
                    <Badge className={getStatusColor(getHealthStatus(currentMetrics.infrastructure.memory, { good: 75, warning: 90 }))}>
                      {getHealthStatus(currentMetrics.infrastructure.memory, { good: 75, warning: 90 })}
                    </Badge>
                  </div>
                </div>
                <Progress value={currentMetrics.infrastructure.memory} />

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <HardDrive className="w-4 h-4" />
                    <span>Disk Usage</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono">{formatPercent(currentMetrics.infrastructure.disk)}</span>
                    <Badge className={getStatusColor(getHealthStatus(currentMetrics.infrastructure.disk, { good: 80, warning: 90 }))}>
                      {getHealthStatus(currentMetrics.infrastructure.disk, { good: 80, warning: 90 })}
                    </Badge>
                  </div>
                </div>
                <Progress value={currentMetrics.infrastructure.disk} />
              </CardContent>
            </Card>
          </div>

          {/* Performance Score and Web Vitals */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Gauge className="w-5 h-5" />
                  Performance Score
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <div className="text-4xl font-bold mb-2">
                    {currentMetrics.webVitals.score}
                  </div>
                  <Badge className={getStatusColor(getHealthStatus(100 - currentMetrics.webVitals.score, { good: 10, warning: 30 }))}>
                    {currentMetrics.webVitals.score >= 90 ? 'Excellent' : currentMetrics.webVitals.score >= 70 ? 'Good' : 'Needs Improvement'}
                  </Badge>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Core Web Vitals</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span>LCP</span>
                  <span className="font-mono">{formatTime(currentMetrics.webVitals.lcp)}</span>
                </div>
                <div className="flex justify-between">
                  <span>FID</span>
                  <span className="font-mono">{formatTime(currentMetrics.webVitals.fid)}</span>
                </div>
                <div className="flex justify-between">
                  <span>CLS</span>
                  <span className="font-mono">{currentMetrics.webVitals.cls.toFixed(3)}</span>
                </div>
                <div className="flex justify-between">
                  <span>TTFB</span>
                  <span className="font-mono">{formatTime(currentMetrics.webVitals.ttfb)}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Business Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span>Conversion Rate</span>
                  <span className="font-mono">{formatPercent(currentMetrics.business.conversionRate)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Search Success</span>
                  <span className="font-mono">{formatPercent(currentMetrics.business.searchSuccessRate)}</span>
                </div>
                <div className="flex justify-between">
                  <span>User Engagement</span>
                  <span className="font-mono">{currentMetrics.business.userEngagement.toFixed(1)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Session Duration</span>
                  <span className="font-mono">{formatTime(currentMetrics.business.sessionDuration * 1000)}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Application Tab */}
        <TabsContent value="application" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Request Volume</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                    />
                    <YAxis />
                    <Tooltip />
                    <Area
                      type="monotone"
                      dataKey="requestsPerMinute"
                      stroke="#8884d8"
                      fill="#8884d8"
                      fillOpacity={0.3}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Error Rate & Cache Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RechartsLineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                    />
                    <YAxis />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey="errorRate"
                      stroke="#ff7300"
                      name="Error Rate %"
                    />
                    <Line
                      type="monotone"
                      dataKey="cacheHitRate"
                      stroke="#00ff00"
                      name="Cache Hit Rate %"
                    />
                  </RechartsLineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Database & Redis Performance */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Database Performance</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span>Connections</span>
                  <span className="font-mono">
                    {currentMetrics.infrastructure.database.connections} / {currentMetrics.infrastructure.database.maxConnections}
                  </span>
                </div>
                <Progress
                  value={(currentMetrics.infrastructure.database.connections / currentMetrics.infrastructure.database.maxConnections) * 100}
                />
                <div className="flex justify-between">
                  <span>Query Time</span>
                  <span className="font-mono">{formatTime(currentMetrics.infrastructure.database.queryTime)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Latency</span>
                  <span className="font-mono">{formatTime(currentMetrics.application.databaseLatency)}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Redis Performance</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span>Memory Usage</span>
                  <span className="font-mono">{formatPercent(currentMetrics.infrastructure.redis.memory)}</span>
                </div>
                <Progress value={currentMetrics.infrastructure.redis.memory} />
                <div className="flex justify-between">
                  <span>Operations/sec</span>
                  <span className="font-mono">{formatNumber(currentMetrics.infrastructure.redis.opsPerSec)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Connections</span>
                  <span className="font-mono">{currentMetrics.infrastructure.redis.connections}</span>
                </div>
                <div className="flex justify-between">
                  <span>Latency</span>
                  <span className="font-mono">{formatTime(currentMetrics.application.redisLatency)}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Infrastructure Tab */}
        <TabsContent value="infrastructure" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>System Resources</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RechartsLineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                    />
                    <YAxis domain={[0, 100]} />
                    <Tooltip />
                    <Line type="monotone" dataKey="cpu" stroke="#8884d8" name="CPU %" />
                    <Line type="monotone" dataKey="memory" stroke="#82ca9d" name="Memory %" />
                    <Line type="monotone" dataKey="disk" stroke="#ffc658" name="Disk %" />
                  </RechartsLineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Network Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                    />
                    <YAxis />
                    <Tooltip />
                    <Area
                      type="monotone"
                      dataKey="networkIn"
                      stackId="1"
                      stroke="#8884d8"
                      fill="#8884d8"
                      name="Inbound MB/s"
                    />
                    <Area
                      type="monotone"
                      dataKey="networkOut"
                      stackId="1"
                      stroke="#82ca9d"
                      fill="#82ca9d"
                      name="Outbound MB/s"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Current Network Stats */}
          <Card>
            <CardHeader>
              <CardTitle>Network Statistics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-2xl font-bold">
                    {formatNumber(currentMetrics.infrastructure.network.in, 1)} MB/s
                  </div>
                  <p className="text-sm text-muted-foreground">Inbound Traffic</p>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">
                    {formatNumber(currentMetrics.infrastructure.network.out, 1)} MB/s
                  </div>
                  <p className="text-sm text-muted-foreground">Outbound Traffic</p>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">
                    {currentMetrics.infrastructure.network.connections}
                  </div>
                  <p className="text-sm text-muted-foreground">Active Connections</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Web Vitals Tab */}
        <TabsContent value="web-vitals" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Core Web Vitals Trends</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RechartsLineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                    />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="lcp" stroke="#8884d8" name="LCP (ms)" />
                    <Line type="monotone" dataKey="fid" stroke="#82ca9d" name="FID (ms)" />
                    <Line type="monotone" dataKey="ttfb" stroke="#ffc658" name="TTFB (ms)" />
                  </RechartsLineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Performance Score Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center mb-6">
                  <div className="text-5xl font-bold mb-2">
                    {currentMetrics.webVitals.score}
                  </div>
                  <Badge className={`text-lg px-4 py-1 ${getStatusColor(getHealthStatus(100 - currentMetrics.webVitals.score, { good: 10, warning: 30 }))}`}>
                    {currentMetrics.webVitals.score >= 90 ? 'Excellent' : currentMetrics.webVitals.score >= 70 ? 'Good' : 'Needs Improvement'}
                  </Badge>
                </div>

                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>LCP (Largest Contentful Paint)</span>
                      <span>{formatTime(currentMetrics.webVitals.lcp)}</span>
                    </div>
                    <Progress
                      value={Math.min((currentMetrics.webVitals.lcp / 4000) * 100, 100)}
                      className="h-2"
                    />
                  </div>

                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>FID (First Input Delay)</span>
                      <span>{formatTime(currentMetrics.webVitals.fid)}</span>
                    </div>
                    <Progress
                      value={Math.min((currentMetrics.webVitals.fid / 300) * 100, 100)}
                      className="h-2"
                    />
                  </div>

                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>CLS (Cumulative Layout Shift)</span>
                      <span>{currentMetrics.webVitals.cls.toFixed(3)}</span>
                    </div>
                    <Progress
                      value={Math.min((currentMetrics.webVitals.cls / 0.5) * 100, 100)}
                      className="h-2"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Business Tab */}
        <TabsContent value="business" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Business Metrics Trends</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RechartsLineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                    />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="conversionRate" stroke="#8884d8" name="Conversion Rate %" />
                    <Line type="monotone" dataKey="searchSuccessRate" stroke="#82ca9d" name="Search Success %" />
                    <Line type="monotone" dataKey="userEngagement" stroke="#ffc658" name="User Engagement" />
                  </RechartsLineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Performance Impact</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span>Revenue Impact</span>
                  <span className="font-mono text-green-600">
                    +${formatNumber(currentMetrics.business.revenueImpact)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Conversion Rate</span>
                  <span className="font-mono">{formatPercent(currentMetrics.business.conversionRate)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Search Success Rate</span>
                  <span className="font-mono">{formatPercent(currentMetrics.business.searchSuccessRate)}</span>
                </div>
                <div className="flex justify-between">
                  <span>User Engagement Score</span>
                  <span className="font-mono">{currentMetrics.business.userEngagement.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Avg Session Duration</span>
                  <span className="font-mono">{formatTime(currentMetrics.business.sessionDuration * 1000)}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Alerts Tab */}
        <TabsContent value="alerts" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Alert Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span>Active Alerts</span>
                  <Badge variant="destructive">{currentMetrics.alerts.active}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span>Critical</span>
                  <Badge variant="destructive">{currentMetrics.alerts.critical}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span>Warning</span>
                  <Badge variant="secondary">{currentMetrics.alerts.warning}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span>Resolved (24h)</span>
                  <Badge variant="default">{currentMetrics.alerts.resolved24h}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span>Avg Resolution Time</span>
                  <span className="font-mono">{formatTime(currentMetrics.alerts.avgResolutionTime * 60 * 1000)}</span>
                </div>
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Recent Alerts</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {alerts.slice(0, 10).map((alert, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        {alert.severity === 'critical' ? (
                          <AlertTriangle className="w-4 h-4 text-red-600" />
                        ) : (
                          <Bell className="w-4 h-4 text-yellow-600" />
                        )}
                        <div>
                          <div className="font-semibold">{alert.title}</div>
                          <div className="text-sm text-muted-foreground">{alert.description}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge variant={alert.severity === 'critical' ? 'destructive' : 'secondary'}>
                          {alert.severity}
                        </Badge>
                        <div className="text-xs text-muted-foreground mt-1">
                          {new Date(alert.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default RealtimeMonitoringDashboard;
