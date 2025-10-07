import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { 
  Gavel, Calendar, DollarSign, User, AlertTriangle,
  TrendingUp, Clock, FileText, Home, Building,
  Scale, Briefcase, AlertCircle, CheckCircle
} from 'lucide-react';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL || '',
  import.meta.env.VITE_SUPABASE_ANON_KEY || ''
);

interface ForeclosureTabProps {
  propertyData: any;
}

export const ForeclosureTab: React.FC<ForeclosureTabProps> = ({ propertyData }) => {
  const [foreclosures, setForeclosures] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { bcpaData, sdfData } = propertyData || {};

  useEffect(() => {
    const fetchForeclosures = async () => {
      if (!bcpaData?.parcel_id) {
        setLoading(false);
        setError('No parcel ID available');
        return;
      }

      try {
        setError(null);
        // Try to fetch real foreclosure data from Supabase
        const { data, error: supabaseError } = await supabase
          .from('foreclosure_cases')
          .select('*')
          .eq('parcel_id', bcpaData.parcel_id)
          .order('filing_date', { ascending: false });

        if (supabaseError) throw supabaseError;

        // Set the real foreclosure data (or empty array if none)
        setForeclosures(data || []);
      } catch (error) {
        console.error('Error fetching foreclosures:', error);
        setError(error instanceof Error ? error.message : 'Failed to fetch foreclosure data');
        setForeclosures([]);
      } finally {
        setLoading(false);
      }
    };

    fetchForeclosures();
  }, [bcpaData, sdfData]);

  const getStatusColor = (status: string) => {
    const lowerStatus = status?.toLowerCase() || '';
    if (lowerStatus.includes('active') || lowerStatus.includes('pending')) {
      return 'bg-red-100 text-red-800';
    } else if (lowerStatus.includes('closed') || lowerStatus.includes('dismissed')) {
      return 'bg-green-100 text-green-800';
    } else if (lowerStatus.includes('sold')) {
      return 'bg-blue-100 text-blue-800';
    }
    return 'bg-gray-100 text-gray-800';
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(value);
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse">
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="space-y-6">
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertTitle className="text-red-800">Error Loading Foreclosure Data</AlertTitle>
          <AlertDescription className="text-red-700">
            {error}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const hasActiveForeclosure = foreclosures.some(f =>
    f.case_status?.toLowerCase().includes('active') ||
    f.case_status?.toLowerCase().includes('pending')
  );

  return (
    <div className="space-y-6">
      {/* Risk Alert */}
      {hasActiveForeclosure && (
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertTitle className="text-red-800">Active Foreclosure Case</AlertTitle>
          <AlertDescription className="text-red-700">
            This property has an active foreclosure proceeding. Exercise extreme caution and consult legal counsel before proceeding with any transaction.
          </AlertDescription>
        </Alert>
      )}

      {/* Summary Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Gavel className="h-5 w-5 text-red-600" />
            Foreclosure History & Status
          </CardTitle>
          <CardDescription>
            {foreclosures.length > 0 
              ? `${foreclosures.length} foreclosure case${foreclosures.length !== 1 ? 's' : ''} on record`
              : 'No foreclosure history found for this property'
            }
          </CardDescription>
        </CardHeader>
        {foreclosures.length > 0 && (
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-4 bg-red-50 rounded">
                <div className="text-2xl font-bold text-red-700">{foreclosures.length}</div>
                <div className="text-sm text-gray-600">Total Cases</div>
              </div>
              <div className="text-center p-4 bg-blue-50 rounded">
                <div className="text-2xl font-bold text-blue-700">
                  {foreclosures.filter(f => f.auction_status === 'Sold').length}
                </div>
                <div className="text-sm text-gray-600">Auction Sales</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded">
                <div className="text-2xl font-bold text-green-700">
                  {foreclosures.filter(f => 
                    f.case_status?.toLowerCase().includes('closed') || 
                    f.case_status?.toLowerCase().includes('dismissed')
                  ).length}
                </div>
                <div className="text-sm text-gray-600">Cases Closed</div>
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Foreclosure Cases */}
      {foreclosures.map((foreclosure, index) => (
        <Card key={index} className="hover:shadow-lg transition-shadow">
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="text-lg">
                  Case #{foreclosure.case_number}
                </CardTitle>
                <CardDescription>
                  Filed: {new Date(foreclosure.filing_date).toLocaleDateString()}
                </CardDescription>
              </div>
              <Badge className={getStatusColor(foreclosure.case_status)}>
                {foreclosure.case_status}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Parties */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Plaintiff (Lender)</p>
                  <p className="font-medium flex items-center gap-1">
                    <Building className="h-4 w-4 text-gray-500" />
                    {foreclosure.plaintiff}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Defendant (Borrower)</p>
                  <p className="font-medium flex items-center gap-1">
                    <User className="h-4 w-4 text-gray-500" />
                    {foreclosure.defendant}
                  </p>
                </div>
              </div>

              {/* Financial Details */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {foreclosure.original_loan_amount && (
                  <div>
                    <p className="text-sm text-gray-500">Original Loan</p>
                    <p className="font-medium text-lg">
                      {formatCurrency(foreclosure.original_loan_amount)}
                    </p>
                  </div>
                )}
                {foreclosure.judgment_amount && (
                  <div>
                    <p className="text-sm text-gray-500">Judgment Amount</p>
                    <p className="font-medium text-lg text-red-600">
                      {formatCurrency(foreclosure.judgment_amount)}
                    </p>
                  </div>
                )}
                {foreclosure.winning_bid && (
                  <div>
                    <p className="text-sm text-gray-500">Winning Bid</p>
                    <p className="font-medium text-lg text-green-600">
                      {formatCurrency(foreclosure.winning_bid)}
                    </p>
                  </div>
                )}
              </div>

              {/* Important Dates */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {foreclosure.final_judgment_date && (
                  <div>
                    <p className="text-sm text-gray-500">Final Judgment</p>
                    <p className="font-medium flex items-center gap-1">
                      <Scale className="h-4 w-4 text-gray-500" />
                      {new Date(foreclosure.final_judgment_date).toLocaleDateString()}
                    </p>
                  </div>
                )}
                {foreclosure.auction_date && (
                  <div>
                    <p className="text-sm text-gray-500">Auction Date</p>
                    <p className="font-medium flex items-center gap-1">
                      <Gavel className="h-4 w-4 text-gray-500" />
                      {new Date(foreclosure.auction_date).toLocaleDateString()}
                    </p>
                  </div>
                )}
                {foreclosure.redemption_deadline && (
                  <div>
                    <p className="text-sm text-gray-500">Redemption Deadline</p>
                    <p className="font-medium flex items-center gap-1">
                      <Clock className="h-4 w-4 text-gray-500" />
                      {new Date(foreclosure.redemption_deadline).toLocaleDateString()}
                    </p>
                  </div>
                )}
              </div>

              {/* Auction Status */}
              {foreclosure.auction_status && (
                <div className="border-t pt-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">Auction Status</p>
                      <p className="font-medium">{foreclosure.auction_status}</p>
                    </div>
                    {foreclosure.certificate_holder && (
                      <div>
                        <p className="text-sm text-gray-500">Certificate Holder</p>
                        <p className="font-medium">{foreclosure.certificate_holder}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      ))}

      {/* No Foreclosure Message */}
      {foreclosures.length === 0 && (
        <Card className="border-green-200 bg-green-50">
          <CardContent className="text-center py-8">
            <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
            <p className="text-green-800 font-medium">No Foreclosure History</p>
            <p className="text-sm text-green-700 mt-2">
              This property has no recorded foreclosure proceedings
            </p>
          </CardContent>
        </Card>
      )}

      {/* Educational Information */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Understanding Foreclosure Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm text-gray-600">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-yellow-600 mt-0.5" />
              <div>
                <span className="font-medium">Lis Pendens:</span> Initial foreclosure filing, legal notice of pending lawsuit
              </div>
            </div>
            <div className="flex items-start gap-2">
              <Scale className="h-4 w-4 text-orange-600 mt-0.5" />
              <div>
                <span className="font-medium">Final Judgment:</span> Court ruling in favor of lender, sets sale date
              </div>
            </div>
            <div className="flex items-start gap-2">
              <Gavel className="h-4 w-4 text-red-600 mt-0.5" />
              <div>
                <span className="font-medium">Auction Sale:</span> Public sale to highest bidder at courthouse
              </div>
            </div>
            <div className="flex items-start gap-2">
              <Home className="h-4 w-4 text-blue-600 mt-0.5" />
              <div>
                <span className="font-medium">REO:</span> Real Estate Owned - property owned by lender after unsuccessful auction
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};