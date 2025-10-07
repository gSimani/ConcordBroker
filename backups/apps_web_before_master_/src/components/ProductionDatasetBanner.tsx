import React, { useState, useEffect } from 'react';
import { CheckCircle, AlertTriangle, Database, RefreshCw } from 'lucide-react';
import { unifiedSearchService, DatasetSummary } from '@/services/unified_search_service';

interface ProductionDatasetBannerProps {
  className?: string;
}

export function ProductionDatasetBanner({ className = '' }: ProductionDatasetBannerProps) {
  const [summary, setSummary] = useState<DatasetSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDatasetSummary = async (forceRefresh = false) => {
    try {
      setLoading(true);
      setError(null);

      const data = await unifiedSearchService.getDatasetSummary(forceRefresh);
      setSummary(data);

      // Log for debugging
      console.log('Dataset summary loaded:', data);
    } catch (err) {
      console.error('Failed to load dataset summary:', err);
      setError(err instanceof Error ? err.message : 'Failed to load dataset info');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDatasetSummary();
  }, []);

  if (loading) {
    return (
      <div className={`bg-blue-50 border border-blue-200 rounded-lg p-3 ${className}`}>
        <div className="flex items-center gap-2">
          <RefreshCw className="w-4 h-4 text-blue-600 animate-spin" />
          <span className="text-sm text-blue-800">Verifying dataset...</span>
        </div>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-3 ${className}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-600" />
            <span className="text-sm text-red-800">Dataset verification failed</span>
          </div>
          <button
            onClick={() => loadDatasetSummary(true)}
            className="text-xs text-red-600 hover:text-red-800 underline"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const getStatusColor = () => {
    if (summary.status === 'production') return 'green';
    if (summary.status === 'limited') return 'yellow';
    return 'red';
  };

  const getStatusIcon = () => {
    if (summary.status === 'production') return CheckCircle;
    if (summary.status === 'limited') return AlertTriangle;
    return AlertTriangle;
  };

  const StatusIcon = getStatusIcon();
  const statusColor = getStatusColor();

  return (
    <div className={`bg-${statusColor}-50 border border-${statusColor}-200 rounded-lg p-3 ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <StatusIcon className={`w-4 h-4 text-${statusColor}-600`} />
          <div className="flex items-center gap-3">
            <span className={`text-sm font-medium text-${statusColor}-800`}>
              Dataset: {summary.status === 'production' ? 'Live' : summary.status === 'limited' ? 'Limited' : 'Error'}
            </span>
            <div className="flex items-center gap-1">
              <Database className={`w-3 h-3 text-${statusColor}-600`} />
              <span className={`text-xs text-${statusColor}-700`}>
                {summary.total_properties.toLocaleString()} properties
              </span>
            </div>
            <span className={`text-xs text-${statusColor}-600`}>
              Project: {summary.project_ref}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {summary.status === 'production' && (
            <span className={`px-2 py-1 bg-${statusColor}-100 text-${statusColor}-700 text-xs rounded-full font-medium`}>
              ✓ Production Ready
            </span>
          )}
          {summary.status === 'limited' && (
            <span className={`px-2 py-1 bg-${statusColor}-100 text-${statusColor}-700 text-xs rounded-full font-medium`}>
              ⚠ Limited Dataset
            </span>
          )}
          <button
            onClick={() => loadDatasetSummary(true)}
            className={`text-xs text-${statusColor}-600 hover:text-${statusColor}-800 underline`}
            title="Refresh dataset info"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Additional info for non-production datasets */}
      {summary.status !== 'production' && (
        <div className={`mt-2 pt-2 border-t border-${statusColor}-200`}>
          <p className={`text-xs text-${statusColor}-700`}>
            {summary.status === 'limited'
              ? 'Limited dataset detected. Some properties may not appear in search results.'
              : 'Dataset verification failed. Search results may be incomplete.'
            }
          </p>
          {summary.total_properties < 1000000 && (
            <p className={`text-xs text-${statusColor}-600 mt-1`}>
              Expected: 7+ million properties. Current: {summary.total_properties.toLocaleString()}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// Lightweight version for smaller spaces
export function ProductionDatasetIndicator({ className = '' }: ProductionDatasetBannerProps) {
  const [summary, setSummary] = useState<DatasetSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    unifiedSearchService.getDatasetSummary()
      .then(setSummary)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className={`inline-flex items-center gap-1 ${className}`}>
        <RefreshCw className="w-3 h-3 text-gray-400 animate-spin" />
        <span className="text-xs text-gray-500">Verifying...</span>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className={`inline-flex items-center gap-1 ${className}`}>
        <AlertTriangle className="w-3 h-3 text-red-500" />
        <span className="text-xs text-red-600">Dataset Error</span>
      </div>
    );
  }

  const isProduction = summary.status === 'production';

  return (
    <div className={`inline-flex items-center gap-1 ${className}`}>
      {isProduction ? (
        <CheckCircle className="w-3 h-3 text-green-500" />
      ) : (
        <AlertTriangle className="w-3 h-3 text-yellow-500" />
      )}
      <span className={`text-xs font-medium ${isProduction ? 'text-green-700' : 'text-yellow-700'}`}>
        {isProduction ? 'Live' : 'Limited'} ({summary.total_properties.toLocaleString()})
      </span>
    </div>
  );
}