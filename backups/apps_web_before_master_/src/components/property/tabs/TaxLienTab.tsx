import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { 
  Link, Calendar, DollarSign, User, Percent,
  TrendingUp, Clock, AlertTriangle, FileText,
  CheckCircle, XCircle, Info, Shield, PiggyBank,
  AlertCircle, ArrowUpRight, Receipt
} from 'lucide-react';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL || '',
  import.meta.env.VITE_SUPABASE_ANON_KEY || ''
);

interface TaxLienTabProps {
  propertyData: any;
}

export const TaxLienTab: React.FC<TaxLienTabProps> = ({ propertyData }) => {
  const [taxLiens, setTaxLiens] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const { bcpaData } = propertyData || {};

  useEffect(() => {
    const fetchTaxLiens = async () => {
      if (!bcpaData?.parcel_id) {
        setLoading(false);
        return;
      }

      try {
        // Try to fetch real tax lien data from Supabase
        const { data, error } = await supabase
          .from('tax_liens')
          .select('*')
          .eq('parcel_id', bcpaData.parcel_id)
          .order('lien_date', { ascending: false });

        if (error) throw error;

        if (data && data.length > 0) {
          setTaxLiens(data);
        } else {
          // No tax lien data found - set empty array
          setTaxLiens([]);
        }
      } catch (error) {
        console.error('Error fetching tax liens:', error);
        setTaxLiens([]);
      } finally {
        setLoading(false);
      }
    };

    fetchTaxLiens();
  }, [bcpaData]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(value);
  };

  const getStatusColor = (status: string) => {
    const lowerStatus = status?.toLowerCase() || '';
    if (lowerStatus.includes('active') || lowerStatus.includes('open')) {
      return 'bg-red-100 text-red-800';
    } else if (lowerStatus.includes('satisfied') || lowerStatus.includes('paid')) {
      return 'bg-green-100 text-green-800';
    } else if (lowerStatus.includes('partial')) {
      return 'bg-yellow-100 text-yellow-800';
    }
    return 'bg-gray-100 text-gray-800';
  };

  const getLienTypeIcon = (type: string) => {
    if (type?.toLowerCase().includes('tax')) {
      return <Receipt className="h-4 w-4 text-red-500" />;
    } else if (type?.toLowerCase().includes('municipal')) {
      return <Shield className="h-4 w-4 text-blue-500" />;
    } else if (type?.toLowerCase().includes('hoa')) {
      return <User className="h-4 w-4 text-purple-500" />;
    }
    return <FileText className="h-4 w-4 text-gray-500" />;
  };

  const calculateAccruedInterest = (principal: number, rate: number, startDate: string) => {
    const start = new Date(startDate);
    const now = new Date();
    const years = (now.getTime() - start.getTime()) / (1000 * 60 * 60 * 24 * 365);
    return principal * (rate / 100) * years;
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

  const activeLiens = taxLiens.filter(l => l.lien_status === 'Active');
  const totalLienAmount = activeLiens.reduce((sum, l) => sum + (l.current_balance || 0), 0);

  return (
    <div className="space-y-6">
      {/* Risk Alert */}
      {activeLiens.length > 0 && (
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertTitle className="text-red-800">Active Tax Liens</AlertTitle>
          <AlertDescription className="text-red-700">
            This property has {activeLiens.length} active lien{activeLiens.length !== 1 ? 's' : ''} totaling {formatCurrency(totalLienAmount)}. 
            These must be satisfied before the property can be sold or refinanced.
          </AlertDescription>
        </Alert>
      )}

      {/* Summary Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Link className="h-5 w-5 text-red-600" />
            Tax Liens & Certificates
          </CardTitle>
          <CardDescription>
            {taxLiens.length > 0 
              ? `${taxLiens.length} lien${taxLiens.length !== 1 ? 's' : ''} on record`
              : 'No tax liens found for this property'
            }
          </CardDescription>
        </CardHeader>
        {taxLiens.length > 0 && (
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-red-50 rounded">
                <div className="text-2xl font-bold text-red-700">{activeLiens.length}</div>
                <div className="text-sm text-gray-600">Active Liens</div>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded">
                <div className="text-2xl font-bold text-orange-700">
                  {formatCurrency(totalLienAmount)}
                </div>
                <div className="text-sm text-gray-600">Total Outstanding</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded">
                <div className="text-2xl font-bold text-green-700">
                  {taxLiens.filter(l => l.lien_status === 'Satisfied').length}
                </div>
                <div className="text-sm text-gray-600">Satisfied</div>
              </div>
              <div className="text-center p-4 bg-blue-50 rounded">
                <div className="text-2xl font-bold text-blue-700">
                  {Math.max(...taxLiens.map(l => l.interest_rate || 0))}%
                </div>
                <div className="text-sm text-gray-600">Max Interest Rate</div>
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Lien Details */}
      {taxLiens.map((lien, index) => (
        <Card key={index} className="hover:shadow-lg transition-shadow">
          <CardHeader>
            <div className="flex justify-between items-start">
              <div className="flex items-center gap-2">
                {getLienTypeIcon(lien.lien_type)}
                <div>
                  <CardTitle className="text-lg">
                    {lien.lien_type}
                  </CardTitle>
                  <CardDescription>
                    Lien #{lien.lien_number} • Filed {new Date(lien.lien_date).toLocaleDateString()}
                  </CardDescription>
                </div>
              </div>
              <Badge className={getStatusColor(lien.lien_status)}>
                {lien.lien_status}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Financial Details */}
              <div className="bg-gray-50 p-4 rounded">
                <h4 className="font-medium mb-3 flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  Financial Details
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Original Amount</p>
                    <p className="font-medium text-lg">
                      {formatCurrency(lien.original_amount)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Current Balance</p>
                    <p className="font-medium text-lg text-red-600">
                      {formatCurrency(lien.current_balance)}
                    </p>
                  </div>
                  {lien.interest_rate && (
                    <div>
                      <p className="text-sm text-gray-500">Interest Rate</p>
                      <p className="font-medium flex items-center gap-1">
                        <Percent className="h-4 w-4 text-orange-500" />
                        {lien.interest_rate}% annually
                      </p>
                    </div>
                  )}
                </div>
                
                {lien.penalty_amount > 0 && (
                  <div className="mt-3 pt-3 border-t">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Penalties & Fees</span>
                      <span className="font-medium text-orange-600">
                        +{formatCurrency(lien.penalty_amount)}
                      </span>
                    </div>
                  </div>
                )}

                {lien.lien_status === 'Active' && lien.interest_rate && (
                  <div className="mt-3 pt-3 border-t">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Estimated Accrued Interest</span>
                      <span className="font-medium text-orange-600">
                        +{formatCurrency(calculateAccruedInterest(
                          lien.original_amount,
                          lien.interest_rate,
                          lien.lien_date
                        ))}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {/* Certificate Information */}
              {lien.certificate_number && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Certificate Number</p>
                    <p className="font-medium">{lien.certificate_number}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Certificate Holder</p>
                    <p className="font-medium">{lien.certificate_holder}</p>
                  </div>
                </div>
              )}

              {/* Tax Year and Priority */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {lien.tax_year && (
                  <div>
                    <p className="text-sm text-gray-500">Tax Year</p>
                    <p className="font-medium">{lien.tax_year}</p>
                  </div>
                )}
                {lien.priority_rank && (
                  <div>
                    <p className="text-sm text-gray-500">Priority Rank</p>
                    <p className="font-medium">#{lien.priority_rank}</p>
                  </div>
                )}
                {lien.recording_info && (
                  <div>
                    <p className="text-sm text-gray-500">Recording Info</p>
                    <p className="font-medium text-xs">{lien.recording_info}</p>
                  </div>
                )}
              </div>

              {/* Redemption/Satisfaction Information */}
              {lien.lien_status === 'Satisfied' && lien.satisfaction_date ? (
                <div className="bg-green-50 p-3 rounded">
                  <div className="flex items-center gap-2 text-green-700 mb-2">
                    <CheckCircle className="h-5 w-5" />
                    <span className="font-medium">Lien Satisfied</span>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">Satisfaction Date</p>
                      <p className="font-medium">
                        {new Date(lien.satisfaction_date).toLocaleDateString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Amount Paid</p>
                      <p className="font-medium">
                        {formatCurrency(lien.satisfaction_amount || lien.original_amount)}
                      </p>
                    </div>
                  </div>
                </div>
              ) : lien.redemption_deadline ? (
                <div className="border-t pt-4">
                  <h4 className="font-medium mb-3 flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    Redemption Timeline
                  </h4>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Redemption Deadline</span>
                      <span className="font-medium">
                        {new Date(lien.redemption_deadline).toLocaleDateString()}
                      </span>
                    </div>
                    <Progress 
                      value={(() => {
                        const start = new Date(lien.lien_date);
                        const end = new Date(lien.redemption_deadline);
                        const now = new Date();
                        const total = end.getTime() - start.getTime();
                        const elapsed = now.getTime() - start.getTime();
                        return Math.min(100, (elapsed / total) * 100);
                      })()}
                      className="h-2"
                    />
                    <p className="text-xs text-gray-500">
                      {(() => {
                        const days = Math.ceil((new Date(lien.redemption_deadline).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24));
                        if (days > 0) {
                          return `${days} days remaining to redeem`;
                        } else {
                          return 'Redemption period expired';
                        }
                      })()}
                    </p>
                  </div>
                </div>
              ) : null}

              {/* Municipal Lien Specific */}
              {lien.lien_type === 'Municipal Lien' && (
                <div className="border-t pt-4">
                  <Alert className="border-blue-200 bg-blue-50">
                    <Info className="h-4 w-4 text-blue-600" />
                    <AlertDescription className="text-blue-700">
                      {lien.description || 'Code violation'} • 
                      {lien.daily_fine && ` Daily fine: $${lien.daily_fine}`}
                      {lien.compliance_deadline && ` • Compliance by: ${new Date(lien.compliance_deadline).toLocaleDateString()}`}
                    </AlertDescription>
                  </Alert>
                </div>
              )}

              {/* Payment Plan */}
              {lien.payment_plan && (
                <div className="bg-blue-50 p-3 rounded">
                  <div className="flex items-center gap-2 text-blue-700">
                    <PiggyBank className="h-4 w-4" />
                    <span className="font-medium">Payment Plan Active</span>
                  </div>
                  {lien.last_payment_date && (
                    <p className="text-sm text-gray-600 mt-1">
                      Last payment: {new Date(lien.last_payment_date).toLocaleDateString()}
                    </p>
                  )}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      ))}

      {/* No Liens Message */}
      {taxLiens.length === 0 && (
        <Card className="border-green-200 bg-green-50">
          <CardContent className="text-center py-8">
            <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
            <p className="text-green-800 font-medium">No Tax Liens</p>
            <p className="text-sm text-green-700 mt-2">
              This property has no recorded tax liens or certificates
            </p>
          </CardContent>
        </Card>
      )}

      {/* Educational Information */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Understanding Tax Liens</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm">
            <div className="flex items-start gap-2">
              <Info className="h-4 w-4 text-blue-600 mt-0.5" />
              <div>
                <span className="font-medium">What is a Tax Lien?</span>
                <p className="text-gray-600 mt-1">
                  A legal claim against a property for unpaid taxes. The lien must be paid before the property can be sold or refinanced.
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-2">
              <ArrowUpRight className="h-4 w-4 text-green-600 mt-0.5" />
              <div>
                <span className="font-medium">Tax Lien Certificates:</span>
                <p className="text-gray-600 mt-1">
                  Investors can purchase tax lien certificates, paying the outstanding taxes and earning interest (up to 18% in Florida) when the owner redeems.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-orange-600 mt-0.5" />
              <div>
                <span className="font-medium">Priority & Risk:</span>
                <p className="text-gray-600 mt-1">
                  Tax liens typically have priority over other liens including mortgages. Unpaid liens can lead to tax deed sales and loss of property.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-2">
              <Shield className="h-4 w-4 text-purple-600 mt-0.5" />
              <div>
                <span className="font-medium">Types of Liens:</span>
                <ul className="text-gray-600 mt-1 list-disc list-inside space-y-1">
                  <li>Property Tax Liens - Unpaid property taxes</li>
                  <li>Municipal Liens - Code violations, utilities</li>
                  <li>HOA Liens - Unpaid association fees</li>
                  <li>IRS Tax Liens - Federal tax obligations</li>
                </ul>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};