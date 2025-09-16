import React from 'react';
import { Calendar, DollarSign, TrendingUp, MapPin, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import { useSalesData, formatSalesForSdfData } from '@/hooks/useSalesData';

interface SalesHistoryTabUpdatedProps {
  parcelId: string;
  data?: any; // Fallback data
}

export function SalesHistoryTabUpdated({ parcelId, data }: SalesHistoryTabUpdatedProps) {
  const { salesData, isLoading, error } = useSalesData(parcelId);

  // Format currency
  const formatCurrency = (value?: number) => {
    if (!value || value === 0) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  // Format date
  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch {
      return dateString;
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="card-executive">
        <div className="elegant-card-header">
          <h3 className="elegant-card-title gold-accent flex items-center">
            <Calendar className="w-5 h-5 mr-2 text-navy" />
            Sales History
          </h3>
          <p className="text-sm mt-4 text-gray-elegant">Loading sales data...</p>
        </div>
        <div className="pt-8">
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold"></div>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="card-executive">
        <div className="elegant-card-header">
          <h3 className="elegant-card-title gold-accent flex items-center">
            <Calendar className="w-5 h-5 mr-2 text-navy" />
            Sales History
          </h3>
        </div>
        <div className="pt-8">
          <div className="text-center py-12">
            <AlertCircle className="w-12 h-12 mx-auto mb-4 text-red-500" />
            <p className="text-lg font-medium text-red-600">Error Loading Sales Data</p>
            <p className="text-sm text-gray-600">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  // No data state
  if (!salesData || salesData.total_sales_count === 0) {
    return (
      <div className="card-executive">
        <div className="elegant-card-header">
          <h3 className="elegant-card-title gold-accent flex items-center">
            <Calendar className="w-5 h-5 mr-2 text-navy" />
            Sales History
          </h3>
          <p className="text-sm mt-4 text-gray-elegant">All recorded sales for this property</p>
        </div>
        <div className="pt-8">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-12"
          >
            <TrendingUp className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p className="text-lg font-medium text-gray-500">No Sales History Available</p>
            <p className="text-sm text-gray-400 mt-1">
              Property may be newly constructed or have no recorded sales
            </p>

            {/* Additional help text */}
            <div className="mt-6 p-4 bg-blue-50 rounded-lg max-w-md mx-auto">
              <p className="text-sm text-blue-700">
                <strong>Possible reasons:</strong>
              </p>
              <ul className="text-xs text-blue-600 mt-2 space-y-1">
                <li>• Property has never been sold</li>
                <li>• Sales data not yet imported</li>
                <li>• Property is newly constructed</li>
                <li>• Records are in different database tables</li>
              </ul>
            </div>
          </motion.div>
        </div>
      </div>
    );
  }

  // Format sales data for display
  const allSales = [salesData.most_recent_sale, ...salesData.previous_sales].filter(Boolean);

  return (
    <div className="card-executive">
      <div className="elegant-card-header">
        <h3 className="elegant-card-title gold-accent flex items-center">
          <Calendar className="w-5 h-5 mr-2 text-navy" />
          Sales History
        </h3>
        <p className="text-sm mt-4 text-gray-elegant">
          All recorded sales for this property ({salesData.total_sales_count} transaction{salesData.total_sales_count !== 1 ? 's' : ''})
        </p>
      </div>

      <div className="pt-8">
        {/* Sales Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-gradient-to-r from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-700 font-medium">Most Recent Sale</p>
                <p className="text-2xl font-bold text-green-800">
                  {formatCurrency(salesData.most_recent_sale?.sale_price)}
                </p>
                <p className="text-xs text-green-600">
                  {salesData.most_recent_sale?.sale_date && formatDate(salesData.most_recent_sale.sale_date)}
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-green-600" />
            </div>
          </div>

          <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-700 font-medium">Average Price</p>
                <p className="text-2xl font-bold text-blue-800">
                  {formatCurrency(salesData.average_sale_price)}
                </p>
                <p className="text-xs text-blue-600">Over {salesData.total_sales_count} sales</p>
              </div>
              <TrendingUp className="w-8 h-8 text-blue-600" />
            </div>
          </div>

          <div className="bg-gradient-to-r from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-purple-700 font-medium">Highest Sale</p>
                <p className="text-2xl font-bold text-purple-800">
                  {formatCurrency(salesData.highest_sale_price)}
                </p>
                <p className="text-xs text-purple-600">Peak value</p>
              </div>
              <TrendingUp className="w-8 h-8 text-purple-600" />
            </div>
          </div>

          <div className="bg-gradient-to-r from-orange-50 to-orange-100 p-4 rounded-lg border border-orange-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-orange-700 font-medium">Market Activity</p>
                <p className="text-2xl font-bold text-orange-800">{salesData.years_on_market}</p>
                <p className="text-xs text-orange-600">Years of sales</p>
              </div>
              <Calendar className="w-8 h-8 text-orange-600" />
            </div>
          </div>
        </div>

        {/* Detailed Sales History */}
        <div className="space-y-6">
          {allSales.map((sale, index) => (
            <motion.div
              key={`${sale!.sale_date}-${sale!.sale_price}-${index}`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`p-6 rounded-lg border transition-all hover:shadow-lg ${
                index === 0 ? 'bg-gold-light border-gold shadow-md ring-2 ring-gold/20' : 'bg-gray-light border-gray-elegant'
              }`}
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <div className="flex items-center space-x-3 mb-2">
                    <p className="text-2xl font-semibold text-navy">
                      {formatCurrency(sale!.sale_price)}
                    </p>
                    {index === 0 && (
                      <span className="badge-elegant badge-gold text-xs">Most Recent</span>
                    )}
                  </div>
                  <p className="text-sm uppercase tracking-wider text-gray-elegant flex items-center">
                    <Calendar className="w-4 h-4 mr-1" />
                    {formatDate(sale!.sale_date)}
                  </p>
                </div>

                <div className="flex flex-col items-end space-y-2">
                  <div className={`px-3 py-1 rounded-full text-xs font-medium uppercase tracking-wider ${
                    sale!.qualified_sale
                      ? 'text-green-700 bg-green-100 border border-green-200'
                      : 'text-orange-700 bg-orange-100 border border-orange-200'
                  }`}>
                    {sale!.qualified_sale ? 'Qualified Sale' : 'Unqualified Sale'}
                  </div>

                  {/* Sale characteristics badges */}
                  <div className="flex flex-wrap gap-1 justify-end">
                    {sale!.is_cash_sale && (
                      <span className="badge-elegant badge-gold text-xs">Cash Sale</span>
                    )}
                    {sale!.is_bank_sale && (
                      <span className="badge-elegant bg-blue-100 text-blue-800 text-xs">Bank Sale</span>
                    )}
                    {sale!.is_distressed && (
                      <span className="badge-elegant bg-red-100 text-red-800 text-xs">Distressed</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Sale Details Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                {sale!.document_type && (
                  <div className="flex flex-col">
                    <span className="text-xs uppercase tracking-wider text-gray-elegant">Document Info</span>
                    <span className="font-medium text-navy">{sale!.document_type}</span>
                    {sale!.book && sale!.page && (
                      <span className="text-sm text-gray-elegant">Book {sale!.book}, Page {sale!.page}</span>
                    )}
                  </div>
                )}

                {(sale!.grantor_name || sale!.grantee_name) && (
                  <div className="flex flex-col">
                    <span className="text-xs uppercase tracking-wider text-gray-elegant">Transaction Parties</span>
                    <div className="space-y-1">
                      {sale!.grantor_name && (
                        <div className="text-sm">
                          <span className="text-gray-elegant">From: </span>
                          <span className="text-navy font-medium">{sale!.grantor_name}</span>
                        </div>
                      )}
                      {sale!.grantee_name && (
                        <div className="text-sm">
                          <span className="text-gray-elegant">To: </span>
                          <span className="text-navy font-medium">{sale!.grantee_name}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                <div className="flex flex-col">
                  <span className="text-xs uppercase tracking-wider text-gray-elegant">Data Source</span>
                  <span className="text-sm font-medium text-blue-600 capitalize">
                    {sale!.data_source.replace('_', ' ')}
                  </span>
                  {sale!.sale_reason && (
                    <span className="text-xs text-gray-elegant mt-1">{sale!.sale_reason}</span>
                  )}
                </div>
              </div>

              {/* Price Change Analysis */}
              {index > 0 && allSales[index - 1] && (
                <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-blue-700">Price Change from Previous Sale:</span>
                    <div className="flex items-center space-x-2">
                      {(() => {
                        const currentPrice = sale!.sale_price;
                        const previousPrice = allSales[index - 1]!.sale_price;
                        const change = currentPrice - previousPrice;
                        const percentChange = previousPrice > 0 ? (change / previousPrice) * 100 : 0;

                        return (
                          <>
                            {change > 0 ? (
                              <TrendingUp className="w-4 h-4 text-green-600" />
                            ) : (
                              <TrendingUp className="w-4 h-4 text-red-600 rotate-180" />
                            )}
                            <span className={`font-semibold ${
                              change > 0 ? 'text-green-600' : 'text-red-600'
                            }`}>
                              {change > 0 ? '+' : ''}{formatCurrency(Math.abs(change))}
                              {' '}({percentChange > 0 ? '+' : ''}{percentChange.toFixed(1)}%)
                            </span>
                          </>
                        );
                      })()}
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          ))}
        </div>

        {/* Sales Performance Summary */}
        {salesData.total_sales_count > 1 && (
          <div className="mt-8 p-6 bg-navy rounded-lg">
            <h4 className="text-lg font-semibold text-white mb-4 flex items-center">
              <TrendingUp className="w-5 h-5 mr-2" />
              Sales Performance Analytics
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-white">
              <div>
                <p className="text-sm opacity-75">Total Transactions</p>
                <p className="text-3xl font-light">{salesData.total_sales_count}</p>
                <p className="text-xs opacity-60 mt-1">Recorded sales</p>
              </div>
              <div>
                <p className="text-sm opacity-75">Price Appreciation</p>
                <p className="text-3xl font-light">
                  {salesData.total_sales_count > 1 ? (
                    ((salesData.most_recent_sale!.sale_price - salesData.previous_sales[salesData.previous_sales.length - 1]!.sale_price) /
                     salesData.previous_sales[salesData.previous_sales.length - 1]!.sale_price * 100).toFixed(1)
                  ) : '0'}%
                </p>
                <p className="text-xs opacity-60 mt-1">Since first sale</p>
              </div>
              <div>
                <p className="text-sm opacity-75">Market Activity</p>
                <p className="text-3xl font-light">
                  {salesData.years_on_market > 0 ?
                    (salesData.total_sales_count / salesData.years_on_market).toFixed(1) :
                    salesData.total_sales_count
                  }
                </p>
                <p className="text-xs opacity-60 mt-1">Sales per year</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}