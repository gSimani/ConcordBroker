import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Download,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  Database,
  Building2,
  AlertCircle
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface ScraperStatus {
  running: boolean;
  lastRun?: string;
  status?: 'success' | 'error' | 'pending';
  message?: string;
}

interface ScraperConfig {
  id: string;
  name: string;
  description: string;
  icon: React.ElementType;
  workflowFile: string;
  color: string;
  bgColor: string;
  schedule: string;
}

const scraperConfigs: ScraperConfig[] = [
  {
    id: 'property',
    name: 'Property Data Update',
    description: 'Updates Florida property data from 67 counties (NAL, NAP, NAV, SDF files)',
    icon: Building2,
    workflowFile: 'daily-property-update.yml',
    color: '#2c3e50',
    bgColor: 'rgba(44, 62, 80, 0.1)',
    schedule: 'Daily at 2:00 AM EST'
  },
  {
    id: 'sunbiz',
    name: 'Sunbiz Data Update',
    description: 'Updates Florida business entity data from Department of State SFTP',
    icon: Database,
    workflowFile: 'daily-sunbiz-update.yml',
    color: '#3498db',
    bgColor: 'rgba(52, 152, 219, 0.1)',
    schedule: 'Daily at 3:00 AM EST'
  }
];

export default function ScraperControls() {
  const [scraperStatus, setScraperStatus] = useState<Record<string, ScraperStatus>>({
    property: { running: false },
    sunbiz: { running: false }
  });
  const [isDryRun, setIsDryRun] = useState(true);

  const triggerScraper = async (scraper: ScraperConfig) => {
    // Set running status
    setScraperStatus(prev => ({
      ...prev,
      [scraper.id]: { running: true, status: 'pending', message: 'Triggering workflow...' }
    }));

    try {
      // Get MCP server URL from environment or default to localhost:3005
      const mcpUrl = import.meta.env.VITE_MCP_SERVER_URL || 'http://localhost:3005';
      const apiKey = import.meta.env.VITE_MCP_API_KEY || 'concordbroker-mcp-key-claude';

      // Trigger the GitHub Actions workflow via MCP server
      const response = await fetch(
        `${mcpUrl}/api/github/workflows/${scraper.workflowFile}/trigger`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'x-api-key': apiKey
          },
          body: JSON.stringify({
            ref: 'master',
            inputs: {
              dry_run: isDryRun ? 'true' : 'false'
            }
          })
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to trigger workflow: ${response.statusText}`);
      }

      const result = await response.json();

      // Update status to success
      setScraperStatus(prev => ({
        ...prev,
        [scraper.id]: {
          running: false,
          status: 'success',
          message: `Workflow triggered successfully! ${isDryRun ? '(Dry Run Mode)' : ''}`,
          lastRun: new Date().toLocaleString()
        }
      }));

      // Clear success message after 10 seconds
      setTimeout(() => {
        setScraperStatus(prev => ({
          ...prev,
          [scraper.id]: {
            ...prev[scraper.id],
            status: undefined,
            message: undefined
          }
        }));
      }, 10000);

    } catch (error) {
      console.error(`Error triggering ${scraper.name}:`, error);

      // Update status to error
      setScraperStatus(prev => ({
        ...prev,
        [scraper.id]: {
          running: false,
          status: 'error',
          message: error instanceof Error ? error.message : 'Unknown error occurred'
        }
      }));

      // Clear error message after 15 seconds
      setTimeout(() => {
        setScraperStatus(prev => ({
          ...prev,
          [scraper.id]: {
            ...prev[scraper.id],
            status: undefined,
            message: undefined
          }
        }));
      }, 15000);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-medium" style={{ color: '#2c3e50' }}>
            Data Scraper Controls
          </h2>
          <p className="text-sm mt-1" style={{ color: '#7f8c8d' }}>
            Manually trigger scheduled data extraction workflows
          </p>
        </div>

        {/* Dry Run Toggle */}
        <div className="flex items-center space-x-3">
          <span className="text-sm font-medium" style={{ color: '#2c3e50' }}>
            Dry Run Mode
          </span>
          <button
            onClick={() => setIsDryRun(!isDryRun)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              isDryRun ? 'bg-blue-500' : 'bg-gray-300'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                isDryRun ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
          {isDryRun && (
            <span className="text-xs" style={{ color: '#7f8c8d' }}>
              (No database changes)
            </span>
          )}
        </div>
      </div>

      {/* Info Alert */}
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          These scrapers run automatically on schedule. Manual triggers are for testing or forcing immediate updates.
          View logs in GitHub Actions after triggering.
        </AlertDescription>
      </Alert>

      {/* Scraper Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {scraperConfigs.map((scraper, index) => {
          const Icon = scraper.icon;
          const status = scraperStatus[scraper.id];

          return (
            <motion.div
              key={scraper.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className="elegant-card hover-lift">
                <CardHeader className="elegant-card-header">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-3">
                      <div
                        className="p-3 rounded-lg"
                        style={{ backgroundColor: scraper.bgColor }}
                      >
                        <Icon className="w-6 h-6" style={{ color: scraper.color }} />
                      </div>
                      <div>
                        <CardTitle className="elegant-card-title">
                          {scraper.name}
                        </CardTitle>
                        <p className="text-xs mt-1" style={{ color: '#95a5a6' }}>
                          <Clock className="w-3 h-3 inline mr-1" />
                          {scraper.schedule}
                        </p>
                      </div>
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  <CardDescription>{scraper.description}</CardDescription>

                  {/* Status Message */}
                  {status.message && (
                    <Alert
                      className={
                        status.status === 'success'
                          ? 'bg-green-50 border-green-200'
                          : status.status === 'error'
                          ? 'bg-red-50 border-red-200'
                          : 'bg-blue-50 border-blue-200'
                      }
                    >
                      {status.status === 'success' ? (
                        <CheckCircle className="h-4 w-4 text-green-600" />
                      ) : status.status === 'error' ? (
                        <XCircle className="h-4 w-4 text-red-600" />
                      ) : (
                        <RefreshCw className="h-4 w-4 text-blue-600 animate-spin" />
                      )}
                      <AlertDescription
                        className={
                          status.status === 'success'
                            ? 'text-green-700'
                            : status.status === 'error'
                            ? 'text-red-700'
                            : 'text-blue-700'
                        }
                      >
                        {status.message}
                      </AlertDescription>
                    </Alert>
                  )}

                  {/* Last Run Info */}
                  {status.lastRun && (
                    <div className="text-xs" style={{ color: '#7f8c8d' }}>
                      Last triggered: {status.lastRun}
                    </div>
                  )}

                  {/* Action Button */}
                  <Button
                    onClick={() => triggerScraper(scraper)}
                    disabled={status.running}
                    className="w-full"
                    style={{
                      backgroundColor: scraper.color,
                      color: 'white'
                    }}
                  >
                    {status.running ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        Updating...
                      </>
                    ) : (
                      <>
                        <Download className="w-4 h-4 mr-2" />
                        UPDATE RECORDS
                      </>
                    )}
                  </Button>

                  {/* View Logs Link */}
                  <a
                    href={`https://github.com/gSimani/ConcordBroker/actions/workflows/${scraper.workflowFile}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block text-center text-sm hover:underline"
                    style={{ color: '#3498db' }}
                  >
                    View Workflow Logs →
                  </a>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Additional Info */}
      <Card className="elegant-card">
        <CardHeader className="elegant-card-header">
          <CardTitle className="elegant-card-title">About Data Scrapers</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm" style={{ color: '#7f8c8d' }}>
            <p>
              <strong>Property Data Update:</strong> Downloads and processes data from Florida Revenue Portal.
              Covers 268 files across 67 counties including property details, sales history, and valuations.
            </p>
            <p>
              <strong>Sunbiz Data Update:</strong> Connects to Florida Department of State SFTP server to download
              daily business entity files (corporate filings, events, and fictitious names).
            </p>
            <p>
              <strong>Dry Run Mode:</strong> When enabled, the scraper will execute all steps except database writes.
              Useful for testing and verification without affecting production data.
            </p>
            <p className="text-xs italic">
              Note: Workflows may take 30 minutes to 3 hours to complete. Check your email for completion notifications
              or view progress in GitHub Actions.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
