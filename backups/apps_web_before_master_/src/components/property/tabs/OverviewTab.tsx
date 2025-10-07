import { PropertyData } from '@/hooks/usePropertyData'
import { DollarSign, Home, Building, Calendar, TrendingUp, Clock, TreePine, Ruler, Info, ExternalLink, FileText } from 'lucide-react'
import { getUseCodeName, getUseCodeDescription } from '@/lib/useCodeMapping'
import { PropertyDataAnalyzer } from '@/utils/property-intelligence'
import { PropertyContactsNotes } from '../PropertyContactsNotes'
import { getDORUseCode, formatDORCode } from '@/utils/dorUseCodes'
import { Badge } from '@/components/ui/badge'

// Utility function to display bed/bath info based on property type (simpler version for Overview)
function getBedBathDisplay(bcpaData: any): string {
  const propertyUse = bcpaData?.propertyUse || bcpaData?.property_use || bcpaData?.property_use_code || bcpaData?.dor_uc;
  const buildingSqFt = bcpaData?.buildingSqFt || bcpaData?.building_sqft || bcpaData?.tot_lvg_area || bcpaData?.living_area || 0;
  const hasBuilding = buildingSqFt && buildingSqFt > 0;
  const bedrooms = bcpaData?.bedrooms;
  const bathrooms = bcpaData?.bathrooms;

  // Property use codes: 0=Vacant Land, 1-3=Residential, 4-7=Commercial, 8-9=Industrial, 10-12=Agricultural
  const propertyUseNum = parseInt(String(propertyUse || '0'));

  // For Vacant Land (no building)
  if (propertyUseNum === 0 || !hasBuilding) {
    return 'N/A';
  }

  // For Residential properties (use codes 1, 2, 3, and 4 for condos/townhomes)
  if (propertyUseNum >= 1 && propertyUseNum <= 4) {
    // If we have bedroom/bathroom data, show it
    if (bedrooms && bathrooms) {
      return `${bedrooms} / ${bathrooms}`;
    }
    // If no bed/bath data but has building, estimate based on square footage
    if (hasBuilding) {
      const estimatedBeds = Math.max(1, Math.floor(buildingSqFt / 500)); // Rough estimate: 500 sqft per bedroom
      const estimatedBaths = Math.max(1, Math.floor(estimatedBeds / 1.5)); // Rough ratio
      return `${estimatedBeds}* / ${estimatedBaths}*`;
    }
    return '- / -';
  }

  // For Non-residential properties
  return 'N/A (Commercial/Industrial)';
}

interface OverviewTabProps {
  data: PropertyData
}

export function OverviewTab({ data }: OverviewTabProps) {
  const { bcpaData, lastSale, investmentScore, opportunities, riskFactors } = data
  const propertyData = data // For accessing nested structure

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

  // Get investment grade based on score
  const getInvestmentGrade = (score: number) => {
    if (score >= 90) return { grade: 'A+', color: 'text-green-600', bg: 'bg-green-600' };
    if (score >= 80) return { grade: 'A', color: 'text-green-600', bg: 'bg-green-600' };
    if (score >= 70) return { grade: 'B', color: 'text-blue-600', bg: 'bg-blue-600' };
    if (score >= 60) return { grade: 'C', color: 'text-yellow-600', bg: 'bg-yellow-600' };
    if (score >= 50) return { grade: 'D', color: 'text-orange-600', bg: 'bg-orange-600' };
    return { grade: 'F', color: 'text-red-600', bg: 'bg-red-600' };
  };

  // Helper function to get tax values with fallback from multiple sources
  const getTaxValue = (fieldName: string) => {
    // Check both API format (camelCase) and database format (snake_case)
    const apiField = fieldName.replace(/_([a-z])/g, (match, letter) => letter.toUpperCase());
    return bcpaData?.[fieldName] || bcpaData?.[apiField] || 0;
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
                  {propertyData?.address?.street || bcpaData?.property_address_full || 'No Street Address'}
                </p>
                <p className="text-sm text-gray-elegant">
                  {propertyData?.address?.city || 'Florida'}, {propertyData?.address?.state || 'FL'}
                </p>
              </div>
              {/* DOR Use Codes Section */}
              <div className="pt-3 border-t border-gold">
                <div className="flex items-center gap-2 mb-3">
                  <FileText className="w-4 h-4 text-gold" />
                  <p className="text-xs uppercase tracking-wider text-gray-elegant">Florida DOR Land Use Classification</p>
                </div>

                {(() => {
                  const dorCode = propertyData?.characteristics?.dor_uc || bcpaData?.dor_uc || bcpaData?.DOR_UC;
                  const paCode = propertyData?.characteristics?.pa_uc || bcpaData?.pa_uc || bcpaData?.PA_UC;
                  const dorUseCode = getDORUseCode(dorCode);

                  return (
                    <div className="space-y-3">
                      {/* Primary DOR Use Code */}
                      {dorUseCode && (
                        <div className="bg-gray-50 rounded-lg p-3">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <Badge className={`${dorUseCode.bgColor} ${dorUseCode.color} ${dorUseCode.borderColor} font-medium mb-1`}>
                                {dorUseCode.category}
                              </Badge>
                              {dorUseCode.subcategory && (
                                <Badge variant="outline" className="ml-2 text-xs">
                                  {dorUseCode.subcategory}
                                </Badge>
                              )}
                            </div>
                            <span className="text-sm font-mono text-gray-600">
                              Code: {formatDORCode(dorCode)}
                            </span>
                          </div>
                          <p className="text-sm text-navy font-medium">
                            {dorUseCode.description}
                          </p>
                        </div>
                      )}

                      {/* Property Appraiser Use Code if present */}
                      {paCode && (
                        <div className="bg-blue-50 rounded-lg p-2">
                          <div className="flex items-center justify-between">
                            <span className="text-xs uppercase tracking-wider text-blue-700">
                              PA Use Code
                            </span>
                            <span className="text-sm font-mono text-blue-900">
                              {String(paCode).padStart(2, '0')}
                            </span>
                          </div>
                          <p className="text-xs text-blue-600 mt-1">
                            County-specific classification
                          </p>
                        </div>
                      )}

                      {/* Fallback to old mapping if no DOR code */}
                      {!dorUseCode && (
                        <div>
                          <p className="text-sm font-medium text-navy">
                            {getUseCodeName(propertyData?.characteristics?.use_code || bcpaData?.property_use_code || '001')}
                          </p>
                          <p className="text-xs text-gray-elegant">
                            {getUseCodeDescription(propertyData?.characteristics?.use_code || bcpaData?.property_use_code || '001')}
                          </p>
                        </div>
                      )}
                    </div>
                  );
                })()}
              </div>

              <div className="grid grid-cols-2 gap-2 pt-3 border-t border-gray-200">
                <div>
                  <p className="text-xs uppercase tracking-wider text-gray-elegant">Year Built</p>
                  <p className="text-sm font-medium text-navy">{propertyData?.characteristics?.year_built || bcpaData?.year_built || bcpaData?.act_yr_blt || 'Unknown'}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wider text-gray-elegant">Living Area</p>
                  <p className="text-sm font-medium text-navy">
                    {bcpaData?.tot_lvg_area ? `${bcpaData.tot_lvg_area.toLocaleString()} sqft` : 'N/A'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="card-executive animate-elegant">
          <div className="elegant-card-header">
            <h3 className="elegant-card-title gold-accent flex items-center">
              <div className={`p-2 rounded-lg mr-3 ${getInvestmentGrade(investmentScore).bg}`}>
                <span className="text-white font-bold text-lg">
                  {getInvestmentGrade(investmentScore).grade}
                </span>
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
                    {propertyData?.values?.market_value ? formatCurrency(propertyData.values.market_value) :
                     (getTaxValue('market_value') ? formatCurrency(getTaxValue('market_value')) : 'N/A')}
                  </p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wider text-gray-elegant">Assessed Value</p>
                  <p className="text-xl font-light text-navy">
                    {propertyData?.values?.assessed_value ? formatCurrency(propertyData.values.assessed_value) :
                     (getTaxValue('assessed_value') ? formatCurrency(getTaxValue('assessed_value')) : 'N/A')}
                  </p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3 pt-3 border-t border-gold">
                <div className="p-2 rounded-lg hover:scale-105 transition-transform cursor-pointer bg-gold-light">
                  <p className="text-xs mb-1 uppercase tracking-wider text-gray-elegant">Land Value</p>
                  <p className="font-medium text-navy">
                    {propertyData?.values?.land_value ? formatCurrency(propertyData.values.land_value) :
                     (getTaxValue('land_value') ? formatCurrency(getTaxValue('land_value')) : 'N/A')}
                  </p>
                </div>
                <div className="p-2 rounded-lg hover:scale-105 transition-transform cursor-pointer bg-gray-light">
                  <p className="text-xs mb-1 uppercase tracking-wider text-gray-elegant">Building Value</p>
                  <p className="font-medium text-navy">
                    {propertyData?.values?.building_value ? formatCurrency(propertyData.values.building_value) :
                     (getTaxValue('building_value') ? formatCurrency(getTaxValue('building_value')) : 'N/A')}
                  </p>
                </div>
              </div>
              {(propertyData?.sales?.last_sale_price > 1000 || propertyData?.sales?.sale_price1 > 1000 || lastSale) && (
                <div className="flex items-center pt-2 border-t border-gray-light">
                  <TrendingUp className="w-4 h-4 mr-2 text-blue-500" />
                  <span className="text-sm elegant-text text-navy">
                    Last Sale: {propertyData?.sales?.last_sale_price > 1000 ?
                      formatCurrency(propertyData.sales.last_sale_price) :
                      (propertyData?.sales?.sale_price1 > 1000 ?
                        formatCurrency(propertyData.sales.sale_price1) :
                        (lastSale ? formatCurrency(parseInt(lastSale.sale_price || '0')) : 'N/A'))}
                  </span>
                  {(propertyData?.sales?.last_sale_date ||
                    (propertyData?.sales?.sale_year1 && propertyData?.sales?.sale_month1)) && (
                    <span className="text-sm text-gray-600 ml-2">
                      ({propertyData.sales.last_sale_date ?
                        new Date(propertyData.sales.last_sale_date).getFullYear() :
                        propertyData.sales.sale_year1})
                    </span>
                  )}
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
                <div className="p-2 rounded-lg hover:bg-gray-50 transition-all group relative">
                  <p className="text-xs mb-1 flex items-center uppercase tracking-wider text-gray-elegant">
                    <Home className="w-3 h-3 mr-1" />
                    Living Area
                  </p>
                  {(() => {
                    const analysis = PropertyDataAnalyzer.analyzeLivingArea(bcpaData);
                    return (
                      <>
                        <p className="text-lg font-light text-navy">
                          {analysis.value || 'N/A'}
                        </p>
                        {analysis.reason && (
                          <div className="absolute bottom-full left-0 mb-1 hidden group-hover:block z-10">
                            <div className="bg-gray-900 text-white text-xs p-2 rounded shadow-lg whitespace-nowrap">
                              <Info className="w-3 h-3 inline mr-1" />
                              {analysis.reason}
                            </div>
                          </div>
                        )}
                      </>
                    );
                  })()}
                </div>
                <div className="p-2 rounded-lg hover:bg-gray-50 transition-all group relative">
                  <p className="text-xs mb-1 flex items-center uppercase tracking-wider text-gray-elegant">
                    <Calendar className="w-3 h-3 mr-1" />
                    Year Built
                  </p>
                  {(() => {
                    const analysis = PropertyDataAnalyzer.analyzeYearBuilt(bcpaData);
                    return (
                      <>
                        <p className="text-lg font-light text-navy">
                          {analysis.value || 'N/A'}
                        </p>
                        {analysis.reason && (
                          <div className="absolute bottom-full right-0 mb-1 hidden group-hover:block z-10">
                            <div className="bg-gray-900 text-white text-xs p-2 rounded shadow-lg whitespace-nowrap">
                              <Info className="w-3 h-3 inline mr-1" />
                              {analysis.reason}
                            </div>
                          </div>
                        )}
                      </>
                    );
                  })()}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="p-2 rounded-lg hover:bg-gray-50 transition-all group relative">
                  <p className="text-xs mb-1 flex items-center uppercase tracking-wider text-gray-elegant">
                    <TreePine className="w-3 h-3 mr-1" />
                    Lot Size
                  </p>
                  {(() => {
                    const analysis = PropertyDataAnalyzer.analyzeLotSize(bcpaData);
                    return (
                      <>
                        <p className="text-lg font-light text-navy">
                          {analysis.value || 'N/A'}
                        </p>
                        {analysis.reason && (
                          <div className="absolute bottom-full left-0 mb-1 hidden group-hover:block z-10">
                            <div className="bg-gray-900 text-white text-xs p-2 rounded shadow-lg whitespace-nowrap">
                              <Info className="w-3 h-3 inline mr-1" />
                              {analysis.reason}
                            </div>
                          </div>
                        )}
                      </>
                    );
                  })()}
                </div>
                <div className="p-2 rounded-lg hover:bg-gray-50 transition-all group relative">
                  <p className="text-xs mb-1 flex items-center uppercase tracking-wider text-gray-elegant">
                    <Building className="w-3 h-3 mr-1" />
                    Bed/Bath
                  </p>
                  {(() => {
                    const analysis = PropertyDataAnalyzer.analyzeBedBath(bcpaData);
                    return (
                      <>
                        <p className="text-lg font-light text-navy">
                          {analysis.value || 'N/A'}
                        </p>
                        {analysis.reason && (
                          <div className="absolute bottom-full right-0 mb-1 hidden group-hover:block z-10">
                            <div className="bg-gray-900 text-white text-xs p-2 rounded shadow-lg whitespace-nowrap">
                              <Info className="w-3 h-3 inline mr-1" />
                              {analysis.reason}
                            </div>
                          </div>
                        )}
                      </>
                    );
                  })()}
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
            {(() => {
              const saleAnalysis = PropertyDataAnalyzer.analyzeSaleData(bcpaData, lastSale);

              if (lastSale || saleAnalysis.saleInfo) {
                return (
                  <div className="space-y-3">
                    <div className="text-center p-3 rounded-lg bg-gray-light">
                      <p className="text-3xl font-light text-navy">
                        {lastSale?.sale_price ? formatCurrency(parseInt(lastSale.sale_price)) :
                         saleAnalysis.saleInfo ? saleAnalysis.saleInfo.split(' on ')[0] : 'N/A'}
                      </p>
                      <p className="text-sm mt-1 text-gray-elegant">
                        <Clock className="w-3 h-3 inline mr-1" />
                        {lastSale?.sale_date ? new Date(lastSale.sale_date).toLocaleDateString() :
                         saleAnalysis.saleInfo ? saleAnalysis.saleInfo.split(' on ')[1] : 'N/A'}
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
                      {/* Add Official Record Link */}
                      {saleAnalysis.recordLink && (
                        <div className="pt-2 mt-2 border-t border-gold">
                          <a
                            href={saleAnalysis.recordLink}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center justify-center text-xs font-medium text-blue-600 hover:text-blue-800 transition-colors"
                          >
                            <ExternalLink className="w-3 h-3 mr-1" />
                            View Official Record
                            {lastSale?.book && lastSale?.page && (
                              <span className="ml-1 text-gray-500">
                                (Book {lastSale.book}/Page {lastSale.page})
                              </span>
                            )}
                            {lastSale?.cin && (
                              <span className="ml-1 text-gray-500">
                                (CIN: {lastSale.cin})
                              </span>
                            )}
                          </a>
                        </div>
                      )}
                    </div>
                  </div>
                );
              } else {
                return (
                  <div className="text-center py-4">
                    <p className="text-gray-elegant">
                      {saleAnalysis.reason || 'No recent sales recorded'}
                    </p>
                    {bcpaData?.owner_name && bcpaData?.owner_name !== 'UNKNOWN' && (
                      <p className="text-xs text-gray-500 mt-2">
                        <Info className="w-3 h-3 inline mr-1" />
                        {saleAnalysis.reason}
                      </p>
                    )}
                  </div>
                );
              }
            })()}
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

      {/* Property Notes & Contacts Section - Full width below the grid */}
      <div className="mt-8">
        <PropertyContactsNotes
          parcelId={propertyData?.parcel_id || bcpaData?.parcel_id || ''}
          propertyAddress={propertyData?.address?.full || propertyData?.address?.street || 'Unknown Address'}
        />
      </div>
    </div>
  )
}