/**
 * Hook for tracked data access with automatic logging and mapping
 */

import { useState, useEffect, useCallback } from 'react';
import { getFieldMapping, transformFieldValue, validateField } from '../config/data-mapping.config';

interface DataAccessLog {
  table: string;
  field: string;
  recordId?: string;
  component: string;
  elementId?: string;
  timestamp: string;
  action: 'fetch' | 'update' | 'validate';
  success: boolean;
  error?: string;
}

interface TrackedDataResult<T = any> {
  data: T | null;
  loading: boolean;
  error: string | null;
  metadata: {
    source: string;
    sourceTable: string;
    sourceField: string;
    fetchedAt: string;
    cacheStatus: 'hit' | 'miss' | 'none';
    transformApplied: boolean;
    validated: boolean;
    uiLocations: string[];
  };
  refetch: () => Promise<void>;
}

// Global data access log for debugging
const dataAccessLog: DataAccessLog[] = [];

// Log data access for debugging and tracking
function logDataAccess(log: DataAccessLog) {
  dataAccessLog.push(log);
  
  // In development, log to console with color coding
  if (process.env.NODE_ENV === 'development') {
    const color = log.success ? 'color: green' : 'color: red';
    console.log(
      `%c[DATA ACCESS] ${log.action.toUpperCase()}`,
      color,
      `\nTable: ${log.table}`,
      `\nField: ${log.field}`,
      `\nRecord: ${log.recordId || 'N/A'}`,
      `\nComponent: ${log.component}`,
      `\nElement: ${log.elementId || 'N/A'}`,
      `\nTime: ${log.timestamp}`
    );
  }
  
  // Send to analytics in production
  if (process.env.NODE_ENV === 'production' && window.analytics) {
    window.analytics.track('Data Access', log);
  }
}

// Get the current component name for tracking
function getCurrentComponent(): string {
  // Try to get component name from React DevTools
  try {
    const fiber = (window as any).__REACT_DEVTOOLS_GLOBAL_HOOK__?.getFiberRoots?.()?.values()?.next()?.value?.current;
    return fiber?.elementType?.name || 'Unknown';
  } catch {
    // Fallback to stack trace parsing
    const stack = new Error().stack || '';
    const match = stack.match(/at (\w+) \(/);
    return match?.[1] || 'Unknown';
  }
}

/**
 * Hook to fetch and track data with automatic mapping
 */
export function useTrackedData<T = any>(
  table: string,
  field: string,
  recordId?: string,
  elementId?: string
): TrackedDataResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<TrackedDataResult<T>['metadata']>({
    source: `${table}.${field}`,
    sourceTable: table,
    sourceField: field,
    fetchedAt: '',
    cacheStatus: 'none',
    transformApplied: false,
    validated: false,
    uiLocations: []
  });

  const fetchData = useCallback(async () => {
    const component = getCurrentComponent();
    const timestamp = new Date().toISOString();
    
    // Log the data access attempt
    logDataAccess({
      table,
      field,
      recordId,
      component,
      elementId,
      timestamp,
      action: 'fetch',
      success: false
    });

    setLoading(true);
    setError(null);

    try {
      // Get field mapping configuration
      const fieldMapping = getFieldMapping(table, field);
      
      // Build API endpoint
      const endpoint = recordId
        ? `/api/data/${table}/${recordId}/${field}`
        : `/api/data/${table}/${field}`;

      // Fetch data
      const response = await fetch(endpoint);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch data: ${response.statusText}`);
      }

      const result = await response.json();
      let value = result.data;

      // Validate the data
      const isValid = validateField(table, field, value);
      if (!isValid && fieldMapping?.validation?.required) {
        throw new Error(`Invalid data for ${table}.${field}`);
      }

      // Apply transformation if configured
      if (fieldMapping?.transform) {
        value = transformFieldValue(table, field, value);
      }

      setData(value);
      setMetadata({
        source: `${table}.${field}`,
        sourceTable: table,
        sourceField: field,
        fetchedAt: timestamp,
        cacheStatus: result.fromCache ? 'hit' : 'miss',
        transformApplied: !!fieldMapping?.transform,
        validated: isValid,
        uiLocations: fieldMapping?.uiLocations || []
      });

      // Log successful access
      logDataAccess({
        table,
        field,
        recordId,
        component,
        elementId,
        timestamp,
        action: 'fetch',
        success: true
      });

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      
      // Log failed access
      logDataAccess({
        table,
        field,
        recordId,
        component,
        elementId,
        timestamp,
        action: 'fetch',
        success: false,
        error: errorMessage
      });
    } finally {
      setLoading(false);
    }
  }, [table, field, recordId, elementId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    metadata,
    refetch: fetchData
  };
}

/**
 * Hook to update tracked data with logging
 */
export function useUpdateTrackedData() {
  return useCallback(async (
    table: string,
    field: string,
    recordId: string,
    value: any,
    elementId?: string
  ): Promise<{ success: boolean; error?: string }> => {
    const component = getCurrentComponent();
    const timestamp = new Date().toISOString();

    // Validate before update
    const isValid = validateField(table, field, value);
    if (!isValid) {
      logDataAccess({
        table,
        field,
        recordId,
        component,
        elementId,
        timestamp,
        action: 'validate',
        success: false,
        error: 'Validation failed'
      });
      return { success: false, error: 'Validation failed' };
    }

    try {
      const response = await fetch(`/api/data/${table}/${recordId}/${field}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value })
      });

      if (!response.ok) {
        throw new Error(`Update failed: ${response.statusText}`);
      }

      logDataAccess({
        table,
        field,
        recordId,
        component,
        elementId,
        timestamp,
        action: 'update',
        success: true
      });

      return { success: true };
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      
      logDataAccess({
        table,
        field,
        recordId,
        component,
        elementId,
        timestamp,
        action: 'update',
        success: false,
        error: errorMessage
      });

      return { success: false, error: errorMessage };
    }
  }, []);
}

/**
 * Hook to get all data access logs (for debugging)
 */
export function useDataAccessLog() {
  const [logs, setLogs] = useState<DataAccessLog[]>([]);

  useEffect(() => {
    const interval = setInterval(() => {
      setLogs([...dataAccessLog]);
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const clearLogs = useCallback(() => {
    dataAccessLog.length = 0;
    setLogs([]);
  }, []);

  const exportLogs = useCallback(() => {
    const blob = new Blob([JSON.stringify(dataAccessLog, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `data-access-log-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, []);

  return {
    logs,
    clearLogs,
    exportLogs
  };
}

// Export for global access
export { dataAccessLog, logDataAccess };