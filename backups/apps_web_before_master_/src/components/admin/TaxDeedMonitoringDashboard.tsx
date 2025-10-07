import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { 
  Activity, AlertTriangle, Clock, DollarSign, Gavel, 
  CheckCircle, XCircle, Pause, RefreshCw, Bell,
  TrendingUp, TrendingDown, Eye, Calendar,
  Server, Database, Zap, BarChart3, AlertOctagon
} from 'lucide-react';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL || '',
  import.meta.env.VITE_SUPABASE_ANON_KEY || ''
);

interface MonitoringStatus {
  monitoring_active: boolean;
  active_monitors: number;
  total_monitors: number;
  recent_changes_24h: number;
  critical_changes_24h: number;
  last_update: string;
  performance_metrics: {
    checks_performed: number;
    changes_detected: number;
    alerts_sent: number;
    errors_encountered: number;
  };
  monitor_details: Array<{
    id: number;
    monitor_name: string;
    status: string;
    last_check: string;
    checks_performed: number;
    changes_detected: number;
    errors_encountered: number;
  }>;
}

interface TaxDeedChange {
  id: number;
  change_type: string;
  auction_id: string;
  parcel_id?: string;
  old_value: string;
  new_value: string;
  detected_at: string;
  priority: number;
  details: any;
  alert_sent: boolean;
}

export const TaxDeedMonitoringDashboard: React.FC = () => {
  const [monitoringStatus, setMonitoringStatus] = useState<MonitoringStatus | null>(null);
  const [recentChanges, setRecentChanges] = useState<TaxDeedChange[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchMonitoringData = async () => {
    try {
      setError(null);

      // Fetch monitoring status
      const statusResult = await supabase
        .from('tax_deed_monitoring_status')
        .select('*')
        .order('updated_at', { ascending: false });

      // Fetch recent changes
      const changesResult = await supabase
        .from('tax_deed_changes')
        .select('*')
        .gte('detected_at', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString())
        .order('detected_at', { ascending: false })
        .limit(50);

      if (statusResult.data && changesResult.data) {
        // Calculate aggregated status
        const monitors = statusResult.data;
        const changes = changesResult.data;
        
        const aggregatedStatus: MonitoringStatus = {
          monitoring_active: monitors.some(m => m.status === 'running'),
          active_monitors: monitors.filter(m => m.status === 'running').length,
          total_monitors: monitors.length,
          recent_changes_24h: changes.length,
          critical_changes_24h: changes.filter(c => c.priority <= 2).length,
          last_update: monitors[0]?.updated_at || new Date().toISOString(),
          performance_metrics: {
            checks_performed: monitors.reduce((sum, m) => sum + (m.checks_performed || 0), 0),
            changes_detected: monitors.reduce((sum, m) => sum + (m.changes_detected || 0), 0),
            alerts_sent: changes.filter(c => c.alert_sent).length,
            errors_encountered: monitors.reduce((sum, m) => sum + (m.errors_encountered || 0), 0)
          },
          monitor_details: monitors
        };

        setMonitoringStatus(aggregatedStatus);
        setRecentChanges(changes);
      }

    } catch (err) {
      console.error('Error fetching monitoring data:', err);
      setError('Failed to fetch monitoring data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMonitoringData();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(fetchMonitoringData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'running': return 'bg-green-100 text-green-800 border-green-200';
      case 'completed': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'error': return 'bg-red-100 text-red-800 border-red-200';
      case 'stopped': return 'bg-gray-100 text-gray-800 border-gray-200';
      default: return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    }
  };

  const getChangeTypeIcon = (changeType: string) => {
    switch (changeType) {
      case 'canceled': return <XCircle className="w-4 h-4 text-red-600" />;
      case 'postponed': return <Pause className="w-4 h-4 text-yellow-600" />;
      case 'bid_change': return <DollarSign className="w-4 h-4 text-green-600" />;
      case 'status_change': return <Activity className="w-4 h-4 text-blue-600" />;
      case 'date_change': return <Calendar className="w-4 h-4 text-purple-600" />;
      case 'new_auction': return <Gavel className="w-4 h-4 text-indigo-600" />;
      default: return <AlertTriangle className="w-4 h-4 text-gray-600" />;
    }
  };

  const getPriorityLabel = (priority: number) => {
    if (priority <= 1) return { label: 'CRITICAL', color: 'bg-red-100 text-red-800' };
    if (priority === 2) return { label: 'HIGH', color: 'bg-orange-100 text-orange-800' };
    if (priority === 3) return { label: 'NORMAL', color: 'bg-blue-100 text-blue-800' };
    return { label: 'LOW', color: 'bg-gray-100 text-gray-800' };
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diff = Math.floor((now.getTime() - time.getTime()) / 1000);

    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  };

  if (loading) {
    return (
      <div className="p-6 space-y-4">
        <div className="animate-pulse space-y-6">
          <div className="h-32 bg-gray-200 rounded"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="h-96 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Monitoring Dashboard Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Tax Deed Monitoring Dashboard</h1>
          <p className="text-gray-600">Real-time monitoring of tax deed auction changes</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant={autoRefresh ? "default" : "outline"}
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            Auto Refresh
          </Button>
          <Button variant="outline" size="sm" onClick={fetchMonitoringData}>
            <Eye className="w-4 h-4 mr-2" />
            Refresh Now
          </Button>
        </div>
      </div>

      {/* System Status Alert */}
      {monitoringStatus && (
        <Alert className={`${monitoringStatus.monitoring_active ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
          <Activity className="h-4 w-4" />
          <AlertTitle>
            System Status: {monitoringStatus.monitoring_active ? 'ACTIVE' : 'INACTIVE'}
          </AlertTitle>
          <AlertDescription>
            {monitoringStatus.monitoring_active 
              ? `${monitoringStatus.active_monitors} monitors running successfully`
              : `Monitoring system is not active - ${monitoringStatus.total_monitors} monitors configured`
            }
          </AlertDescription>
        </Alert>
      )}

      {/* Key Metrics */}
      {monitoringStatus && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Active Monitors</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {monitoringStatus.active_monitors}/{monitoringStatus.total_monitors}
                  </p>
                </div>
                <Server className="w-8 h-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Changes (24h)</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {monitoringStatus.recent_changes_24h}
                  </p>
                </div>
                <TrendingUp className="w-8 h-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Critical Alerts</p>
                  <p className="text-2xl font-bold text-red-600">
                    {monitoringStatus.critical_changes_24h}
                  </p>
                </div>
                <AlertOctagon className="w-8 h-8 text-red-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Checks Performed</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {monitoringStatus.performance_metrics.checks_performed.toLocaleString()}
                  </p>
                </div>
                <BarChart3 className="w-8 h-8 text-purple-600" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Monitor Details */}
      {monitoringStatus && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="w-5 h-5" />
              Monitor Details
            </CardTitle>
            <CardDescription>
              Status of individual monitoring agents
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {monitoringStatus.monitor_details.map((monitor) => (
                <div key={monitor.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <Badge className={getStatusColor(monitor.status)}>
                      {monitor.status.toUpperCase()}
                    </Badge>
                    <div>
                      <p className="font-medium">{monitor.monitor_name}</p>
                      <p className="text-sm text-gray-500">
                        Last check: {monitor.last_check ? formatTimeAgo(monitor.last_check) : 'Never'}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">
                      {monitor.checks_performed || 0} checks
                    </p>
                    <p className="text-sm text-gray-500">
                      {monitor.changes_detected || 0} changes
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Changes */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="w-5 h-5" />
            Recent Changes (Last 24 Hours)
          </CardTitle>
          <CardDescription>
            Real-time updates and alerts from tax deed auctions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {recentChanges.length === 0 ? (
              <p className="text-center text-gray-500 py-8">No changes detected in the last 24 hours</p>
            ) : (
              recentChanges.map((change) => {
                const priority = getPriorityLabel(change.priority);
                return (
                  <div key={change.id} className="flex items-start space-x-3 p-3 border rounded-lg hover:bg-gray-50">
                    <div className="flex-shrink-0 mt-1">
                      {getChangeTypeIcon(change.change_type)}
                    </div>
                    <div className="flex-grow min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <Badge className={priority.color}>
                          {priority.label}
                        </Badge>
                        <span className="text-sm font-medium capitalize">
                          {change.change_type.replace('_', ' ')}
                        </span>
                      </div>
                      <p className="text-sm text-gray-900">
                        Auction #{change.auction_id}
                        {change.parcel_id && ` - Parcel: ${change.parcel_id}`}
                      </p>
                      {change.change_type === 'bid_change' && (
                        <p className="text-sm text-gray-600">
                          Bid: ${JSON.parse(change.old_value || '0')} → ${JSON.parse(change.new_value || '0')}
                        </p>
                      )}
                      {change.change_type === 'status_change' && (
                        <p className="text-sm text-gray-600">
                          Status: {change.old_value} → {change.new_value}
                        </p>
                      )}
                    </div>
                    <div className="flex-shrink-0 text-right">
                      <p className="text-xs text-gray-500">
                        {formatTimeAgo(change.detected_at)}
                      </p>
                      {change.alert_sent && (
                        <CheckCircle className="w-4 h-4 text-green-600 mt-1" />
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};