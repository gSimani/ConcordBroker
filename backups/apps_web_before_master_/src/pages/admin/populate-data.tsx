import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { populateSampleData } from '@/lib/populate-data';
import { Database, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';

export default function PopulateDataPage() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [success, setSuccess] = useState(false);

  const handlePopulateData = async () => {
    setLoading(true);
    setMessage('');
    setSuccess(false);
    
    try {
      await populateSampleData();
      setSuccess(true);
      setMessage('Sample data has been successfully populated! You can now view the properties.');
    } catch (error: any) {
      setSuccess(false);
      setMessage(`Error populating data: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <Card className="p-8">
          <div className="flex items-center mb-6">
            <Database className="w-8 h-8 mr-3 text-gold" />
            <h1 className="text-2xl font-bold text-navy">Populate Sample Data</h1>
          </div>
          
          <p className="text-gray-600 mb-6">
            Click the button below to populate the database with sample property data. 
            This will create sample properties that you can use to test the application.
          </p>
          
          <div className="space-y-4">
            <Button
              onClick={handlePopulateData}
              disabled={loading}
              className="w-full md:w-auto"
              style={{ background: '#d4af37' }}
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Populating Data...
                </>
              ) : (
                <>
                  <Database className="w-4 h-4 mr-2" />
                  Populate Sample Data
                </>
              )}
            </Button>
            
            {message && (
              <Alert className={success ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
                {success ? (
                  <CheckCircle className="h-4 w-4 text-green-600" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-red-600" />
                )}
                <AlertDescription className={success ? 'text-green-800' : 'text-red-800'}>
                  {message}
                </AlertDescription>
              </Alert>
            )}
            
            {success && (
              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <h3 className="font-semibold text-blue-900 mb-2">Sample Properties Created:</h3>
                <ul className="space-y-2">
                  <li>
                    <a 
                      href="/property/064210010010" 
                      className="text-blue-600 hover:underline"
                      target="_blank"
                    >
                      → View Property: 1234 SAMPLE ST, FORT LAUDERDALE
                    </a>
                  </li>
                  <li>
                    <a 
                      href="/property/064210010011" 
                      className="text-blue-600 hover:underline"
                      target="_blank"
                    >
                      → View Property: 1236 SAMPLE ST, FORT LAUDERDALE
                    </a>
                  </li>
                  <li>
                    <a 
                      href="/property/064210015020" 
                      className="text-blue-600 hover:underline"
                      target="_blank"
                    >
                      → View Property: 5678 EXAMPLE AVE, PEMBROKE PINES
                    </a>
                  </li>
                </ul>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}