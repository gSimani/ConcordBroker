import React from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import '@/styles/elegant-property.css';
import {
  MapPin,
  DollarSign,
  User,
  Home,
  TrendingUp,
  TrendingDown,
  Calendar,
  Eye,
  Star,
  MoreVertical,
  Phone,
  Mail,
  Building,
  Square,
  Tag,
  CheckSquare,
  AlertTriangle,
  ExternalLink
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useSalesData, getLatestSaleInfo } from '@/hooks/useSalesData';
import { getUseCodeInfo, getPropertyCategory as getDORCategory, getUseCodeShortName, getUseCodeDescription } from '@/lib/dorUseCodes';
import { useSunbizMatching, getSunbizSearchUrl } from '@/hooks/useSunbizMatching';

// New function to categorize properties based on actual property_use numeric codes
export const getPropertyCategoryFromCode = (propertyUse?: string | number, propertyUseDesc?: string): string => {
  // Convert to string for comparison
  const code = String(propertyUse || '').trim();

  // Map based on actual codes found in database analysis
  if (code === '0' || code === '00') return 'Vacant Land';
  if (code === '1' || code === '01') return 'Residential';
  if (code === '2' || code === '02') return 'Residential';
  if (code === '3' || code === '03') return 'Residential';
  if (code === '4' || code === '04') return 'Commercial';  // Most properties have code '4'
  if (code === '5' || code === '05') return 'Commercial';
  if (code === '6' || code === '06') return 'Commercial';
  if (code === '7' || code === '07') return 'Commercial';
  if (code === '8' || code === '08') return 'Industrial';
  if (code === '9' || code === '09') return 'Industrial';
  if (code === '10') return 'Agricultural';
  if (code === '11') return 'Agricultural';
  if (code === '12') return 'Agricultural';

  // Government codes (90-99)
  if (code.startsWith('9')) return 'Government';

  // Try to categorize by description if available
  if (propertyUseDesc) {
    const desc = propertyUseDesc.toUpperCase();
    if (desc.includes('RESIDENTIAL') || desc.includes('SINGLE') || desc.includes('FAMILY') || desc.includes('CONDO')) {
      return 'Residential';
    }
    if (desc.includes('COMMERCIAL') || desc.includes('RETAIL') || desc.includes('OFFICE') || desc.includes('STORE')) {
      return 'Commercial';
    }
    if (desc.includes('INDUSTRIAL') || desc.includes('WAREHOUSE') || desc.includes('MANUFACTURING')) {
      return 'Industrial';
    }
    if (desc.includes('AGRICULTURAL') || desc.includes('FARM') || desc.includes('GROVE')) {
      return 'Agricultural';
    }
    if (desc.includes('GOVERNMENT') || desc.includes('PUBLIC') || desc.includes('MUNICIPAL')) {
      return 'Government';
    }
    if (desc.includes('VACANT') || desc.includes('UNDEVELOPED')) {
      return 'Vacant Land';
    }
  }

  return 'Unknown';
};

interface MiniPropertyCardProps {
  parcelId: string;
  data: {
    phy_addr1?: string;
    phy_city?: string;
    phy_zipcd?: string;
    own_name?: string;
    owner_name?: string;   // Alternative owner name field
    jv?: number;           // Just (appraised) value
    tv_sd?: number;        // Taxable value
    lnd_val?: number;      // Land value
    tot_lvg_area?: number; // Building square feet
    lnd_sqfoot?: number;   // Land square feet
    act_yr_blt?: number;   // Year built
    dor_uc?: string;       // Department of Revenue Use Code (legacy)
    propertyUse?: string | number;  // New property_use field from database
    propertyType?: string | number; // Same as propertyUse
    propertyUseDesc?: string;       // property_use_desc from database
    landUseCode?: string;           // land_use_code from database
    sale_prc1?: number;    // Last sale price
    sale_yr1?: number;     // Last sale year
    sale_date?: string;    // Last sale date (YYYY-MM-DD)
    sale_month?: number;   // Last sale month (1-12)
    property_type?: string; // Property type description
    has_tax_certificates?: boolean; // Tax certificate indicator
    certificate_count?: number;     // Number of tax certificates
    // Tax deed auction details
    auction_date?: string;          // Auction date (YYYY-MM-DD)
    opening_bid?: number;           // Starting bid amount
    tax_deed_number?: string;       // Tax deed number
    auction_url?: string;           // Direct link to auction
    total_certificate_amount?: number; // Total certificate amount
  };
  onClick?: () => void;
  variant?: 'grid' | 'list';
  showQuickActions?: boolean;
  isWatched?: boolean;
  hasNotes?: boolean;
  priority?: 'low' | 'medium' | 'high';
  isSelected?: boolean;
  onToggleSelection?: () => void;
}

// Get property category based on DOR use code
export const getPropertyCategory = (useCode?: string, propertyType?: string): string => {
  const category = getDORCategory(useCode);
  if (category !== 'UNKNOWN') {
    // Format category for display
    return category.charAt(0) + category.slice(1).toLowerCase();
  }

  // Fallback to property type description if no use code
  if (propertyType) {
    const lowerType = propertyType.toLowerCase();
    if (lowerType.includes('residential') || lowerType.includes('single family') ||
        lowerType.includes('condo') || lowerType.includes('home')) {
      return 'Residential';
    }
    if (lowerType.includes('commercial') || lowerType.includes('office') ||
        lowerType.includes('retail') || lowerType.includes('store')) {
      return 'Commercial';
    }
    if (lowerType.includes('industrial') || lowerType.includes('warehouse') ||
        lowerType.includes('manufacturing')) {
      return 'Industrial';
    }
    if (lowerType.includes('agricultural') || lowerType.includes('farm')) {
      return 'Agricultural';
    }
    if (lowerType.includes('vacant')) {
      return 'Vacant Land';
    }
  }
  return 'Unknown';
};

// Property type badges with colors
const getPropertyTypeBadge = (useCode?: string, propertyType?: string, ownerName?: string, justValue?: number, hasAddress?: boolean, propertyUse?: string | number, propertyUseDesc?: string) => {
  // First try to get category from the new property_use field
  let category = getPropertyCategoryFromCode(propertyUse, propertyUseDesc);

  // If that doesn't work, fall back to old method
  if (category === 'Unknown') {
    category = getPropertyCategory(useCode, propertyType);
  }

  // Since DOR codes are not available, categorize based on owner names and other data
  if (ownerName) {
    const ownerUpper = ownerName.toUpperCase();

    // Government/Public entities
    if (ownerUpper.includes('TRUSTEE') || ownerUpper.includes('BRD OF') ||
        ownerUpper.includes('BOARD OF') || ownerUpper.includes('STATE OF') ||
        ownerUpper.includes('COUNTY') || ownerUpper.includes('CITY OF') ||
        ownerUpper.includes('TIITF')) {
      category = 'Government';
    }
    // Religious institutions
    else if (ownerUpper.includes('CHURCH') || ownerUpper.includes('BAPTIST') ||
             ownerUpper.includes('METHODIST') || ownerUpper.includes('CATHOLIC') ||
             ownerUpper.includes('SYNAGOGUE') || ownerUpper.includes('TEMPLE') ||
             ownerUpper.includes('MOSQUE') || ownerUpper.includes('EPISCOPAL') ||
             ownerUpper.includes('LUTHERAN') || ownerUpper.includes('PRESBYTERIAN')) {
      category = 'Religious';
    }
    // Conservation/Environmental
    else if (ownerUpper.includes('CONSERVANCY') || ownerUpper.includes('NATURE') ||
             ownerUpper.includes('FORESTRY') || ownerUpper.includes('PARK') ||
             ownerUpper.includes('PRESERVE') || ownerUpper.includes('WILDLIFE') ||
             ownerUpper.includes('AG FORESTRY')) {
      category = 'Conservation';
    }
    // Commercial entities
    else if (ownerUpper.includes('CORP') || ownerUpper.includes('LLC') ||
             ownerUpper.includes('INC') || ownerUpper.includes('COMPANY') ||
             ownerUpper.includes('PROPERTIES') || ownerUpper.includes('ENTERPRISES') ||
             ownerUpper.includes('DEVELOPMENT') || ownerUpper.includes('INVESTMENTS')) {
      category = 'Commercial';
    }
    // Industrial
    else if (ownerUpper.includes('MANUFACTURING') || ownerUpper.includes('INDUSTRIAL') ||
             ownerUpper.includes('WAREHOUSE') || ownerUpper.includes('LOGISTICS') ||
             ownerUpper.includes('DISTRIBUTION') || ownerUpper.includes('FACTORY')) {
      category = 'Industrial';
    }
    // Agricultural
    else if (ownerUpper.includes('FARM') || ownerUpper.includes('RANCH') ||
             ownerUpper.includes('AGRICULTURE') || ownerUpper.includes('GROVE') ||
             ownerUpper.includes('NURSERY') || ownerUpper.includes('AG ')) {
      category = 'Agricultural';
    }
    // Residential - individual names with addresses
    else if (hasAddress && ownerUpper.includes(' ') && ownerUpper.length > 5 &&
             !ownerUpper.includes('TRUSTEE') && !ownerUpper.includes('CHURCH')) {
      category = 'Residential';
    }
    // Vacant/Special - everything else with value
    else if (justValue && justValue > 0) {
      category = 'Vacant/Special';
    }
  }
  const shortName = getUseCodeShortName(useCode);
  const useCodeInfo = getUseCodeInfo(useCode);

  // Return both category badge and detailed use badge
  return (
    <div className="flex items-center flex-wrap gap-1.5">
      {/* Main category badge */}
      {category === 'Residential' && (
        <Badge className="bg-green-100 text-green-800 border-green-200 font-medium">
          Residential
        </Badge>
      )}
      {category === 'Commercial' && (
        <Badge className="bg-blue-100 text-blue-800 border-blue-200 font-medium">
          Commercial
        </Badge>
      )}
      {category === 'Industrial' && (
        <Badge className="bg-orange-100 text-orange-800 border-orange-200 font-medium">
          Industrial
        </Badge>
      )}
      {category === 'Agricultural' && (
        <Badge className="bg-yellow-100 text-yellow-800 border-yellow-200 font-medium">
          Agricultural
        </Badge>
      )}
      {category === 'Vacant Land' && (
        <Badge className="bg-gray-100 text-gray-800 border-gray-200 font-medium">
          Vacant Land
        </Badge>
      )}
      {category === 'Institutional' && (
        <Badge className="bg-purple-100 text-purple-800 border-purple-200 font-medium">
          Institutional
        </Badge>
      )}
      {category === 'Governmental' && (
        <Badge className="bg-indigo-100 text-indigo-800 border-indigo-200 font-medium">
          Governmental
        </Badge>
      )}
      {category === 'Miscellaneous' && (
        <Badge className="bg-gray-100 text-gray-800 border-gray-200 font-medium">
          Miscellaneous
        </Badge>
      )}
      {category === 'Unknown' && (
        <Badge className="bg-gray-100 text-gray-600 border-gray-200 font-medium">
          Unknown
        </Badge>
      )}
      {category === 'Religious' && (
        <Badge className="bg-purple-100 text-purple-800 border-purple-200 font-medium">
          Religious
        </Badge>
      )}
      {category === 'Government' && (
        <Badge className="bg-red-100 text-red-800 border-red-200 font-medium">
          Government
        </Badge>
      )}
      {category === 'Conservation' && (
        <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200 font-medium">
          Conservation
        </Badge>
      )}
      {category === 'Vacant/Special' && (
        <Badge className="bg-amber-100 text-amber-800 border-amber-200 font-medium">
          Vacant/Special
        </Badge>
      )}

      {/* Sub-use type badge - showing DOR code and specific type */}
      {shortName && shortName !== 'Unknown' && useCodeInfo && (
        <Badge variant="outline" className="text-xs" title={useCodeInfo.description}>
          {useCodeInfo.code}: {shortName}
        </Badge>
      )}
    </div>
  );
};

export const MiniPropertyCard = React.memo(function MiniPropertyCard({
  parcelId,
  data,
  onClick,
  variant = 'grid',
  showQuickActions = true,
  isWatched = false,
  hasNotes = false,
  priority,
  isSelected = false,
  onToggleSelection
}: MiniPropertyCardProps) {

  console.log('MiniPropertyCard data received:', data);
  console.log('ParcelId received:', parcelId);

  // Fetch sales data - automatically checks batch cache first (useBatchSalesData in PropertySearch)
  const { salesData } = useSalesData(parcelId);

  // Fetch Sunbiz matching data for this property
  const { bestMatch, hasMatches, loading: sunbizLoading } = useSunbizMatching(
    parcelId,
    data.owner_name || data.own_name
  );

  console.log('Sales data for parcel', parcelId, ':', salesData);
  console.log('Sunbiz match for parcel', parcelId, ':', bestMatch);

  // Get latest sale info to augment the property data (filters out sales ≤ $1,000)
  const latestSaleInfo = getLatestSaleInfo(salesData);

  console.log('Latest sale info for parcel', parcelId, ':', latestSaleInfo);

  // Combine property data with latest qualifying sale info
  const enhancedData = {
    ...data,
    ...latestSaleInfo
  };

  // Enhanced debugging and real data integration
  console.log('🔍 MiniPropertyCard Debug - Parcel ID:', parcelId);
  console.log('📊 Raw data received:', data);
  console.log('💰 Sales data from useSalesData:', salesData);

  // Use real sales data if available, NO mock data
  if (salesData && Array.isArray(salesData) && salesData.length > 0) {
    const latestSale = salesData[0];
    const salePrice = typeof latestSale.sale_price === 'string' ? parseFloat(latestSale.sale_price) : latestSale.sale_price;
    if (salePrice && salePrice >= 1000) {
      enhancedData.sale_prc1 = salePrice;
      enhancedData.sale_yr1 = latestSale.sale_date ? new Date(latestSale.sale_date).getFullYear() : null;
      enhancedData.sale_date = latestSale.sale_date;
      enhancedData.sale_month = latestSale.sale_date ? new Date(latestSale.sale_date).getMonth() + 1 : null;
      console.log('✅ REAL SALES DATA found:', enhancedData.sale_prc1, enhancedData.sale_yr1, enhancedData.sale_month);
    }
  }
  // NO MOCK DATA - only show real data from database

  console.log('Enhanced data (simplified for debugging):', enhancedData);
  console.log('Original data jv field:', data.jv);
  console.log('Enhanced data jv field:', enhancedData.jv);

  // Helper function to get appraised value from multiple possible field names
  const getAppraisedValue = (data: any) => {
    const value = data.jv || data.just_value || data.appraised_value || data.market_value || data.assessed_value;
    console.log('getAppraisedValue checking fields:', {
      jv: data.jv,
      just_value: data.just_value,
      appraised_value: data.appraised_value,
      market_value: data.market_value,
      assessed_value: data.assessed_value,
      final_value: value
    });
    return value;
  };

  // Helper function to get taxable value from multiple possible field names
  const getTaxableValue = (data: any) => {
    return data.tv_sd || data.taxable_value || data.tax_value;
  };

  // Helper function to get land value
  const getLandValue = (data: any) => {
    return data.lnd_val || data.land_value;
  };

  const formatCurrency = (value?: number) => {
    console.log('MiniPropertyCard.formatCurrency called with value:', value, 'type:', typeof value);
    console.log('MiniPropertyCard.formatCurrency value is falsy:', !value);
    console.log('MiniPropertyCard.formatCurrency value == 0:', value == 0);
    console.log('MiniPropertyCard.formatCurrency value === 0:', value === 0);
    console.log('MiniPropertyCard.formatCurrency value === undefined:', value === undefined);
    console.log('MiniPropertyCard.formatCurrency value === null:', value === null);

    if (!value && value !== 0) return 'N/A';  // Only return N/A if value is actually falsy but not zero

    // Format as full currency with commas (no abbreviation)
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatArea = (sqft?: number) => {
    if (!sqft) return 'N/A';
    return `${sqft.toLocaleString()} sqft`;
  };

  const formatSaleDate = (saleDate?: string, saleYear?: number, saleMonth?: number) => {
    if (saleDate) {
      const date = new Date(saleDate);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        year: 'numeric'
      });
    } else if (saleYear && saleMonth) {
      const date = new Date(saleYear, saleMonth - 1);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        year: 'numeric'
      });
    } else if (saleYear) {
      return saleYear.toString();
    }
    return 'N/A';
  };

  // Format address for display
  const formatAddress = () => {
    // Check if property has a valid street address
    if (!data.phy_addr1 || data.phy_addr1 === '-' || data.phy_addr1 === 'No Street Address') {
      // For properties without street addresses, show owner address WITHOUT 'Owner:' prefix
      if (data.owner_addr1 && data.owner_addr1 !== '-') {
        return data.owner_addr1;
      }
      // For government properties, use a cleaner format
      if (data.owner_name && (data.owner_name.includes('TRUSTEE') || data.owner_name.includes('BRD OF'))) {
        return 'No Street Address';
      }
      // Default for properties without addresses
      return 'Address Not Available';
    }
    return data.phy_addr1;
  };

  // Get property category with better defaults
  const getPropertyCategoryDisplay = () => {
    // First try the new property_use categorization
    let category = getPropertyCategoryFromCode(data.propertyUse, data.propertyUseDesc);

    // Fall back to old method if needed
    if (category === 'Unknown') {
      category = getPropertyCategory(data.dor_uc, data.property_type);
    }
    // For government/institutional properties, use better categorization
    if (data.owner_name) {
      const ownerUpper = data.owner_name.toUpperCase();
      if (ownerUpper.includes('CHURCH') || ownerUpper.includes('BAPTIST') || ownerUpper.includes('METHODIST')) {
        return 'Religious';
      }
      if (ownerUpper.includes('TRUSTEE') || ownerUpper.includes('BRD OF') || ownerUpper.includes('BOARD OF')) {
        return 'Government';
      }
      if (ownerUpper.includes('CONSERVANCY') || ownerUpper.includes('NATURE') || ownerUpper.includes('FORESTRY')) {
        return 'Conservation';
      }
    }
    // If still unknown, check assessed value for hints
    if (category === 'Unknown' && data.jv) {
      // Properties with value are likely vacant land or special use
      return 'Vacant/Special';
    }
    return category;
  };

  // Grid variant - Elegant card design
  if (variant === 'grid') {
    return (
      <div 
        className={`
          elegant-card hover-lift cursor-pointer animate-in
          ${priority === 'high' ? 'ring-2 ring-red-500' : ''}
          ${priority === 'medium' ? 'ring-2 ring-yellow-500' : ''}
          ${isSelected ? 'ring-2 ring-yellow-400 bg-yellow-50/30' : ''}
        `}
        onClick={onClick}
      >
        {/* Status indicators and Selection */}
        <div className="absolute top-3 right-3 flex items-center space-x-2">
          {isWatched && (
            <div className="p-1.5 rounded-full" style={{background: 'rgba(212, 175, 55, 0.1)'}}>
              <Star className="w-3 h-3 fill-current" style={{color: '#d4af37'}} />
            </div>
          )}
          {hasNotes && (
            <div className="p-1.5 rounded-full" style={{background: 'rgba(52, 152, 219, 0.1)'}}>
              <span className="text-xs font-bold" style={{color: '#3498db'}}>N</span>
            </div>
          )}
          {onToggleSelection && (
            <div 
              className="hover:bg-gray-100 p-1 rounded z-10"
              onClick={(e) => {
                e.stopPropagation();
                onToggleSelection();
              }}
            >
              {isSelected ? (
                <CheckSquare className="w-4 h-4" style={{color: '#d4af37'}} />
              ) : (
                <Square className="w-4 h-4" style={{color: '#95a5a6'}} />
              )}
            </div>
          )}
        </div>

        <div className="p-4">
          {/* Property Type/Usage Badge and Tax Certificate Indicator */}
          <div className="mb-2 flex items-center justify-between">
            {getPropertyTypeBadge(data.dor_uc, data.property_type, data.owner_name || data.own_name, getAppraisedValue(data), !!(data.phy_addr1 && data.phy_addr1 !== '-'), data.propertyUse, data.propertyUseDesc)}
            <div className="flex items-center space-x-1">
              {data.has_tax_certificates && (
                <Badge className="bg-orange-100 text-orange-800 border-orange-200 flex items-center space-x-1">
                  <AlertTriangle className="w-3 h-3" />
                  <span className="text-xs font-medium">
                    {data.certificate_count} Certificate{data.certificate_count && data.certificate_count > 1 ? 's' : ''}
                  </span>
                </Badge>
              )}
              {data.auction_date && (
                <Badge className="bg-red-100 text-red-800 border-red-200 flex items-center space-x-1">
                  <Calendar className="w-3 h-3" />
                  <span className="text-xs font-medium">Tax Deed Auction</span>
                </Badge>
              )}
            </div>
          </div>

          {/* Address */}
          <div className="mb-3">
            <div className="flex items-start space-x-2">
              <MapPin className="w-4 h-4 mt-0.5 flex-shrink-0" style={{color: '#95a5a6'}} />
              <div className="flex-1">
                <a
                  href={(() => {
                    // Determine the best address to use for Google Maps
                    if (data.phy_addr1 && data.phy_city && data.phy_addr1 !== '-' && data.phy_addr1 !== 'No Street Address') {
                      // Use property address if available
                      return `https://www.google.com/maps/search/${encodeURIComponent(
                        `${data.phy_addr1}, ${data.phy_city}, FL ${data.phy_zipcd || ''}`
                      )}`;
                    } else if (data.owner_addr1 && data.owner_addr1 !== '-') {
                      // Use owner address as fallback
                      return `https://www.google.com/maps/search/${encodeURIComponent(
                        `${data.owner_addr1}, FL`
                      )}`;
                    } else if (parcelId) {
                      // Search by parcel ID as last resort
                      return `https://www.google.com/maps/search/${encodeURIComponent(
                        `Parcel ${parcelId} Florida`
                      )}`;
                    }
                    return '#';
                  })()}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline"
                  onClick={(e) => {
                    // Only prevent click if we have no address at all
                    if (!data.phy_addr1 && !data.owner_addr1 && !parcelId) {
                      e.preventDefault();
                    } else {
                      e.stopPropagation();
                    }
                  }}
                >
                  <p className="font-semibold text-sm mb-0.5 hover:text-blue-600 transition-colors flex items-center gap-1" style={{color: '#2c3e50'}}>
                    {formatAddress()}
                    {(data.phy_addr1 || data.owner_addr1 || parcelId) && (
                      <ExternalLink className="w-3 h-3 opacity-50 hover:opacity-100" />
                    )}
                  </p>
                </a>
                <p className="text-xs" style={{color: '#7f8c8d'}}>
                  {data.phy_city || 'Unknown City'}, FL {data.phy_zipcd || ''}
                </p>
              </div>
            </div>
          </div>

          {/* Owner */}
          <div className="mb-3 pb-2" style={{borderBottom: '1px solid #ecf0f1'}}>
            <div className="flex items-start space-x-2">
              <User className="w-4 h-4 mt-0.5 flex-shrink-0" style={{color: '#95a5a6'}} />
              <div className="flex-1 min-w-0">
                <p className="text-xs uppercase tracking-wider mb-0.5" style={{color: '#95a5a6'}}>Owner</p>
                <p className="text-xs font-medium truncate" style={{color: '#2c3e50'}}>{data.owner_name || data.own_name || 'Owner Not Available'}</p>
              </div>
            </div>
          </div>

          {/* Key Metrics Grid */}
          <div className="space-y-1.5">
            {/* Last Sale or Tax Info */}
            {enhancedData.sale_prc1 && enhancedData.sale_prc1 > 1000 ? (
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-1">
                  <Tag className="w-3 h-3" style={{color: '#95a5a6'}} />
                  <span className="text-xs" style={{color: '#95a5a6'}}>Last Sold</span>
                </div>
                <div className="text-right">
                  <span className="font-semibold text-sm" style={{color: '#2c3e50'}}>{formatCurrency(enhancedData.sale_prc1)}</span>
                  <br />
                  <span className="text-xs font-medium" style={{color: '#7f8c8d'}}>
                    {formatSaleDate(enhancedData.sale_date, enhancedData.sale_yr1, enhancedData.sale_month)}
                  </span>
                </div>
              </div>
            ) : (
              // Show annual tax if no sale data
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-1">
                  <DollarSign className="w-3 h-3" style={{color: '#95a5a6'}} />
                  <span className="text-xs" style={{color: '#95a5a6'}}>Annual Tax</span>
                </div>
                <span className="font-semibold text-sm" style={{color: '#2c3e50'}}>
                  {formatCurrency(data.taxable_value ? data.taxable_value * 0.02 : 0)}
                </span>
              </div>
            )}

            {/* Appraised Value */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-1">
                <DollarSign className="w-3 h-3" style={{color: '#95a5a6'}} />
                <span className="text-xs" style={{color: '#95a5a6'}}>Appraised</span>
              </div>
              <span className="font-semibold text-sm" style={{color: '#d4af37'}}>{formatCurrency(getAppraisedValue(data))}</span>
            </div>

            {/* Assessed/SOH Value if different from appraised */}
            {data.assessed_value && data.assessed_value !== getAppraisedValue(data) && (
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-1">
                  <Home className="w-3 h-3" style={{color: '#95a5a6'}} />
                  <span className="text-xs" style={{color: '#95a5a6'}}>Assessed/SOH</span>
                </div>
                <span className="font-semibold text-sm" style={{color: '#27ae60'}}>{formatCurrency(data.assessed_value)}</span>
              </div>
            )}

            {/* Tax Certificate Amount */}
            {data.has_tax_certificates && data.total_certificate_amount && (
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-1">
                  <AlertTriangle className="w-3 h-3" style={{color: '#e67e22'}} />
                  <span className="text-xs" style={{color: '#e67e22'}}>Tax Liens</span>
                </div>
                <span className="font-semibold text-sm" style={{color: '#e67e22'}}>
                  {formatCurrency(data.total_certificate_amount)}
                </span>
              </div>
            )}

            {/* Tax Deed Auction Date */}
            {data.auction_date && (
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-1">
                  <Calendar className="w-3 h-3" style={{color: '#c0392b'}} />
                  <span className="text-xs" style={{color: '#c0392b'}}>Auction</span>
                </div>
                <span className="font-semibold text-sm" style={{color: '#c0392b'}}>
                  {new Date(data.auction_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                </span>
              </div>
            )}

            {/* Opening Bid Amount */}
            {data.opening_bid && (
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-1">
                  <DollarSign className="w-3 h-3" style={{color: '#8e44ad'}} />
                  <span className="text-xs" style={{color: '#8e44ad'}}>Starting Bid</span>
                </div>
                <span className="font-semibold text-sm" style={{color: '#8e44ad'}}>
                  {formatCurrency(data.opening_bid)}
                </span>
              </div>
            )}

            {/* Building Sq Ft */}
            {data.tot_lvg_area && (
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-1">
                  <Square className="w-3 h-3" style={{color: '#95a5a6'}} />
                  <span className="text-xs" style={{color: '#95a5a6'}}>Building</span>
                </div>
                <span className="font-semibold text-xs" style={{color: '#2c3e50'}}>{formatArea(data.tot_lvg_area)}</span>
              </div>
            )}

            {/* Land Sq Ft */}
            {data.lnd_sqfoot && (
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-1">
                  <Square className="w-3 h-3" style={{color: '#95a5a6'}} />
                  <span className="text-xs" style={{color: '#95a5a6'}}>Land</span>
                </div>
                <span className="font-semibold text-xs" style={{color: '#2c3e50'}}>{formatArea(data.lnd_sqfoot)}</span>
              </div>
            )}

            {/* Year Built */}
            {data.act_yr_blt && (
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-1">
                  <Calendar className="w-3 h-3" style={{color: '#95a5a6'}} />
                  <span className="text-xs" style={{color: '#95a5a6'}}>Built</span>
                </div>
                <span className="font-semibold text-xs" style={{color: '#2c3e50'}}>{data.act_yr_blt}</span>
              </div>
            )}
          </div>

          {/* Quick Actions */}
          {showQuickActions && (
            <div className="mt-3 pt-2 flex justify-between items-center" style={{borderTop: '1px solid #ecf0f1'}}>
              <Button
                size="sm"
                variant="ghost"
                className={`hover-lift h-6 px-2 ${hasMatches ? 'bg-green-50 text-green-700 border border-green-200' : ''}`}
                style={{color: hasMatches ? '#059669' : '#2c3e50'}}
                onClick={(e) => {
                  e.stopPropagation();
                  const ownerName = data.owner_name || data.own_name || '';
                  if (ownerName) {
                    const searchUrl = getSunbizSearchUrl(ownerName, bestMatch);
                    window.open(searchUrl, '_blank');
                  }
                }}
                title={
                  hasMatches && bestMatch
                    ? `Best match: ${bestMatch.company_name} (${bestMatch.confidence}% confidence)`
                    : 'Search Sunbiz for this owner'
                }
              >
                <Eye className="w-3 h-3 mr-1" />
                {hasMatches ? (
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                    View Match
                  </span>
                ) : (
                  'View Sunbiz'
                )}
              </Button>
              
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button 
                    size="sm" 
                    variant="ghost"
                    className="h-6 w-6 p-0 hover-lift"
                    style={{color: '#2c3e50'}}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <MoreVertical className="w-3 h-3" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem>
                    <Star className="w-4 h-4 mr-2" />
                    Watch
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    <Phone className="w-4 h-4 mr-2" />
                    Contact Owner
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    <Mail className="w-4 h-4 mr-2" />
                    Send Email
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          )}

          {/* Parcel ID */}
          <div className="mt-2 pt-1.5" style={{borderTop: '1px solid #ecf0f1'}}>
            <p className="text-xs" style={{color: '#95a5a6'}}>Parcel: {parcelId}</p>
          </div>
        </div>
      </div>
    );
  }

  // List variant - Horizontal layout
  return (
    <Card 
      className={`
        relative p-3 hover:shadow-md transition-all cursor-pointer
        ${priority === 'high' ? 'border-l-4 border-l-red-500' : ''}
        ${priority === 'medium' ? 'border-l-4 border-l-yellow-500' : ''}
        ${isSelected ? 'ring-2 ring-yellow-400 bg-yellow-50/30' : ''}
      `}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        {/* Left section - Address & Type */}
        <div className="flex items-center space-x-4 flex-1 min-w-0">
          <div className="flex-shrink-0">
            {data.dor_uc?.startsWith('0') && <Home className="w-5 h-5 text-green-600" />}
            {data.dor_uc?.startsWith('1') && <Building className="w-5 h-5 text-blue-600" />}
            {!data.dor_uc?.match(/^[01]/) && <MapPin className="w-5 h-5 text-gray-600" />}
          </div>
          
          <div className="min-w-0 flex-1">
            <div className="flex items-center space-x-2 mb-1">
              {getPropertyTypeBadge(data.dor_uc, data.property_type, data.owner_name || data.own_name, getAppraisedValue(data), !!(data.phy_addr1 && data.phy_addr1 !== '-'), data.propertyUse, data.propertyUseDesc)}
              <a
                href={(() => {
                  // Determine the best address to use for Google Maps
                  if (data.phy_addr1 && data.phy_city && data.phy_addr1 !== '-' && data.phy_addr1 !== 'No Street Address') {
                    // Use property address if available
                    return `https://www.google.com/maps/search/${encodeURIComponent(
                      `${data.phy_addr1}, ${data.phy_city}, FL ${data.phy_zipcd || ''}`
                    )}`;
                  } else if (data.owner_addr1 && data.owner_addr1 !== '-') {
                    // Use owner address as fallback
                    return `https://www.google.com/maps/search/${encodeURIComponent(
                      `${data.owner_addr1}, FL`
                    )}`;
                  } else if (parcelId) {
                    // Search by parcel ID as last resort
                    return `https://www.google.com/maps/search/${encodeURIComponent(
                      `Parcel ${parcelId} Florida`
                    )}`;
                  }
                  return '#';
                })()}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:underline truncate"
                onClick={(e) => {
                  // Only prevent click if we have no address at all
                  if (!data.phy_addr1 && !data.owner_addr1 && !parcelId) {
                    e.preventDefault();
                  } else {
                    e.stopPropagation();
                  }
                }}
              >
                <p className="font-semibold text-sm truncate hover:text-blue-600 transition-colors flex items-center gap-1">
                  {formatAddress()}
                  {(data.phy_addr1 || data.owner_addr1 || parcelId) && (
                    <ExternalLink className="w-3 h-3 opacity-50 hover:opacity-100 flex-shrink-0" />
                  )}
                </p>
              </a>
            </div>
            <p className="text-xs text-gray-500">
              {data.phy_city || 'Unknown City'}, FL {data.phy_zipcd || ''} • Parcel: {parcelId}
            </p>
          </div>
        </div>

        {/* Middle section - Owner */}
        <div className="px-4 min-w-0 flex-1 max-w-xs">
          <p className="text-xs text-gray-500 mb-1">Owner</p>
          <p className="text-sm font-medium truncate">{data.owner_name || data.own_name || 'Owner Not Available'}</p>
        </div>

        {/* Values section */}
        <div className="flex items-center space-x-6">
          {/* Last Sale (only shows sales > $1,000) */}
          {enhancedData.sale_prc1 && enhancedData.sale_prc1 > 1000 && (
            <div className="text-right">
              <p className="text-xs text-gray-500">Last Sale</p>
              <p className="font-semibold">{formatCurrency(enhancedData.sale_prc1)}</p>
              <p className="text-xs text-gray-500">
                {formatSaleDate(enhancedData.sale_date, enhancedData.sale_yr1, enhancedData.sale_month)}
              </p>
            </div>
          )}
          
          {/* Appraised Value */}
          <div className="text-right">
            <p className="text-xs text-gray-500">Appraised</p>
            <p className="font-bold text-green-600">{formatCurrency(getAppraisedValue(data))}</p>
          </div>
          
          {/* Building Sq Ft */}
          {data.tot_lvg_area && (
            <div className="text-right">
              <p className="text-xs text-gray-500">Building</p>
              <p className="font-semibold">{formatArea(data.tot_lvg_area)}</p>
            </div>
          )}

          {/* Land Sq Ft */}
          <div className="text-right">
            <p className="text-xs text-gray-500">Land</p>
            <p className="font-semibold">{formatArea(data.lnd_sqfoot)}</p>
          </div>
        </div>

        {/* Status indicators */}
        <div className="flex items-center space-x-2 ml-4">
          {isWatched && <Star className="w-4 h-4 text-yellow-500 fill-current" />}
          {hasNotes && (
            <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
              <span className="text-xs font-bold text-blue-600">3</span>
            </div>
          )}
          {onToggleSelection && (
            <div 
              className="hover:bg-gray-100 p-1 rounded"
              onClick={(e) => {
                e.stopPropagation();
                onToggleSelection();
              }}
            >
              {isSelected ? (
                <CheckSquare className="w-4 h-4" style={{color: '#d4af37'}} />
              ) : (
                <Square className="w-4 h-4" style={{color: '#95a5a6'}} />
              )}
            </div>
          )}
        </div>

        {/* Actions */}
        {showQuickActions && (
          <div className="ml-4">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button 
                  size="sm" 
                  variant="ghost"
                  className="h-8 w-8 p-0"
                  onClick={(e) => e.stopPropagation()}
                >
                  <MoreVertical className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={(e) => e.stopPropagation()}>
                  <Eye className="w-4 h-4 mr-2" />
                  View Details
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Star className="w-4 h-4 mr-2" />
                  Add to Watchlist
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Phone className="w-4 h-4 mr-2" />
                  Contact Owner
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )}
      </div>
    </Card>
  );
});