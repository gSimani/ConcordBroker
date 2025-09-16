/**
 * Data Flow Visualizer Component
 * Shows real-time data flow from database to UI
 */

import React, { useState, useEffect } from 'react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { 
  Database, 
  ArrowRight, 
  Monitor, 
  Activity, 
  Info,
  Filter,
  Eye,
  EyeOff,
  Download,
  RefreshCw
} from 'lucide-react';
import { useDataAccessLog } from '../../hooks/useTrackedData';
import { DATA_MAPPING } from '../../config/data-mapping.config';

interface DataFlowVisualizerProps {
  enabled?: boolean;
}

export const DataFlowVisualizer: React.FC<DataFlowVisualizerProps> = ({ 
  enabled = process.env.NODE_ENV === 'development' 
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [selectedField, setSelectedField] = useState<string | null>(null);
  const [highlightedElements, setHighlightedElements] = useState<string[]>([]);
  const { logs, clearLogs, exportLogs } = useDataAccessLog();

  // Only render in development or when explicitly enabled
  if (!enabled) return null;

  // Highlight UI elements when a field is selected
  useEffect(() => {
    if (selectedTable && selectedField) {
      const mapping = DATA_MAPPING[selectedTable]?.fields[selectedField];
      if (mapping) {
        const elements = mapping.uiLocations.map(loc => 
          loc.replace('${id}', '*')
        );
        setHighlightedElements(elements);
        
        // Add visual highlighting to actual DOM elements
        elements.forEach(pattern => {
          const selector = pattern.includes('*') 
            ? `[id^="${pattern.replace('*', '')}"]`
            : `#${pattern}`;
          
          document.querySelectorAll(selector).forEach(el => {
            (el as HTMLElement).style.outline = '2px solid #3B82F6';
            (el as HTMLElement).style.outlineOffset = '2px';
          });
        });
      }
    }
    
    // Cleanup function to remove highlighting
    return () => {
      document.querySelectorAll('[style*="outline"]').forEach(el => {
        (el as HTMLElement).style.outline = '';
        (el as HTMLElement).style.outlineOffset = '';
      });
    };
  }, [selectedTable, selectedField]);

  // Get unique tables from logs
  const getActiveTables = () => {
    const tables = new Set(logs.map(log => log.table));
    return Array.from(tables);
  };

  // Get fields accessed for a table
  const getAccessedFields = (table: string) => {
    const fields = new Set(
      logs
        .filter(log => log.table === table)
        .map(log => log.field)
    );
    return Array.from(fields);
  };

  // Get access count for a field
  const getAccessCount = (table: string, field: string) => {
    return logs.filter(
      log => log.table === table && log.field === field
    ).length;
  };

  return (
    <>
      {/* Toggle Button */}
      <button
        id="data-flow-toggle"
        onClick={() => setIsVisible(!isVisible)}
        className="fixed bottom-4 left-4 z-50 bg-blue-600 text-white p-3 rounded-full shadow-lg hover:bg-blue-700 transition-all"
        title="Toggle Data Flow Visualizer"
      >
        <Activity className="w-5 h-5" />
      </button>

      {/* Main Visualizer Panel */}
      {isVisible && (
        <div 
          id="data-flow-visualizer"
          className="fixed bottom-20 left-4 z-50 w-96 max-h-[600px] overflow-hidden"
        >
          <Card className="shadow-2xl">
            {/* Header */}
            <div 
              id="data-flow-header"
              className="p-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Activity className="w-5 h-5" />
                  <h3 className="font-semibold">Data Flow Visualizer</h3>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={clearLogs}
                    className="hover:bg-white/20 p-1 rounded"
                    title="Clear logs"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>
                  <button
                    onClick={exportLogs}
                    className="hover:bg-white/20 p-1 rounded"
                    title="Export logs"
                  >
                    <Download className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setIsVisible(false)}
                    className="hover:bg-white/20 p-1 rounded"
                  >
                    <EyeOff className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            {/* Stats Bar */}
            <div 
              id="data-flow-stats"
              className="px-4 py-2 bg-gray-50 border-b flex justify-between text-sm"
            >
              <span>Total Accesses: {logs.length}</span>
              <span>Tables: {getActiveTables().length}</span>
              <span>Errors: {logs.filter(l => !l.success).length}</span>
            </div>

            {/* Content */}
            <div className="overflow-y-auto max-h-[400px]">
              {/* Data Flow Diagram */}
              <div 
                id="data-flow-diagram"
                className="p-4 border-b"
              >
                <h4 className="text-sm font-semibold mb-3">Active Data Flow</h4>
                <div className="flex items-center justify-between">
                  <div className="text-center">
                    <Database className="w-8 h-8 text-blue-600 mx-auto mb-1" />
                    <div className="text-xs">Database</div>
                    <div className="text-xs text-gray-500">
                      {getActiveTables().join(', ') || 'No activity'}
                    </div>
                  </div>
                  <ArrowRight className="w-6 h-6 text-gray-400" />
                  <div className="text-center">
                    <Filter className="w-8 h-8 text-purple-600 mx-auto mb-1" />
                    <div className="text-xs">Transform</div>
                    <div className="text-xs text-gray-500">
                      {logs.filter(l => l.action === 'validate').length} validations
                    </div>
                  </div>
                  <ArrowRight className="w-6 h-6 text-gray-400" />
                  <div className="text-center">
                    <Monitor className="w-8 h-8 text-green-600 mx-auto mb-1" />
                    <div className="text-xs">UI Elements</div>
                    <div className="text-xs text-gray-500">
                      {highlightedElements.length} mapped
                    </div>
                  </div>
                </div>
              </div>

              {/* Table & Field Selection */}
              <div 
                id="data-flow-selection"
                className="p-4 border-b"
              >
                <h4 className="text-sm font-semibold mb-3">Explore Mappings</h4>
                
                {/* Table Selector */}
                <div className="mb-3">
                  <label className="text-xs text-gray-600">Select Table:</label>
                  <select
                    value={selectedTable || ''}
                    onChange={(e) => {
                      setSelectedTable(e.target.value);
                      setSelectedField(null);
                    }}
                    className="w-full mt-1 px-2 py-1 border rounded text-sm"
                  >
                    <option value="">-- Select Table --</option>
                    {Object.keys(DATA_MAPPING).map(table => (
                      <option key={table} value={table}>
                        {table} ({getAccessedFields(table).length} fields accessed)
                      </option>
                    ))}
                  </select>
                </div>

                {/* Field Selector */}
                {selectedTable && (
                  <div>
                    <label className="text-xs text-gray-600">Select Field:</label>
                    <select
                      value={selectedField || ''}
                      onChange={(e) => setSelectedField(e.target.value)}
                      className="w-full mt-1 px-2 py-1 border rounded text-sm"
                    >
                      <option value="">-- Select Field --</option>
                      {Object.keys(DATA_MAPPING[selectedTable].fields).map(field => {
                        const count = getAccessCount(selectedTable, field);
                        return (
                          <option key={field} value={field}>
                            {field} ({count} accesses)
                          </option>
                        );
                      })}
                    </select>
                  </div>
                )}
              </div>

              {/* Field Details */}
              {selectedTable && selectedField && (
                <div 
                  id="data-flow-field-details"
                  className="p-4 border-b bg-blue-50"
                >
                  <h4 className="text-sm font-semibold mb-2">Field Details</h4>
                  <div className="space-y-1 text-xs">
                    <div>
                      <span className="font-medium">Source:</span>{' '}
                      {selectedTable}.{selectedField}
                    </div>
                    <div>
                      <span className="font-medium">Type:</span>{' '}
                      {DATA_MAPPING[selectedTable].fields[selectedField].type}
                    </div>
                    <div>
                      <span className="font-medium">UI Locations:</span>
                      <ul className="mt-1 ml-4 list-disc">
                        {DATA_MAPPING[selectedTable].fields[selectedField].uiLocations.map(
                          (loc, idx) => (
                            <li key={idx} className="text-blue-600">
                              {loc}
                            </li>
                          )
                        )}
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {/* Recent Access Log */}
              <div 
                id="data-flow-logs"
                className="p-4"
              >
                <h4 className="text-sm font-semibold mb-3">Recent Activity</h4>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {logs.slice(-10).reverse().map((log, idx) => (
                    <div
                      key={idx}
                      className={`text-xs p-2 rounded ${
                        log.success ? 'bg-green-50' : 'bg-red-50'
                      }`}
                    >
                      <div className="flex justify-between">
                        <span className="font-medium">
                          {log.action.toUpperCase()}: {log.table}.{log.field}
                        </span>
                        <span className="text-gray-500">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      {log.recordId && (
                        <div className="text-gray-600 mt-1">
                          Record: {log.recordId}
                        </div>
                      )}
                      {log.error && (
                        <div className="text-red-600 mt-1">
                          Error: {log.error}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div 
              id="data-flow-footer"
              className="p-3 bg-gray-50 border-t text-xs text-center text-gray-500"
            >
              <Info className="w-3 h-3 inline mr-1" />
              Click on table/field to highlight UI elements
            </div>
          </Card>
        </div>
      )}
    </>
  );
};