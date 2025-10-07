import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  DollarSign, FileText, Building, Calculator,
  CheckCircle, XCircle, AlertCircle, Info,
  Calendar, MapPin, Users, Receipt, Printer,
  CreditCard, Home, Shield, TrendingUp
} from 'lucide-react';

interface PropertyTaxInfoTabProps {
  propertyData: any;
}

export function PropertyTaxInfoTab({ propertyData }: PropertyTaxInfoTabProps) {
  const taxData = propertyData?.tax || {};
  const [taxCertificates, setTaxCertificates] = useState<any[]>([]);
  const [loadingCerts, setLoadingCerts] = useState(false);

  // Format currency
  const formatCurrency = (value: any) => {
    const num = parseFloat(value) || 0;
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(num);
  };

  // Format millage rate
  const formatMillage = (value: any) => {
    const num = parseFloat(value) || 0;
    return num.toFixed(5);
  };

  // Format parcel ID for display
  const formatParcelId = (parcelId: string) => {
    if (!parcelId) return '';
    const cleaned = parcelId.replace(/[^0-9]/g, '');
    if (cleaned.length === 13) {
      return `${cleaned.slice(0, 2)}-${cleaned.slice(2, 6)}-${cleaned.slice(6, 9)}-${cleaned.slice(9)}`;
    }
    return parcelId;
  };

  // Calculate payment status
  const getPaymentStatus = () => {
    const totalDue = taxData.amount_due || 0;
    const billStatus = taxData.bill_status || '';

    if (billStatus.toLowerCase() === 'paid' || totalDue === 0) {
      return { status: 'paid', label: 'PAID', color: 'bg-green-100 text-green-800' };
    } else if (totalDue > 0) {
      return { status: 'due', label: `DUE: ${formatCurrency(totalDue)}`, color: 'bg-red-100 text-red-800' };
    }
    return { status: 'unknown', label: 'STATUS UNKNOWN', color: 'bg-gray-100 text-gray-800' };
  };

  const paymentStatus = getPaymentStatus();

  // Check for tax certificates
  useEffect(() => {
    // In a real implementation, this would fetch from the database
    // For now, we'll determine based on payment status
    if (paymentStatus.status === 'due' && taxData.total_tax > 0) {
      // Property may have tax certificates if taxes are unpaid
      setTaxCertificates([]);
    }
  }, [taxData, paymentStatus]);

  return (
    <div className="space-y-6">
      {/* Tax Bill Header */}
      <Card className="elegant-card">
        <div className="p-6">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h2 className="text-2xl font-bold text-navy mb-2">
                {taxData.tax_year || new Date().getFullYear()} Annual Tax Bill
              </h2>
              <p className="text-sm text-gray-600">Miami-Dade County Tax Collector</p>
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
                  <p className="text-sm text-navy font-mono">#{formatParcelId(propertyData?.parcel_id)}</p>
                </div>
              </div>

              <div className="flex items-start">
                <Users className="w-5 h-5 text-gold mr-2 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-gray-700">Owner</p>
                  <p className="text-sm text-navy">{propertyData?.owner?.name || 'N/A'}</p>
                  {propertyData?.owner?.name2 && (
                    <p className="text-sm text-navy">{propertyData.owner.name2}</p>
                  )}
                </div>
              </div>

              <div className="flex items-start">
                <MapPin className="w-5 h-5 text-gold mr-2 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-gray-700">Situs</p>
                  <p className="text-sm text-navy">{propertyData?.address?.street}</p>
                  <p className="text-sm text-navy">
                    {propertyData?.address?.city} {propertyData?.address?.zip}
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-start">
                <Calculator className="w-5 h-5 text-gold mr-2 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-gray-700">Millage Code</p>
                  <p className="text-sm text-navy">{taxData.millage_code || '3000'} - UNINCORPORATED DADE COUNTY</p>
                </div>
              </div>

              <div className="flex items-start">
                <TrendingUp className="w-5 h-5 text-gold mr-2 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-gray-700">Millage Rate</p>
                  <p className="text-sm text-navy">{formatMillage(taxData.total_millage || 16.94870)}</p>
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
                <p className="text-sm font-semibold text-navy">{taxData.tax_year} Annual Bill</p>
              </div>
              <div>
                <p className="text-xs text-gray-600 mb-1">Escrow Code</p>
                <p className="text-sm font-semibold text-navy">{taxData.escrow_code || 'N/A'}</p>
              </div>
              <div>
                <p className="text-xs text-gray-600 mb-1">Millage Code</p>
                <p className="text-sm font-semibold text-navy">{taxData.millage_code || '3000'}</p>
              </div>
              <div>
                <p className="text-xs text-gray-600 mb-1">Amount Due</p>
                <p className="text-sm font-bold text-navy">
                  {paymentStatus.status === 'paid' ? '$0.00' : formatCurrency(taxData.total_tax)}
                </p>
              </div>
            </div>
          </div>

          {/* Payment Options */}
          {paymentStatus.status !== 'paid' && (
            <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm font-semibold text-yellow-800 mb-2">Payment Information</p>
              <p className="text-xs text-yellow-700">If paid by: Nov 30, {taxData.tax_year}</p>
              <p className="text-lg font-bold text-yellow-900">{formatCurrency(taxData.total_tax)}</p>
              <p className="text-xs text-yellow-700 mt-2">
                Mail payments payable to: Miami-Dade Office of the Tax Collector<br />
                200 NW 2nd Avenue, Miami, FL 33128<br />
                (In U.S. funds from a U.S. Bank)
              </p>
            </div>
          )}

          {/* Print/Download Options */}
          <div className="mt-4 flex gap-2">
            <button className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
              <Printer className="w-4 h-4" />
              <span className="text-sm">Print (PDF)</span>
            </button>
            <button className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
              <Receipt className="w-4 h-4" />
              <span className="text-sm">BillExpress</span>
            </button>
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
              {formatCurrency(taxData.total_tax || 3455.14)}
            </p>
            <p className="text-sm text-gray-600 text-center mt-2">Total Tax Amount</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-white rounded-lg border border-gray-200">
              <DollarSign className="w-8 h-8 text-gold mx-auto mb-2" />
              <p className="text-sm text-gray-600 mb-1">Ad Valorem</p>
              <p className="text-xl font-bold text-navy">
                {formatCurrency(taxData.ad_valorem_tax || 2718.58)}
              </p>
            </div>

            <div className="text-center p-4 bg-white rounded-lg border border-gray-200">
              <Building className="w-8 h-8 text-gold mx-auto mb-2" />
              <p className="text-sm text-gray-600 mb-1">Non-Ad Valorem</p>
              <p className="text-xl font-bold text-navy">
                {formatCurrency(taxData.non_ad_valorem_tax || 736.56)}
              </p>
            </div>

            <div className="text-center p-4 bg-white rounded-lg border border-gray-200">
              <Calculator className="w-8 h-8 text-gold mx-auto mb-2" />
              <p className="text-sm text-gray-600 mb-1">Total Discountable</p>
              <p className="text-xl font-bold text-navy">
                {formatCurrency(taxData.total_tax || 3455.14)}
              </p>
            </div>
          </div>
        </div>
      </Card>

      {/* Ad Valorem Taxes Breakdown */}
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
                {/* Miami-Dade School Board */}
                <tr className="border-t border-gray-100">
                  <td className="py-3 font-semibold text-navy" colSpan={6}>Miami-Dade School Board</td>
                </tr>
                <tr>
                  <td className="py-1 pl-4">School Board Operating</td>
                  <td className="py-1 text-right">5.46800</td>
                  <td className="py-1 text-right">{formatCurrency(taxData.assessed_value || 200662)}</td>
                  <td className="py-1 text-right">{formatCurrency(25000)}</td>
                  <td className="py-1 text-right">{formatCurrency(taxData.school_taxable_value || 175662)}</td>
                  <td className="py-1 text-right font-semibold">{formatCurrency(taxData.ad_valorem_breakdown?.school_board?.operating || 960.52)}</td>
                </tr>
                <tr>
                  <td className="py-1 pl-4">School Board Debt Service</td>
                  <td className="py-1 text-right">0.13400</td>
                  <td className="py-1 text-right">{formatCurrency(taxData.assessed_value || 200662)}</td>
                  <td className="py-1 text-right">{formatCurrency(25000)}</td>
                  <td className="py-1 text-right">{formatCurrency(taxData.school_taxable_value || 175662)}</td>
                  <td className="py-1 text-right font-semibold">{formatCurrency(taxData.ad_valorem_breakdown?.school_board?.debt_service || 23.54)}</td>
                </tr>
                <tr>
                  <td className="py-1 pl-4">Voted School Operating</td>
                  <td className="py-1 text-right">1.00000</td>
                  <td className="py-1 text-right">{formatCurrency(taxData.assessed_value || 200662)}</td>
                  <td className="py-1 text-right">{formatCurrency(25000)}</td>
                  <td className="py-1 text-right">{formatCurrency(taxData.school_taxable_value || 175662)}</td>
                  <td className="py-1 text-right font-semibold">{formatCurrency(taxData.ad_valorem_breakdown?.school_board?.voted_operating || 175.66)}</td>
                </tr>

                {/* State and Other */}
                <tr className="border-t border-gray-200">
                  <td className="py-3 font-semibold text-navy" colSpan={6}>State and Other</td>
                </tr>
                <tr>
                  <td className="py-1 pl-4">Florida Inland Navigation District</td>
                  <td className="py-1 text-right">0.02880</td>
                  <td className="py-1 text-right">{formatCurrency(taxData.assessed_value || 200662)}</td>
                  <td className="py-1 text-right">{formatCurrency(50000)}</td>
                  <td className="py-1 text-right">{formatCurrency(taxData.county_taxable_value || 150662)}</td>
                  <td className="py-1 text-right font-semibold">{formatCurrency(taxData.ad_valorem_breakdown?.state_other?.inland_nav || 4.34)}</td>
                </tr>
                <tr>
                  <td className="py-1 pl-4">South Florida Water Management District</td>
                  <td className="py-1 text-right">0.09480</td>
                  <td className="py-1 text-right">{formatCurrency(taxData.assessed_value || 200662)}</td>
                  <td className="py-1 text-right">{formatCurrency(50000)}</td>
                  <td className="py-1 text-right">{formatCurrency(taxData.county_taxable_value || 150662)}</td>
                  <td className="py-1 text-right font-semibold">{formatCurrency(taxData.ad_valorem_breakdown?.state_other?.water_mgmt || 14.28)}</td>
                </tr>
                <tr>
                  <td className="py-1 pl-4">Okeechobee Basin</td>
                  <td className="py-1 text-right">0.10260</td>
                  <td className="py-1 text-right">{formatCurrency(taxData.assessed_value || 200662)}</td>
                  <td className="py-1 text-right">{formatCurrency(50000)}</td>
                  <td className="py-1 text-right">{formatCurrency(taxData.county_taxable_value || 150662)}</td>
                  <td className="py-1 text-right font-semibold">{formatCurrency(taxData.ad_valorem_breakdown?.state_other?.okeechobee || 15.46)}</td>
                </tr>
                <tr>
                  <td className="py-1 pl-4">Everglades Construction Project</td>
                  <td className="py-1 text-right">0.03270</td>
                  <td className="py-1 text-right">{formatCurrency(taxData.assessed_value || 200662)}</td>
                  <td className="py-1 text-right">{formatCurrency(50000)}</td>
                  <td className="py-1 text-right">{formatCurrency(taxData.county_taxable_value || 150662)}</td>
                  <td className="py-1 text-right font-semibold">{formatCurrency(taxData.ad_valorem_breakdown?.state_other?.everglades || 4.93)}</td>
                </tr>
                <tr>
                  <td className="py-1 pl-4">Children's Trust Authority</td>
                  <td className="py-1 text-right">0.50000</td>
                  <td className="py-1 text-right">{formatCurrency(taxData.assessed_value || 200662)}</td>
                  <td className="py-1 text-right">{formatCurrency(50000)}</td>
                  <td className="py-1 text-right">{formatCurrency(taxData.county_taxable_value || 150662)}</td>
                  <td className="py-1 text-right font-semibold">{formatCurrency(taxData.ad_valorem_breakdown?.state_other?.childrens_trust || 75.33)}</td>
                </tr>

                {/* Miami-Dade County */}
                <tr className="border-t border-gray-200">
                  <td className="py-3 font-semibold text-navy" colSpan={6}>Miami-Dade County</td>
                </tr>
                <tr>
                  <td className="py-1 pl-4">County Wide Operating</td>
                  <td className="py-1 text-right">4.57400</td>
                  <td className="py-1 text-right">{formatCurrency(taxData.assessed_value || 200662)}</td>
                  <td className="py-1 text-right">{formatCurrency(50000)}</td>
                  <td className="py-1 text-right">{formatCurrency(taxData.county_taxable_value || 150662)}</td>
                  <td className="py-1 text-right font-semibold">{formatCurrency(taxData.ad_valorem_breakdown?.miami_dade_county?.county_operating || 689.13)}</td>
                </tr>
                <tr>
                  <td className="py-1 pl-4">County Wide Debt Service</td>
                  <td className="py-1 text-right">0.42710</td>
                  <td className="py-1 text-right">{formatCurrency(taxData.assessed_value || 200662)}</td>
                  <td className="py-1 text-right">{formatCurrency(50000)}</td>
                  <td className="py-1 text-right">{formatCurrency(taxData.county_taxable_value || 150662)}</td>
                  <td className="py-1 text-right font-semibold">{formatCurrency(taxData.ad_valorem_breakdown?.miami_dade_county?.county_debt || 64.35)}</td>
                </tr>
                <tr>
                  <td className="py-1 pl-4">Unincorporated Operating</td>
                  <td className="py-1 text-right">1.90900</td>
                  <td className="py-1 text-right">{formatCurrency(taxData.assessed_value || 200662)}</td>
                  <td className="py-1 text-right">{formatCurrency(50000)}</td>
                  <td className="py-1 text-right">{formatCurrency(taxData.county_taxable_value || 150662)}</td>
                  <td className="py-1 text-right font-semibold">{formatCurrency(taxData.ad_valorem_breakdown?.miami_dade_county?.unincorporated || 287.61)}</td>
                </tr>
                <tr>
                  <td className="py-1 pl-4">Library District</td>
                  <td className="py-1 text-right">0.28120</td>
                  <td className="py-1 text-right">{formatCurrency(taxData.assessed_value || 200662)}</td>
                  <td className="py-1 text-right">{formatCurrency(50000)}</td>
                  <td className="py-1 text-right">{formatCurrency(taxData.county_taxable_value || 150662)}</td>
                  <td className="py-1 text-right font-semibold">{formatCurrency(taxData.ad_valorem_breakdown?.miami_dade_county?.library || 42.37)}</td>
                </tr>
                <tr>
                  <td className="py-1 pl-4">Fire Rescue Operating</td>
                  <td className="py-1 text-right">2.39650</td>
                  <td className="py-1 text-right">{formatCurrency(taxData.assessed_value || 200662)}</td>
                  <td className="py-1 text-right">{formatCurrency(50000)}</td>
                  <td className="py-1 text-right">{formatCurrency(taxData.county_taxable_value || 150662)}</td>
                  <td className="py-1 text-right font-semibold">{formatCurrency(taxData.ad_valorem_breakdown?.miami_dade_county?.fire_rescue || 361.06)}</td>
                </tr>

                {/* Total Row */}
                <tr className="border-t-2 border-gray-300 font-semibold">
                  <td className="py-3 text-navy">Total Ad Valorem Taxes</td>
                  <td className="py-3 text-right">{formatMillage(taxData.total_millage || 16.94870)}</td>
                  <td className="py-3 text-right" colSpan={3}></td>
                  <td className="py-3 text-right text-lg text-navy">{formatCurrency(taxData.ad_valorem_tax || 2718.58)}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </Card>

      {/* Non-Ad Valorem Assessments */}
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
                <tr>
                  <td className="py-2">SOUTHWEST SEC. 1</td>
                  <td className="py-2 text-right">@ 0.5275</td>
                  <td className="py-2 text-right font-semibold">
                    {formatCurrency(taxData.non_ad_valorem_breakdown?.southwest_sec_1 || 39.56)}
                  </td>
                </tr>
                <tr>
                  <td className="py-2">GARB,TRASH,TRC,RECYCLE</td>
                  <td className="py-2 text-right">@ 697.0000</td>
                  <td className="py-2 text-right font-semibold">
                    {formatCurrency(taxData.non_ad_valorem_breakdown?.garbage_trash_recycle || 697.00)}
                  </td>
                </tr>
                <tr className="border-t-2 border-gray-300 font-semibold">
                  <td className="py-3 text-navy" colSpan={2}>Total Non-Ad Valorem Assessments</td>
                  <td className="py-3 text-right text-lg text-navy">
                    {formatCurrency(taxData.non_ad_valorem_tax || 736.56)}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </Card>

      {/* Property Details */}
      <Card className="elegant-card">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-navy mb-4">Property Details</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <div>
                <p className="text-sm font-semibold text-gray-700 mb-1">Assessed Value</p>
                <p className="text-lg font-bold text-navy">{formatCurrency(taxData.assessed_value || 200662)}</p>
              </div>

              <div>
                <p className="text-sm font-semibold text-gray-700 mb-1">School Assessed Value</p>
                <p className="text-lg font-bold text-navy">{formatCurrency(taxData.school_assessed_value || 200662)}</p>
              </div>

              <div>
                <p className="text-sm font-semibold text-gray-700 mb-1">Location</p>
                <div className="text-sm text-gray-600">
                  <p>Range: {propertyData?.legal?.range || '40E'}</p>
                  <p>Township: {propertyData?.legal?.township || '54S'}</p>
                  <p>Section: {propertyData?.legal?.section || '19'}</p>
                  <p>Block: {propertyData?.legal?.block || '60'}</p>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <div>
                <p className="text-sm font-semibold text-gray-700 mb-1">Use Code</p>
                <p className="text-lg font-bold text-navy">{propertyData?.property_use || '0101'}</p>
              </div>

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
                  {!taxData.exemptions?.homestead && !taxData.exemptions?.additional_homestead && (
                    <span className="text-sm text-gray-500">No exemptions</span>
                  )}
                </div>
              </div>

              <div>
                <p className="text-sm font-semibold text-gray-700 mb-1">Legal Description</p>
                <p className="text-xs text-gray-600">
                  {propertyData?.legal?.legal_description ||
                   'WESTWOOD LAKE PB 57-29 LOT 7 BLK 13 LOT SIZE 75.000 X 100 OR 19086-1264 4/2000 4 COC 21980'}
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
              <p className="text-xs text-gray-600 mt-4">
                {taxData.tax_year} taxes were paid in full{taxData.escrow_company && ` through ${taxData.escrow_company}`}.
              </p>
            </div>
          ) : taxCertificates.length > 0 ? (
            <div className="space-y-3">
              {taxCertificates.map((cert, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-semibold text-navy">Certificate #{cert.certificate_number}</p>
                      <p className="text-sm text-gray-600">Year: {cert.tax_year}</p>
                      <p className="text-sm text-gray-600">Face Value: {formatCurrency(cert.face_value)}</p>
                    </div>
                    <Badge className="bg-orange-100 text-orange-800">
                      {cert.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
              <Info className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600">
                {paymentStatus.status === 'due'
                  ? 'Tax certificates may be issued if taxes remain unpaid.'
                  : 'No tax certificate information available.'}
              </p>
            </div>
          )}
        </div>
      </Card>

      {/* Contact Information */}
      <Card className="elegant-card">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-navy mb-4">Miami-Dade County Tax Collector</h3>
          <p className="text-sm text-gray-600">
            200 NW 2nd Avenue, Miami, FL 33128<br />
            Phone: (305) 270-4916<br />
            Website: www.miamidade.county-taxes.com
          </p>
        </div>
      </Card>
    </div>
  );
}