import React, { useState, useEffect } from 'react';
import { Switch } from '@headlessui/react';
import {
  CloudArrowUpIcon,
  ClockIcon,
  ServerIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

interface BackupConfig {
  enabled: boolean;
  schedule_time: string;
  retention_days: number;
  last_backup: string | null;
  next_backup: string | null;
  status: 'enabled' | 'disabled' | 'running' | 'error';
}

interface BackupStats {
  total_backups: number;
  total_size_gb: number;
  last_backup_date: string | null;
  last_backup_size_mb: number | null;
  next_scheduled: string | null;
  status: string;
}

const API_URL = process.env.NODE_ENV === 'production'
  ? 'https://api.concordbroker.com/backup'
  : 'http://localhost:8006';

const API_KEY = 'concordbroker-backup-key-2025';

export default function BackupManager() {
  const [config, setConfig] = useState<BackupConfig | null>(null);
  const [stats, setStats] = useState<BackupStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(false);
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchConfig();
    fetchStats();
    // Refresh every 30 seconds
    const interval = setInterval(() => {
      fetchConfig();
      fetchStats();
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchConfig = async () => {
    try {
      const response = await fetch(`${API_URL}/api/backup/config`, {
        headers: {
          'x-api-key': API_KEY,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      }
    } catch (error) {
      console.error('Error fetching config:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_URL}/api/backup/stats`, {
        headers: {
          'x-api-key': API_KEY,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const toggleBackup = async () => {
    if (!config) return;

    setToggling(true);
    setMessage('');

    try {
      const response = await fetch(`${API_URL}/api/backup/toggle`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': API_KEY,
        },
        body: JSON.stringify({ enabled: !config.enabled }),
      });

      const data = await response.json();

      if (response.ok) {
        setConfig({ ...config, enabled: data.enabled, status: data.status });
        setMessage(data.message);
        // Refresh stats
        fetchStats();
      } else {
        setMessage('Failed to toggle backup');
      }
    } catch (error) {
      console.error('Error toggling backup:', error);
      setMessage('Error toggling backup');
    } finally {
      setToggling(false);
    }
  };

  const runBackupNow = async () => {
    setRunning(true);
    setMessage('');

    try {
      const response = await fetch(`${API_URL}/api/backup/run`, {
        method: 'POST',
        headers: {
          'x-api-key': API_KEY,
        },
      });

      const data = await response.json();

      if (response.ok) {
        setMessage('Backup started in background');
        // Start polling for status
        const pollInterval = setInterval(() => {
          fetchConfig();
          fetchStats();
        }, 5000);

        // Stop polling after 5 minutes
        setTimeout(() => clearInterval(pollInterval), 300000);
      } else {
        setMessage(data.detail || 'Failed to start backup');
      }
    } catch (error) {
      console.error('Error running backup:', error);
      setMessage('Error starting backup');
    } finally {
      setRunning(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'enabled':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'running':
        return <ArrowPathIcon className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'error':
        return <ExclamationCircleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <ExclamationCircleIcon className="h-5 w-5 text-gray-400" />;
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <ArrowPathIcon className="h-8 w-8 text-gray-500 animate-spin" />
      </div>
    );
  }

  return (
    <div id="admin-backup-manager-1" className="bg-white shadow rounded-lg p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center">
          <ServerIcon className="h-7 w-7 mr-3 text-gray-600" />
          Backup Management
        </h2>
        <p className="mt-1 text-sm text-gray-500">
          Configure and monitor daily database backups
        </p>
      </div>

      {/* Main Toggle */}
      <div id="backup-toggle-section-1" className="bg-gray-50 rounded-lg p-6 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <CloudArrowUpIcon className="h-8 w-8 text-gray-600 mr-4" />
            <div>
              <h3 className="text-lg font-medium text-gray-900">
                Daily Automatic Backup
              </h3>
              <p className="text-sm text-gray-500">
                Backup runs daily at {config?.schedule_time || '02:00'} (server time)
              </p>
            </div>
          </div>
          <Switch
            checked={config?.enabled || false}
            onChange={toggleBackup}
            disabled={toggling || config?.status === 'running'}
            className={`${
              config?.enabled ? 'bg-blue-600' : 'bg-gray-200'
            } relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2`}
          >
            <span
              className={`${
                config?.enabled ? 'translate-x-6' : 'translate-x-1'
              } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`}
            />
          </Switch>
        </div>

        {message && (
          <div className="mt-4 p-3 bg-blue-50 rounded-md">
            <p className="text-sm text-blue-700">{message}</p>
          </div>
        )}
      </div>

      {/* Status and Stats */}
      <div id="backup-stats-grid-1" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-500">Status</span>
            {getStatusIcon(config?.status || 'disabled')}
          </div>
          <p className="mt-1 text-lg font-semibold text-gray-900 capitalize">
            {config?.status || 'Unknown'}
          </p>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <span className="text-sm text-gray-500">Total Backups</span>
          <p className="mt-1 text-lg font-semibold text-gray-900">
            {stats?.total_backups || 0}
          </p>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <span className="text-sm text-gray-500">Total Size</span>
          <p className="mt-1 text-lg font-semibold text-gray-900">
            {stats?.total_size_gb || 0} GB
          </p>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <span className="text-sm text-gray-500">Retention</span>
          <p className="mt-1 text-lg font-semibold text-gray-900">
            {config?.retention_days || 30} days
          </p>
        </div>
      </div>

      {/* Backup Timeline */}
      <div id="backup-timeline-section-1" className="bg-gray-50 rounded-lg p-6 mb-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
          <ClockIcon className="h-5 w-5 mr-2 text-gray-600" />
          Backup Schedule
        </h3>

        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-500">Last Backup</span>
            <span className="text-sm font-medium text-gray-900">
              {formatDate(stats?.last_backup_date)}
              {stats?.last_backup_size_mb && (
                <span className="text-gray-500 ml-2">
                  ({stats.last_backup_size_mb} MB)
                </span>
              )}
            </span>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-500">Next Scheduled</span>
            <span className="text-sm font-medium text-gray-900">
              {config?.enabled
                ? formatDate(stats?.next_scheduled)
                : 'Disabled'}
            </span>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div id="backup-actions-section-1" className="flex flex-col sm:flex-row gap-4">
        <button
          onClick={runBackupNow}
          disabled={running || config?.status === 'running'}
          className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-150 flex items-center justify-center"
        >
          {config?.status === 'running' ? (
            <>
              <ArrowPathIcon className="h-5 w-5 mr-2 animate-spin" />
              Backup Running...
            </>
          ) : (
            <>
              <CloudArrowUpIcon className="h-5 w-5 mr-2" />
              Run Backup Now
            </>
          )}
        </button>

        <button
          onClick={() => {
            fetchConfig();
            fetchStats();
          }}
          className="flex-1 bg-gray-200 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-300 transition-colors duration-150 flex items-center justify-center"
        >
          <ArrowPathIcon className="h-5 w-5 mr-2" />
          Refresh Status
        </button>
      </div>

      {/* Database Info */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <p className="text-sm text-blue-700">
          <strong>Database:</strong> 7.3M+ Florida property records
        </p>
        <p className="text-sm text-blue-700 mt-1">
          <strong>Backup Location:</strong> C:/TEMP/SUPABASE_BACKUPS/
        </p>
        <p className="text-sm text-blue-700 mt-1">
          <strong>Compression:</strong> ~90% reduction with gzip
        </p>
      </div>
    </div>
  );
}