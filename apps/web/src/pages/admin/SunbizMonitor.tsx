// Cloud-Native Sunbiz Monitor Dashboard
// This runs entirely in the browser, connecting directly to Supabase
// NO PC DEPENDENCY - 100% CLOUD-BASED MONITORING

import React, { useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Button } from '../../components/ui/button';
import { RefreshCw, CheckCircle, XCircle, Clock, Database, Cloud } from 'lucide-react';

// Initialize Supabase client (uses public anon key - safe for browser)
const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
);

interface ProcessedFile {
  id: number;
  file_name: string;
  file_type: string;
  file_date: string;
  records_processed: number;
  entities_created: number;
  entities_updated: number;
  processing_time_seconds: number;
  processed_at: string;
  status: string;
}

interface SupervisorStatus {
  id: number;
  status: string;
  last_update: string;
  metrics: any;
  created_at: string;
}

export default function SunbizMonitor() {
  const [loading, setLoading] = useState(true);
  const [lastStatus, setLastStatus] = useState<SupervisorStatus | null>(null);
  const [recentFiles, setRecentFiles] = useState<ProcessedFile[]>([]);
  const [stats, setStats] = useState({
    totalFiles: 0,
    totalRecords: 0,
    totalEntities: 0,
    avgProcessingTime: 0,
    lastUpdateTime: null as Date | null,
    isHealthy: true
  });
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Load data from Supabase
  const loadData = async () => {
    try {
      // Get latest supervisor status
      const { data: statusData } = await supabase
        .from('sunbiz_supervisor_status')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(1)
        .single();

      if (statusData) {
        setLastStatus(statusData);
      }

      // Get recent processed files
      const { data: filesData } = await supabase
        .from('florida_daily_processed_files')
        .select('*')
        .order('processed_at', { ascending: false })
        .limit(10);

      if (filesData) {
        setRecentFiles(filesData);
      }

      // Calculate statistics
      const { data: statsData } = await supabase
        .from('florida_daily_processed_files')
        .select('records_processed, entities_created, entities_updated, processing_time_seconds');

      if (statsData && statsData.length > 0) {
        const totalRecords = statsData.reduce((sum, f) => sum + (f.records_processed || 0), 0);
        const totalEntities = statsData.reduce((sum, f) => sum + (f.entities_created || 0) + (f.entities_updated || 0), 0);
        const avgTime = statsData.reduce((sum, f) => sum + (f.processing_time_seconds || 0), 0) / statsData.length;

        setStats({
          totalFiles: statsData.length,
          totalRecords,
          totalEntities,
          avgProcessingTime: avgTime,
          lastUpdateTime: statusData ? new Date(statusData.last_update) : null,
          isHealthy: statusData?.status === 'completed' || statusData?.status === 'idle'
        });
      }

      setLoading(false);
    } catch (error) {
      console.error('Error loading data:', error);
      setLoading(false);
    }
  };

  // Manual trigger for testing
  const triggerManualUpdate = async () => {
    try {
      const response = await fetch('/api/cron/sunbiz-daily-update', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${import.meta.env.VITE_CRON_SECRET || 'test-secret'}`
        }
      });

      const result = await response.json();
      
      if (result.success) {
        alert('Manual update triggered successfully!');
        setTimeout(loadData, 2000); // Reload after 2 seconds
      } else {
        alert('Failed to trigger update: ' + result.error);
      }
    } catch (error) {
      alert('Error triggering update: ' + error.message);
    }
  };

  // Auto-refresh every 30 seconds
  useEffect(() => {
    loadData();
    
    if (autoRefresh) {
      const interval = setInterval(loadData, 30000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  // Format time ago
  const timeAgo = (date: Date) => {
    const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000);
    if (seconds < 60) return `${seconds} seconds ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} minutes ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hours ago`;
    const days = Math.floor(hours / 24);
    return `${days} days ago`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <RefreshCw className="animate-spin h-8 w-8" />
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Cloud className="h-8 w-8 text-blue-500" />
          Sunbiz Cloud Monitor
        </h1>
        <p className="text-gray-600 mt-2">
          100% Cloud-Native Daily Update System - No PC Required
        </p>
      </div>

      {/* Status Alert */}
      <Alert className={`mb-6 ${stats.isHealthy ? 'border-green-500' : 'border-red-500'}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {stats.isHealthy ? (
              <CheckCircle className="h-5 w-5 text-green-500" />
            ) : (
              <XCircle className="h-5 w-5 text-red-500" />
            )}
            <AlertDescription>
              System Status: <strong>{lastStatus?.status || 'Unknown'}</strong>
              {stats.lastUpdateTime && (
                <span className="ml-2 text-sm text-gray-500">
                  Last update: {timeAgo(stats.lastUpdateTime)}
                </span>
              )}
            </AlertDescription>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setAutoRefresh(!autoRefresh)}
            >
              {autoRefresh ? 'Pause' : 'Resume'} Auto-Refresh
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={loadData}
            >
              <RefreshCw className="h-4 w-4 mr-1" />
              Refresh
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={triggerManualUpdate}
            >
              Trigger Manual Update
            </Button>
          </div>
        </div>
      </Alert>

      {/* Statistics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Files</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalFiles.toLocaleString()}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Records</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalRecords.toLocaleString()}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Entities</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalEntities.toLocaleString()}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Avg Processing</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.avgProcessingTime.toFixed(1)}s</div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Files Table */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Processed Files</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">File Name</th>
                  <th className="text-left p-2">Type</th>
                  <th className="text-left p-2">Date</th>
                  <th className="text-right p-2">Records</th>
                  <th className="text-right p-2">Created</th>
                  <th className="text-right p-2">Updated</th>
                  <th className="text-right p-2">Time</th>
                  <th className="text-center p-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {recentFiles.map((file) => (
                  <tr key={file.id} className="border-b hover:bg-gray-50">
                    <td className="p-2 font-mono text-xs">{file.file_name}</td>
                    <td className="p-2">{file.file_type}</td>
                    <td className="p-2">{new Date(file.file_date).toLocaleDateString()}</td>
                    <td className="p-2 text-right">{file.records_processed?.toLocaleString()}</td>
                    <td className="p-2 text-right">{file.entities_created?.toLocaleString()}</td>
                    <td className="p-2 text-right">{file.entities_updated?.toLocaleString()}</td>
                    <td className="p-2 text-right">{file.processing_time_seconds?.toFixed(1)}s</td>
                    <td className="p-2 text-center">
                      <span className={`px-2 py-1 rounded text-xs ${
                        file.status === 'completed' ? 'bg-green-100 text-green-800' :
                        file.status === 'error' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {file.status}
                      </span>
                    </td>
                  </tr>
                ))}
                {recentFiles.length === 0 && (
                  <tr>
                    <td colSpan={8} className="p-4 text-center text-gray-500">
                      No files processed yet. The system will start processing at 2 AM EST.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Cloud Architecture Info */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Cloud Architecture</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-start gap-3">
              <Clock className="h-5 w-5 text-blue-500 mt-1" />
              <div>
                <div className="font-semibold">Vercel Cron</div>
                <div className="text-sm text-gray-600">Daily at 2 AM EST</div>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Database className="h-5 w-5 text-green-500 mt-1" />
              <div>
                <div className="font-semibold">Supabase Edge</div>
                <div className="text-sm text-gray-600">Direct SFTP Processing</div>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Cloud className="h-5 w-5 text-purple-500 mt-1" />
              <div>
                <div className="font-semibold">100% Cloud</div>
                <div className="text-sm text-gray-600">No PC Required</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}