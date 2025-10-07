import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  DollarSign, FileText, Building, Calculator,
  CheckCircle, XCircle, AlertCircle, Info,
  Calendar, MapPin, Users, Receipt, Printer,
  CreditCard, Home, Shield, TrendingUp, Loader2
} from 'lucide-react';
import { usePropertyTaxInfo } from '@/hooks/usePropertyTaxInfo';

interface PropertyTaxInfoTabProps {
  propertyData: any;
  parcelId?: string;
}

export function PropertyTaxInfoTab({ propertyData, parcelId }: PropertyTaxInfoTabProps) {
  // Use the real tax data hook
  const finalParcelId = parcelId || propertyData?.parcel_id || propertyData?.bcpaData?.parcel_id;
  const { taxInfo, loading, error } = usePropertyTaxInfo(finalParcelId);

  // Fallback to passed tax data if hook data is not available
  const taxData = taxInfo || propertyData?.tax || {};
  const [taxCertificates, setTaxCertificates] = useState<any[]>([]);
  const [loadingCerts, setLoadingCerts] = useState(false);

  // Format currency - returns N/A for null/undefined values
  const formatCurrency = (value: any) => {
    if (value === null || value === undefined || isNaN(parseFloat(value))) {
      return 'N/A';
    }
    const num = parseFloat(value) || 0;
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(num);
  };

  // Format millage rate - returns N/A for null/undefined values
  const formatMillage = (value: any) => {
    if (value === null || value === undefined || isNaN(parseFloat(value))) {
      return 'N/A';
    }
    const num = parseFloat(value) || 0;
    return num.toFixed(5);
  };

  // Format parcel ID for display
  const formatParcelId = (parcelId: string) => {
    if (!parcelId) return 'N/A';
    const cleaned = parcelId.replace(/[^0-9]/g, '');
    if (cleaned.length === 13) {
      return `${cleaned.slice(0, 2)}-${cleaned.slice(2, 6)}-${cleaned.slice(6, 9)}-${cleaned.slice(9)}`;
    }
    return parcelId;
  };

  // Calculate payment status based on actual data from hook or fallback
  const getPaymentStatus = () => {
    // Use hook data if available, otherwise fallback to prop data
    const totalDue = taxInfo?.estimated_annual_taxes || parseFloat(taxData.amount_due) || 0;
    const billStatus = taxInfo?.payment_status || taxData.bill_status || '';

    if (billStatus.toLowerCase() === 'paid' || billStatus === 'current' || totalDue === 0) {
      return { status: 'paid', label: 'CURRENT', color: 'bg-green-100 text-green-800' };
    } else if (billStatus === 'delinquent' || totalDue > 0) {
      return { status: 'due', label: `ESTIMATED: ${formatCurrency(totalDue)}`, color: 'bg-orange-100 text-orange-800' };
    } else if (billStatus === 'certificate_sold') {
      return { status: 'certificate', label: 'TAX CERTIFICATE', color: 'bg-red-100 text-red-800' };
    }
    return { status: 'unknown', label: 'STATUS UNKNOWN', color: 'bg-gray-100 text-gray-800' };
  };

  const paymentStatus = getPaymentStatus();

  // Debug logging to show what data is available
  useEffect(() => {
    console.log('PropertyTaxInfoTab - hook taxInfo:', taxInfo);
    console.log('PropertyTaxInfoTab - hook loading:', loading);
    console.log('PropertyTaxInfoTab - hook error:', error);
    console.log('PropertyTaxInfoTab - final taxData:', taxData);
    console.log('PropertyTaxInfoTab - taxData keys:', taxData ? Object.keys(taxData) : 'null');
  }, [taxInfo, loading, error, taxData]);

  // Loading state
  if (loading) {
    return (
      <div className="space-y-6">
        <Card className="elegant-card">
          <div className="p-6 text-center">
            <Loader2 className="w-12 h-12 text-gold mx-auto mb-3 animate-spin" />
            <h3 className="text-lg font-semibold text-gray-600 mb-2">Loading Tax Information</h3>
            <p className="text-sm text-gray-500">
              Fetching property tax data from multiple sources...
            </p>
          </div>
        </Card>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="space-y-6">
        <Card className="elegant-card">
          <div className="p-6 text-center">
            <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-red-600 mb-2">Error Loading Tax Data</h3>
            <p className="text-sm text-red-500">
              {error}
            </p>
          </div>
        </Card>
      </div>
    );
  }

  // Show message if no tax data is available
  if (!taxData || Object.keys(taxData).length === 0) {
    return (
      <div className="space-y-6">
        <Card className="elegant-card">
          <div className="p-6 text-center">
            <Info className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-gray-600 mb-2">No Tax Data Available</h3>
            <p className="text-sm text-gray-500">
              Tax information is not available for this property in the database.
            </p>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Tax Bill Header */}
      <Card className="elegant-card">
        <div className="p-6">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h2 className="text-2xl font-bold text-navy mb-2">
                {taxInfo?.current_assessment?.year || taxData.tax_year || new Date().getFullYear()} Tax Information
              </h2>
              <p className="text-sm text-gray-600">{taxInfo?.current_assessment?.county || 'County'} Tax Collector</p>
              <p className="text-xs text-gray-500">Notice of Ad Valorem Taxes and Non-ad Valorem Assessments</p>
            </div>
            <Badge className={`text-lg px-4 py-2 ${paymentStatus.color}`}>
              {paymentStatus.label}
            </Badge>
          </div>

          {/* Account Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div className="space-y-3">
              <div className="flex items-start">
                <Home className="w-5 h-5 text-gold mr-2 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-gray-700">Real Estate Account</p>
                  <p className="text-sm text-navy font-mono">#{formatParcelId(finalParcelId || propertyData?.parcel_id)}</p>
                </div>
              </div>

              <div className="flex items-start">
                <Users className="w-5 h-5 text-gold mr-2 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-gray-700">Owner</p>
                  <p className="text-sm text-navy">{propertyData?.owner?.name || propertyData?.bcpaData?.owner_name || propertyData?.owner_name || 'N/A'}</p>
                  {(propertyData?.owner?.name2 || propertyData?.bcpaData?.owner_name2) && (
                    <p className="text-sm text-navy">{propertyData.owner.name2 || propertyData.bcpaData.owner_name2}</p>
                  )}
                </div>
              </div>

              <div className="flex items-start">
                <MapPin className="w-5 h-5 text-gold mr-2 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-gray-700">Situs</p>
                  <p className="text-sm text-navy">{propertyData?.address?.street || 'N/A'}</p>
                  <p className="text-sm text-navy">
                    {propertyData?.address?.city || 'N/A'} {propertyData?.address?.zip || ''}
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-start">
                <Calculator className="w-5 h-5 text-gold mr-2 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-gray-700">Millage Code</p>
                  <p className="text-sm text-navy">
                    {taxData.millage_code || 'N/A'} - {taxData.tax_district || 'N/A'}
                  </p>
                </div>
              </div>

              <div className="flex items-start">
                <TrendingUp className="w-5 h-5 text-gold mr-2 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-gray-700">Millage Rate</p>
                  <p className="text-sm text-navy">{formatMillage(taxData.total_millage)}</p>
                </div>
              </div>

              {taxData.escrow_company && (
                <div className="flex items-start">
                  <CreditCard className="w-5 h-5 text-gold mr-2 mt-0.5" />
                  <div>
                    <p className="text-sm font-semibold text-gray-700">Escrow Company</p>
                    <p className="text-sm text-navy">{taxData.escrow_company}</p>
                    <p className="text-xs text-gray-500">Code: {taxData.escrow_code}</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Bill Summary */}
          <div className="bg-navy-light p-4 rounded-lg">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-gray-600 mb-1">Bill</p>
                <p className="text-sm font-semibold text-navy">{taxData.tax_year || 'N/A'} Annual Bill</p>
              </div>
              <div>
                <p className="text-xs text-gray-600 mb-1">Escrow Code</p>
                <p className="text-sm font-semibold text-navy">{taxData.escrow_code || 'N/A'}</p>
              </div>
              <div>
                <p className="text-xs text-gray-600 mb-1">Millage Code</p>
                <p className="text-sm font-semibold text-navy">{taxData.millage_code || 'N/A'}</p>
              </div>
              <div>
                <p className="text-xs text-gray-600 mb-1">Amount Due</p>
                <p className="text-sm font-bold text-navy">
                  {paymentStatus.status === 'paid' ? '$0.00' : formatCurrency(taxData.amount_due || taxData.total_tax)}
                </p>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Tax Summary */}
      <Card className="elegant-card">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-navy mb-4">
            Combined Taxes and Assessments
          </h3>

          <div className="bg-gold-light p-6 rounded-lg mb-4">
            <p className="text-3xl font-bold text-navy text-center">
              {formatCurrency(taxInfo?.estimated_annual_taxes || taxData.total_tax)}
            </p>
            <p className="text-sm text-gray-600 text-center mt-2">Estimated Annual Tax Amount</p>
            {taxInfo?.total_nav_assessment && taxInfo.total_nav_assessment > 0 && (
              <p className="text-xs text-orange-600 text-center mt-1">
                Includes ${taxInfo.total_nav_assessment.toFixed(0)} in CDD assessments
              </p>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-white rounded-lg border border-gray-200">
              <DollarSign className="w-8 h-8 text-gold mx-auto mb-2" />
              <p className="text-sm text-gray-600 mb-1">Base Tax</p>
              <p className="text-xl font-bold text-navy">
                {formatCurrency((taxInfo?.estimated_annual_taxes || 0) - (taxInfo?.total_nav_assessment || 0))}
              </p>
            </div>

            <div className="text-center p-4 bg-white rounded-lg border border-gray-200">
              <Building className="w-8 h-8 text-gold mx-auto mb-2" />
              <p className="text-sm text-gray-600 mb-1">CDD Assessments</p>
              <p className="text-xl font-bold text-navy">
                {formatCurrency(taxInfo?.total_nav_assessment || taxData.non_ad_valorem_tax)}
              </p>
            </div>

            <div className="text-center p-4 bg-white rounded-lg border border-gray-200">
              <Calculator className="w-8 h-8 text-gold mx-auto mb-2" />
              <p className="text-sm text-gray-600 mb-1">Total Estimated</p>
              <p className="text-xl font-bold text-navy">
                {formatCurrency(taxInfo?.estimated_annual_taxes || taxData.total_tax)}
              </p>
            </div>
          </div>
        </div>
      </Card>

      {/* Ad Valorem Taxes Breakdown - Only show if data exists */}
      {taxData.ad_valorem_breakdown && (
        <Card className="elegant-card">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-navy mb-4">Ad Valorem Taxes</h3>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-left">
                    <th className="py-2 font-semibold text-gray-700">Taxing Authority</th>
                    <th className="py-2 text-right font-semibold text-gray-700">Millage</th>
                    <th className="py-2 text-right font-semibold text-gray-700">Assessed</th>
                    <th className="py-2 text-right font-semibold text-gray-700">Exemption</th>
                    <th className="py-2 text-right font-semibold text-gray-700">Taxable</th>
                    <th className="py-2 text-right font-semibold text-gray-700">Tax</th>
                  </tr>
                </thead>
                <tbody>
                  {/* School Board Section - Only show if data exists */}
                  {taxData.ad_valorem_breakdown.school_board && (
                    <>
                      <tr className="border-t border-gray-100">
                        <td className="py-3 font-semibold text-navy" colSpan={6}>Miami-Dade School Board</td>
                      </tr>
                      {taxData.millage_breakdown?.school_board_operating && (
                        <tr>
                          <td className="py-1 pl-4">School Board Operating</td>
                          <td className="py-1 text-right">{formatMillage(taxData.millage_breakdown.school_board_operating)}</td>
                          <td className="py-1 text-right">{formatCurrency(taxData.assessed_value)}</td>
                          <td className="py-1 text-right">{formatCurrency(taxData.exemptions?.homestead)}</td>
                          <td className="py-1 text-right">{formatCurrency(taxData.school_taxable_value)}</td>
                          <td className="py-1 text-right font-semibold">{formatCurrency(taxData.ad_valorem_breakdown.school_board.operating)}</td>
                        </tr>
                      )}
                      {taxData.millage_breakdown?.school_board_debt && (
                        <tr>
                          <td className="py-1 pl-4">School Board Debt Service</td>
                          <td className="py-1 text-right">{formatMillage(taxData.millage_breakdown.school_board_debt)}</td>
                          <td className="py-1 text-right">{formatCurrency(taxData.assessed_value)}</td>
                          <td className="py-1 text-right">{formatCurrency(taxData.exemptions?.homestead)}</td>
                          <td className="py-1 text-right">{formatCurrency(taxData.school_taxable_value)}</td>
                          <td className="py-1 text-right font-semibold">{formatCurrency(taxData.ad_valorem_breakdown.school_board.debt_service)}</td>
                        </tr>
                      )}
                      {taxData.millage_breakdown?.voted_school_operating && (
                        <tr>
                          <td className="py-1 pl-4">Voted School Operating</td>
                          <td className="py-1 text-right">{formatMillage(taxData.millage_breakdown.voted_school_operating)}</td>
                          <td className="py-1 text-right">{formatCurrency(taxData.assessed_value)}</td>
                          <td className="py-1 text-right">{formatCurrency(taxData.exemptions?.homestead)}</td>
                          <td className="py-1 text-right">{formatCurrency(taxData.school_taxable_value)}</td>
                          <td className="py-1 text-right font-semibold">{formatCurrency(taxData.ad_valorem_breakdown.school_board.voted_operating)}</td>
                        </tr>
                      )}
                    </>
                  )}

                  {/* State and Other Section - Only show if data exists */}
                  {taxData.ad_valorem_breakdown.state_other && (
                    <>
                      <tr className="border-t border-gray-200">
                        <td className="py-3 font-semibold text-navy" colSpan={6}>State and Other</td>
                      </tr>
                      {Object.entries(taxData.ad_valorem_breakdown.state_other).map(([key, value]) => {
                        if (key === 'total') return null; // Skip total row
                        const millageKey = key + '_millage';
                        const millageValue = taxData.millage_breakdown?.[millageKey];

                        return (
                          <tr key={key}>
                            <td className="py-1 pl-4">{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</td>
                            <td className="py-1 text-right">{formatMillage(millageValue)}</td>
                            <td className="py-1 text-right">{formatCurrency(taxData.assessed_value)}</td>
                            <td className="py-1 text-right">{formatCurrency(taxData.exemptions?.total_exemptions)}</td>
                            <td className="py-1 text-right">{formatCurrency(taxData.county_taxable_value)}</td>
                            <td className="py-1 text-right font-semibold">{formatCurrency(value)}</td>
                          </tr>
                        );
                      })}
                    </>
                  )}

                  {/* Miami-Dade County Section - Only show if data exists */}
                  {taxData.ad_valorem_breakdown.miami_dade_county && (
                    <>
                      <tr className="border-t border-gray-200">
                        <td className="py-3 font-semibold text-navy" colSpan={6}>Miami-Dade County</td>
                      </tr>
                      {Object.entries(taxData.ad_valorem_breakdown.miami_dade_county).map(([key, value]) => {
                        if (key === 'total') return null; // Skip total row
                        const millageKey = key + '_millage';
                        const millageValue = taxData.millage_breakdown?.[millageKey];

                        return (
                          <tr key={key}>
                            <td className="py-1 pl-4">{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</td>
                            <td className="py-1 text-right">{formatMillage(millageValue)}</td>
                            <td className="py-1 text-right">{formatCurrency(taxData.assessed_value)}</td>
                            <td className="py-1 text-right">{formatCurrency(taxData.exemptions?.total_exemptions)}</td>
                            <td className="py-1 text-right">{formatCurrency(taxData.county_taxable_value)}</td>
                            <td className="py-1 text-right font-semibold">{formatCurrency(value)}</td>
                          </tr>
                        );
                      })}
                    </>
                  )}

                  {/* Total Row */}
                  <tr className="border-t-2 border-gray-300 font-semibold">
                    <td className="py-3 text-navy">Total Ad Valorem Taxes</td>
                    <td className="py-3 text-right">{formatMillage(taxData.total_millage)}</td>
                    <td className="py-3 text-right" colSpan={3}></td>
                    <td className="py-3 text-right text-lg text-navy">{formatCurrency(taxData.ad_valorem_tax)}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </Card>
      )}

      {/* Non-Ad Valorem Assessments - Only show if data exists */}
      {taxData.non_ad_valorem_breakdown && (
        <Card className="elegant-card">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-navy mb-4">Non-Ad Valorem Assessments</h3>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-left">
                    <th className="py-2 font-semibold text-gray-700">Levying Authority</th>
                    <th className="py-2 text-right font-semibold text-gray-700">Rate</th>
                    <th className="py-2 text-right font-semibold text-gray-700">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(taxData.non_ad_valorem_breakdown).map(([key, value]) => (
                    <tr key={key}>
                      <td className="py-2">{key.replace(/_/g, ' ').toUpperCase()}</td>
                      <td className="py-2 text-right">N/A</td>
                      <td className="py-2 text-right font-semibold">{formatCurrency(value)}</td>
                    </tr>
                  ))}
                  <tr className="border-t-2 border-gray-300 font-semibold">
                    <td className="py-3 text-navy" colSpan={2}>Total Non-Ad Valorem Assessments</td>
                    <td className="py-3 text-right text-lg text-navy">
                      {formatCurrency(taxData.non_ad_valorem_tax)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </Card>
      )}

      {/* Property Details - Only show if data exists */}
      <Card className="elegant-card">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-navy mb-4">Property Details</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <div>
                <p className="text-sm font-semibold text-gray-700 mb-1">Assessed Value</p>
                <p className="text-lg font-bold text-navy">{formatCurrency(taxData.assessed_value)}</p>
              </div>

              <div>
                <p className="text-sm font-semibold text-gray-700 mb-1">School Assessed Value</p>
                <p className="text-lg font-bold text-navy">{formatCurrency(taxData.school_assessed_value)}</p>
              </div>

              <div>
                <p className="text-sm font-semibold text-gray-700 mb-1">Use Code</p>
                <p className="text-lg font-bold text-navy">{propertyData?.property_use || 'N/A'}</p>
              </div>
            </div>

            <div className="space-y-3">
              <div>
                <p className="text-sm font-semibold text-gray-700 mb-1">Exemptions</p>
                <div className="space-y-1">
                  {taxData.exemptions?.homestead > 0 && (
                    <Badge className="bg-green-100 text-green-800 mr-2">
                      HOMESTEAD: {formatCurrency(taxData.exemptions.homestead)}
                    </Badge>
                  )}
                  {taxData.exemptions?.additional_homestead > 0 && (
                    <Badge className="bg-green-100 text-green-800">
                      ADDL HOMESTEAD: {formatCurrency(taxData.exemptions.additional_homestead)}
                    </Badge>
                  )}
                  {(!taxData.exemptions?.homestead && !taxData.exemptions?.additional_homestead) && (
                    <span className="text-sm text-gray-500">No exemptions available in database</span>
                  )}
                </div>
              </div>

              <div>
                <p className="text-sm font-semibold text-gray-700 mb-1">Legal Description</p>
                <p className="text-xs text-gray-600">
                  {propertyData?.legal?.legal_description || 'Not available in database'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Tax Certificates Status */}
      <Card className="elegant-card">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-navy mb-4 flex items-center">
            <FileText className="w-5 h-5 mr-2 text-gold" />
            Tax Certificates
          </h3>

          {paymentStatus.status === 'paid' ? (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
              <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-3" />
              <p className="text-lg font-semibold text-green-800 mb-2">
                No Tax Certificates Outstanding
              </p>
              <p className="text-sm text-green-600">
                All taxes have been paid. The amount due is $0.00.
              </p>
              {taxData.escrow_company && (
                <p className="text-xs text-gray-600 mt-4">
                  {taxData.tax_year} taxes were paid in full through {taxData.escrow_company}.
                </p>
              )}
            </div>
          ) : (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
              <Info className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600">
                Tax certificate information would be displayed here if taxes were unpaid.
                Current status indicates no certificates are outstanding.
              </p>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}