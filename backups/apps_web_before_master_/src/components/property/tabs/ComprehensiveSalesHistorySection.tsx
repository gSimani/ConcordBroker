import React from 'react';
import { TrendingUp, Calendar, FileText, ExternalLink, DollarSign, AlertCircle, CheckCircle } from 'lucide-react';

interface Sale {
  sale_date: string;
  sale_price: number;
  book_page?: string;
  instrument_type?: string;
  qualification?: string;
  vacant_improved?: string;
  grantor?: string;
  grantee?: string;
  instrument_number?: string;
  sale_qualification?: string;
}

interface ComprehensiveSalesHistorySectionProps {
  salesHistory: Sale[];
  parcelId: string;
  county: string;
}

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: '2-digit',
      day: '2-digit',
      year: 'numeric'
    });
  } catch {
    return 'N/A';
  }
};

const getQualificationColor = (qualification?: string): string => {
  if (!qualification) return 'bg-gray-100 text-gray-800';

  const qual = qualification.toLowerCase();
  if (qual.includes('qualified')) return 'bg-green-100 text-green-800';
  if (qual.includes('unqualified')) return 'bg-yellow-100 text-yellow-800';
  return 'bg-blue-100 text-blue-800';
};

const getQualificationIcon = (qualification?: string) => {
  if (!qualification) return <AlertCircle className="w-3 h-3" />;

  const qual = qualification.toLowerCase();
  if (qual.includes('qualified')) return <CheckCircle className="w-3 h-3" />;
  if (qual.includes('unqualified')) return <AlertCircle className="w-3 h-3" />;
  return <FileText className="w-3 h-3" />;
};

export function ComprehensiveSalesHistorySection({
  salesHistory,
  parcelId,
  county
}: ComprehensiveSalesHistorySectionProps) {

  if (!salesHistory || salesHistory.length === 0) {
    return (
      <div className="card-executive">
        <div className="elegant-card-header">
          <h3 className="elegant-card-title flex items-center">
            <TrendingUp className="w-5 h-5 mr-2 text-gold" />
            Sales History
          </h3>
        </div>

        <div className="text-center py-12">
          <TrendingUp className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h4 className="text-xl font-semibold text-gray-700 mb-4">No Sales History Available</h4>

          <div className="bg-blue-50 rounded-lg p-6 max-w-2xl mx-auto">
            <p className="text-sm font-semibold text-blue-800 mb-4">Likely Reasons:</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
              <div className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-blue-600 rounded-full mt-2"></div>
                <div>
                  <span className="text-sm font-medium text-blue-700">Inherited Property</span>
                  <p className="text-xs text-blue-600 mt-1">Transferred through family estate/will</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-blue-600 rounded-full mt-2"></div>
                <div>
                  <span className="text-sm font-medium text-blue-700">Gift Transfer</span>
                  <p className="text-xs text-blue-600 mt-1">Property gifted between family/friends</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-blue-600 rounded-full mt-2"></div>
                <div>
                  <span className="text-sm font-medium text-blue-700">Corporate/Trust Transfer</span>
                  <p className="text-xs text-blue-600 mt-1">Business entity or trust ownership</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-blue-600 rounded-full mt-2"></div>
                <div>
                  <span className="text-sm font-medium text-blue-700">Pre-Digital Records</span>
                  <p className="text-xs text-blue-600 mt-1">Sales before electronic record keeping</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-blue-600 rounded-full mt-2"></div>
                <div>
                  <span className="text-sm font-medium text-blue-700">Government/Municipal Property</span>
                  <p className="text-xs text-blue-600 mt-1">Public sector ownership transfer</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-blue-600 rounded-full mt-2"></div>
                <div>
                  <span className="text-sm font-medium text-blue-700">Long-term Family Ownership</span>
                  <p className="text-xs text-blue-600 mt-1">Property held by same family for generations</p>
                </div>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-blue-200">
              <p className="text-xs text-blue-600">
                <strong>Investment Note:</strong> Properties without sales history may indicate long-term
                family ownership, stable ownership patterns, or unique acquisition circumstances worth
                investigating further through county records.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Filter only qualified sales over $1000
  const qualifiedSales = salesHistory.filter(sale => sale.sale_price > 1000);

  return (
    <div className="card-executive">
      <div className="elegant-card-header">
        <h3 className="elegant-card-title flex items-center justify-between">
          <span className="flex items-center">
            <TrendingUp className="w-5 h-5 mr-2 text-gold" />
            Sales History ({qualifiedSales.length} sales over $1,000)
          </span>
          <span className="text-sm font-normal text-gray-600">
            Showing qualified sales only
          </span>
        </h3>
      </div>

      <div className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 bg-gradient-to-r from-gray-50 to-gray-100">
                <th className="px-4 py-4 text-left">
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 bg-gold rounded-sm flex items-center justify-center">
                      <span className="text-[8px] font-bold text-white">#</span>
                    </div>
                    <span className="text-xs font-semibold text-gray-700 uppercase tracking-wider">
                      Book/Page
                    </span>
                  </div>
                </th>

                <th className="px-4 py-4 text-left">
                  <div className="flex items-center space-x-2">
                    <Calendar className="w-4 h-4 text-gray-600" />
                    <span className="text-xs font-semibold text-gray-700 uppercase tracking-wider">
                      Sale Date
                    </span>
                  </div>
                </th>

                <th className="px-4 py-4 text-left">
                  <div className="flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-gray-600" />
                    <span className="text-xs font-semibold text-gray-700 uppercase tracking-wider">
                      Instrument
                    </span>
                  </div>
                </th>

                <th className="px-4 py-4 text-center">
                  <span className="text-xs font-semibold text-gray-700 uppercase tracking-wider">
                    Qualified
                  </span>
                </th>

                <th className="px-4 py-4 text-center">
                  <span className="text-xs font-semibold text-gray-700 uppercase tracking-wider">
                    Type
                  </span>
                </th>

                <th className="px-4 py-4 text-right">
                  <div className="flex items-center justify-end space-x-2">
                    <DollarSign className="w-4 h-4 text-gray-600" />
                    <span className="text-xs font-semibold text-gray-700 uppercase tracking-wider">
                      Sale Price
                    </span>
                  </div>
                </th>
              </tr>
            </thead>

            <tbody>
              {qualifiedSales.map((sale, index) => (
                <tr
                  key={index}
                  className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                >
                  {/* Book/Page */}
                  <td className="px-4 py-4">
                    <span className="text-sm font-medium text-navy">
                      {sale.book_page || 'N/A'}
                    </span>
                  </td>

                  {/* Sale Date */}
                  <td className="px-4 py-4">
                    <span className="text-sm text-gray-700 font-medium">
                      {formatDate(sale.sale_date)}
                    </span>
                  </td>

                  {/* Instrument Type */}
                  <td className="px-4 py-4">
                    <span className="text-sm text-gray-700">
                      {sale.instrument_type || 'Deed'}
                    </span>
                  </td>

                  {/* Qualification Status */}
                  <td className="px-4 py-4 text-center">
                    <span className={`inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full ${
                      getQualificationColor(sale.qualification)
                    }`}>
                      {getQualificationIcon(sale.qualification)}
                      <span className="ml-1">
                        {sale.qualification || 'Qualified'}
                      </span>
                    </span>
                  </td>

                  {/* Vacant/Improved */}
                  <td className="px-4 py-4 text-center">
                    <span className="text-sm text-gray-700">
                      {sale.vacant_improved || 'Improved'}
                    </span>
                  </td>

                  {/* Sale Price */}
                  <td className="px-4 py-4 text-right">
                    <span className="text-lg font-bold text-navy">
                      {formatCurrency(sale.sale_price)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Summary Footer */}
        <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-gold-light rounded-lg">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-1">Total Sales</h4>
              <p className="text-2xl font-bold text-navy">{qualifiedSales.length}</p>
            </div>

            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-1">Latest Sale</h4>
              <p className="text-lg font-bold text-navy">
                {qualifiedSales.length > 0 ? formatCurrency(qualifiedSales[0].sale_price) : 'N/A'}
              </p>
              <p className="text-xs text-gray-600">
                {qualifiedSales.length > 0 ? formatDate(qualifiedSales[0].sale_date) : ''}
              </p>
            </div>

            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-1">Average Price</h4>
              <p className="text-lg font-bold text-navy">
                {qualifiedSales.length > 0
                  ? formatCurrency(qualifiedSales.reduce((sum, sale) => sum + sale.sale_price, 0) / qualifiedSales.length)
                  : 'N/A'
                }
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}