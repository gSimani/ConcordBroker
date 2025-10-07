import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { dorUseCodeService } from '@/services/dorUseCodeService';
import { getDORUseCode } from '@/utils/dorUseCodes';
import { FileText, Database, CheckCircle, XCircle, Search } from 'lucide-react';

export const DORCodeTest: React.FC = () => {
  const [testCode, setTestCode] = useState('001');
  const [localCode, setLocalCode] = useState<any>(null);
  const [dbCode, setDbCode] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<any>(null);

  // Test local mapping
  const testLocalMapping = () => {
    const result = getDORUseCode(testCode);
    setLocalCode(result);
  };

  // Test database lookup
  const testDatabaseLookup = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await dorUseCodeService.getDORUseCode(testCode);
      setDbCode(result);

      // Also get stats
      const categoryStats = await dorUseCodeService.getCategorySummary();
      setStats(categoryStats);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch from database');
    } finally {
      setLoading(false);
    }
  };

  // Run both tests
  const runTests = () => {
    testLocalMapping();
    testDatabaseLookup();
  };

  useEffect(() => {
    runTests();
  }, []);

  return (
    <div className="p-6 space-y-6">
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <FileText className="w-6 h-6 text-blue-600" />
            DOR Use Code Testing
          </h2>
          <Badge variant="outline" className="text-lg px-3 py-1">
            Florida Department of Revenue
          </Badge>
        </div>

        {/* Test Input */}
        <div className="flex gap-4 mb-6">
          <Input
            type="text"
            value={testCode}
            onChange={(e) => setTestCode(e.target.value)}
            placeholder="Enter DOR code (e.g., 001)"
            className="max-w-xs"
          />
          <Button onClick={runTests} disabled={loading}>
            <Search className="w-4 h-4 mr-2" />
            Test Code
          </Button>
        </div>

        {/* Results Grid */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Local Mapping Result */}
          <Card className="p-4 border-2">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Local Mapping (utils/dorUseCodes.ts)
              </h3>
              {localCode && <CheckCircle className="w-5 h-5 text-green-500" />}
            </div>

            {localCode ? (
              <div className="space-y-3">
                <div>
                  <Badge className={`${localCode.bgColor} ${localCode.color} ${localCode.borderColor}`}>
                    {localCode.category}
                  </Badge>
                  {localCode.subcategory && (
                    <Badge variant="outline" className="ml-2">
                      {localCode.subcategory}
                    </Badge>
                  )}
                </div>
                <div className="text-sm space-y-1">
                  <p><strong>Code:</strong> {localCode.code}</p>
                  <p><strong>Description:</strong> {localCode.description}</p>
                </div>
              </div>
            ) : (
              <p className="text-gray-500">No local mapping found</p>
            )}
          </Card>

          {/* Database Result */}
          <Card className="p-4 border-2">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold flex items-center gap-2">
                <Database className="w-4 h-4" />
                Supabase Database
              </h3>
              {dbCode ? (
                <CheckCircle className="w-5 h-5 text-green-500" />
              ) : error ? (
                <XCircle className="w-5 h-5 text-red-500" />
              ) : null}
            </div>

            {loading ? (
              <p className="text-gray-500">Loading from database...</p>
            ) : error ? (
              <div className="text-red-600">
                <p className="font-semibold">Database Not Connected</p>
                <p className="text-sm mt-1">{error}</p>
                <p className="text-xs mt-2 text-gray-600">
                  Run the SQL scripts in Supabase to enable database features
                </p>
              </div>
            ) : dbCode ? (
              <div className="space-y-3">
                <div>
                  <Badge className={`${dbCode.bg_color_class} ${dbCode.color_class} ${dbCode.border_color_class}`}>
                    {dbCode.category}
                  </Badge>
                  {dbCode.subcategory && (
                    <Badge variant="outline" className="ml-2">
                      {dbCode.subcategory}
                    </Badge>
                  )}
                </div>
                <div className="text-sm space-y-1">
                  <p><strong>Code:</strong> {dbCode.code}</p>
                  <p><strong>Description:</strong> {dbCode.description}</p>
                  <div className="flex gap-2 mt-2">
                    {dbCode.is_residential && <Badge variant="secondary" className="text-xs">Residential</Badge>}
                    {dbCode.is_commercial && <Badge variant="secondary" className="text-xs">Commercial</Badge>}
                    {dbCode.is_vacant && <Badge variant="secondary" className="text-xs">Vacant</Badge>}
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-gray-500">No database result</p>
            )}
          </Card>
        </div>

        {/* Category Statistics */}
        {stats && stats.length > 0 && (
          <Card className="mt-6 p-4">
            <h3 className="font-semibold mb-3">Database Category Summary</h3>
            <div className="grid grid-cols-3 md:grid-cols-5 gap-3">
              {stats.map((cat: any) => (
                <div key={cat.category} className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{cat.code_count}</div>
                  <div className="text-xs text-gray-600">{cat.category}</div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Sample Codes */}
        <Card className="mt-6 p-4">
          <h3 className="font-semibold mb-3">Sample DOR Codes to Test</h3>
          <div className="flex flex-wrap gap-2">
            {['000', '001', '002', '003', '010', '017', '021', '039', '040', '050', '066', '071', '083', '091', '098', '099'].map(code => (
              <Button
                key={code}
                variant="outline"
                size="sm"
                onClick={() => {
                  setTestCode(code);
                  setTimeout(runTests, 100);
                }}
              >
                {code}
              </Button>
            ))}
          </div>
        </Card>
      </Card>
    </div>
  );
};

export default DORCodeTest;