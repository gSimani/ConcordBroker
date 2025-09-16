import { PropertyData } from '@/hooks/usePropertyData'
import { DollarSign, Home, Building, Calendar, TrendingUp, Clock, TreePine, Ruler } from 'lucide-react'

interface OverviewTabProps {
  data: PropertyData
}

export function OverviewTab({ data }: OverviewTabProps) {
  const { bcpaData, lastSale, investmentScore, opportunities, riskFactors } = data

  // Format currency
  const formatCurrency = (value?: number) => {
    if (!value) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  return (
    <div className="grid grid-cols-3 gap-8">
      {/* Left Column - Property & Investment */}
      <div className="space-y-6">
        <div className="card-executive animate-elegant">
          <div className="elegant-card-header">
            <h3 className="elegant-card-title gold-accent">
              Property Location
            </h3>
          </div>
          <div className="pt-4">
            <div className="space-y-2">
              <div>
                <p className="text-lg font-medium text-navy">
                  {bcpaData?.property_address_full || 'No Street Address'}
                </p>
                <p className="text-sm text-gray-elegant">
                  Fort Lauderdale, FL
                </p>
              </div>
              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-gold">
                <div>
                  <p className="text-xs uppercase tracking-wider text-gray-elegant">Property Type</p>
                  <p className="text-sm font-medium text-navy">{bcpaData?.property_use_code || 'Unknown'}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wider text-gray-elegant">Year Built</p>
                  <p className="text-sm font-medium text-navy">{bcpaData?.year_built || 'Unknown'}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="card-executive animate-elegant">
          <div className="elegant-card-header">
            <h3 className="elegant-card-title gold-accent flex items-center">
              <div className="p-2 rounded-lg mr-3" style={{background: '#2c3e50'}}>
                <DollarSign className="w-4 h-4 text-white" />
              </div>
              Investment Analysis
            </h3>
          </div>
          <div className="pt-4">
            <div className="text-center p-4 rounded-lg mb-4" style={{background: 'linear-gradient(135deg, #f4e5c2 0%, #fff 100%)'}}>
              <div className="text-3xl font-light text-gold mb-2">
                {investmentScore}/100
              </div>
              <p className="text-sm text-gray-elegant uppercase tracking-wider">Investment Score</p>
            </div>
            
            {/* Opportunities */}
            {opportunities.length > 0 && (
              <div className="mb-4">
                <h4 className="elegant-heading text-navy mb-3 text-sm uppercase tracking-wider">✅ Opportunities</h4>
                <ul className="space-y-2">
                  {opportunities.slice(0, 2).map((opp, index) => (
                    <li key={index} className="text-xs elegant-text bg-green-50 p-2 rounded border-l-2 border-gold">
                      {opp}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Risk Factors */}
            {riskFactors.length > 0 && (
              <div>
                <h4 className="elegant-heading text-navy mb-3 text-sm uppercase tracking-wider">⚠️ Risk Factors</h4>
                <ul className="space-y-2">
                  {riskFactors.slice(0, 2).map((risk, index) => (
                    <li key={index} className="text-xs elegant-text bg-orange-50 p-2 rounded border-l-2 border-orange-400">
                      {risk}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Middle Column - Valuation & Details */}
      <div className="space-y-4">
        <div className="card-executive animate-elegant">
          <div className="elegant-card-header">
            <h3 className="elegant-card-title flex items-center">
              <DollarSign className="w-4 h-4 mr-2 text-gold" />
              Valuation Summary
            </h3>
          </div>
          <div className="pt-4">
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs uppercase tracking-wider text-gray-elegant">Market Value</p>
                  <p className="text-xl font-light text-navy">
                    {bcpaData?.market_value ? formatCurrency(parseInt(bcpaData.market_value)) : 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wider text-gray-elegant">Assessed Value</p>
                  <p className="text-xl font-light text-navy">
                    {bcpaData?.assessed_value ? formatCurrency(parseInt(bcpaData.assessed_value)) : 'N/A'}
                  </p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3 pt-3 border-t border-gold">
                <div className="p-2 rounded-lg hover:scale-105 transition-transform cursor-pointer bg-gold-light">
                  <p className="text-xs mb-1 uppercase tracking-wider text-gray-elegant">Land Value</p>
                  <p className="font-medium text-navy">{bcpaData?.land_value ? formatCurrency(parseInt(bcpaData.land_value)) : 'N/A'}</p>
                </div>
                <div className="p-2 rounded-lg hover:scale-105 transition-transform cursor-pointer bg-gray-light">
                  <p className="text-xs mb-1 uppercase tracking-wider text-gray-elegant">Building Value</p>
                  <p className="font-medium text-navy">
                    {bcpaData?.building_value ? formatCurrency(parseInt(bcpaData.building_value)) : 'N/A'}
                  </p>
                </div>
              </div>
              {lastSale && (
                <div className="flex items-center pt-2 border-t border-gray-light">
                  <TrendingUp className="w-4 h-4 mr-2 text-blue-500" />
                  <span className="text-sm elegant-text text-navy">
                    Last Sale: {formatCurrency(parseInt(lastSale.sale_price || '0'))}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="card-executive animate-elegant">
          <div className="elegant-card-header">
            <h3 className="elegant-card-title flex items-center">
              <div className="p-2 bg-navy rounded-lg mr-3">
                <Building className="w-4 h-4 text-white" />
              </div>
              Property Details
            </h3>
          </div>
          <div className="pt-4">
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="p-2 rounded-lg hover:bg-gray-50 transition-all group">
                  <p className="text-xs mb-1 flex items-center uppercase tracking-wider text-gray-elegant">
                    <Home className="w-3 h-3 mr-1" />
                    Living Area
                  </p>
                  <p className="text-lg font-light text-navy">
                    {bcpaData?.living_area ? `${parseInt(bcpaData.living_area).toLocaleString()} sqft` : 'N/A'}
                  </p>
                </div>
                <div className="p-2 rounded-lg hover:bg-gray-50 transition-all group">
                  <p className="text-xs mb-1 flex items-center uppercase tracking-wider text-gray-elegant">
                    <Calendar className="w-3 h-3 mr-1" />
                    Year Built
                  </p>
                  <p className="text-lg font-light text-navy">{bcpaData?.year_built || 'N/A'}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="p-2 rounded-lg hover:bg-gray-50 transition-all group">
                  <p className="text-xs mb-1 flex items-center uppercase tracking-wider text-gray-elegant">
                    <TreePine className="w-3 h-3 mr-1" />
                    Lot Size
                  </p>
                  <p className="text-lg font-light text-navy">
                    {bcpaData?.lot_size ? `${parseInt(bcpaData.lot_size).toLocaleString()} sqft` : 'N/A'}
                  </p>
                </div>
                <div className="p-2 rounded-lg hover:bg-gray-50 transition-all group">
                  <p className="text-xs mb-1 flex items-center uppercase tracking-wider text-gray-elegant">
                    <Building className="w-3 h-3 mr-1" />
                    Bed/Bath
                  </p>
                  <p className="text-lg font-light text-navy">{bcpaData?.bedrooms || '?'} / {bcpaData?.bathrooms || '?'}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right Column - Recent Sale & Owner */}
      <div className="space-y-4">
        <div className="card-executive animate-elegant">
          <div className="elegant-card-header">
            <h3 className="elegant-card-title flex items-center">
              <div className="p-2 bg-gold rounded-lg mr-3">
                <Calendar className="w-4 h-4 text-navy" />
              </div>
              Most Recent Sale
            </h3>
          </div>
          <div className="pt-4">
            {lastSale ? (
              <div className="space-y-3">
                <div className="text-center p-3 rounded-lg bg-gray-light">
                  <p className="text-3xl font-light text-navy">
                    {lastSale?.sale_price ? formatCurrency(parseInt(lastSale.sale_price)) : 'N/A'}
                  </p>
                  <p className="text-sm mt-1 text-gray-elegant">
                    <Clock className="w-3 h-3 inline mr-1" />
                    {lastSale?.sale_date ? new Date(lastSale.sale_date).toLocaleDateString() : 'N/A'}
                  </p>
                </div>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-xs uppercase tracking-wider text-gray-elegant">Type:</span>
                    <span className="text-sm font-medium badge-elegant text-navy">
                      {lastSale?.qualified_sale ? 'Qualified' : lastSale ? 'Unqualified' : 'N/A'}
                    </span>
                  </div>
                  {lastSale?.is_distressed && (
                    <div className="flex justify-between">
                      <span className="text-xs uppercase tracking-wider text-gray-elegant">Status:</span>
                      <span className="text-sm text-red-600">Distressed</span>
                    </div>
                  )}
                  {bcpaData?.market_value && (
                    <div className="flex justify-between">
                      <span className="text-xs uppercase tracking-wider text-gray-elegant">vs Market:</span>
                      <span className="text-sm font-medium text-navy">
                        {lastSale?.sale_price && bcpaData.market_value ? ((parseInt(lastSale.sale_price) / parseInt(bcpaData.market_value)) * 100).toFixed(0) + '%' : 'N/A'}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center py-4 text-gray-elegant">
                No recent sales recorded
              </div>
            )}
          </div>
        </div>

        <div className="card-executive animate-elegant">
          <div className="elegant-card-header">
            <h3 className="elegant-card-title gold-accent">
              Property Owner
            </h3>
          </div>
          <div className="pt-4">
            <div className="space-y-3">
              <div>
                <p className="text-lg font-light text-navy">{bcpaData?.owner_name || 'Unknown Owner'}</p>
                {bcpaData?.owner_address && (
                  <p className="text-sm text-gray-elegant">
                    {bcpaData.owner_address}
                  </p>
                )}
              </div>
              
              <div className="pt-3 border-t border-gold">
                <div className="flex items-center space-x-2">
                  {bcpaData?.homestead_exemption ? (
                    <span className="badge-elegant badge-gold text-xs">Homesteaded</span>
                  ) : (
                    <span className="badge-elegant badge-gray text-xs">Investment Property</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}