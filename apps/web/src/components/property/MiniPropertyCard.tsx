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
  AlertTriangle
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
// TEMPORARILY DISABLED FOR DEBUGGING
// import { useSalesData, getLatestSaleInfo } from '@/hooks/useSalesData';

interface MiniPropertyCardProps {
  parcelId: string;
  data: {
    phy_addr1?: string;
    phy_city?: string;
    phy_zipcd?: string;
    own_name?: string;
    jv?: number;           // Just (appraised) value
    tv_sd?: number;        // Taxable value
    lnd_val?: number;      // Land value
    tot_lvg_area?: number; // Building square feet
    lnd_sqfoot?: number;   // Land square feet
    act_yr_blt?: number;   // Year built
    dor_uc?: string;       // Department of Revenue Use Code
    sale_prc1?: number;    // Last sale price
    sale_yr1?: number;     // Last sale year
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

// Get property use description from DOR use code
const getPropertyUse = (useCode?: string, propertyType?: string) => {
  if (!useCode) return 'Unknown';
  
  // Common DOR use codes - Florida Department of Revenue
  const useCodes: Record<string, string> = {
    // Residential (000-099)
    '000': 'Vacant Residential',
    '001': 'Single Family',
    '002': 'Mobile Home',
    '003': 'Multi-Family (2-9 units)',
    '004': 'Condominium',
    '005': 'Cooperative',
    '006': 'Retirement Home',
    '007': 'Miscellaneous Residential',
    '008': 'Multi-Family (10+ units)',
    '009': 'Undefined Residential',
    
    // Commercial (100-399)
    '100': 'Vacant Commercial',
    '101': 'Retail Store',
    '102': 'Office Building',
    '103': 'Department Store',
    '104': 'Supermarket',
    '105': 'Regional Shopping',
    '106': 'Community Shopping',
    '107': 'Wholesale Outlet',
    '108': 'Restaurant/Cafeteria',
    '109': 'Hotel/Motel',
    '110': 'Finance/Insurance/Real Estate',
    '111': 'Service Station',
    '112': 'Auto Sales/Service/Rental',
    '113': 'Parking Lot/Mobile Home Park',
    '114': 'Nightclub/Bar/Lounge',
    '115': 'Bowling Alley/Skating Rink',
    '116': 'Theater/Auditorium',
    '117': 'Race Track',
    
    // Industrial (400-499)
    '400': 'Vacant Industrial',
    '401': 'Light Manufacturing',
    '402': 'Heavy Manufacturing',
    '403': 'Lumber Yard/Saw Mill',
    '404': 'Packing Plant',
    '405': 'Cannery',
    '406': 'Food Processing',
    '407': 'Mineral Processing',
    '408': 'Warehouse/Storage',
    '409': 'Open Storage',
    
    // Agricultural (500-699)
    '500': 'Improved Agricultural',
    '501': 'Cropland/Soil',
    '502': 'Timber Land',
    '503': 'Grazing Land',
    '504': 'Orchard/Grove',
    '505': 'Poultry/Bee/Fish Farm',
    '506': 'Dairy',
    
    // Institutional (700-899)
    '700': 'Institutional',
    '701': 'Church',
    '702': 'Private School',
    '703': 'Hospital',
    '704': 'Charitable Service',
    '705': 'Clubs/Lodges',
    '706': 'Sanitarium/Convalescent',
    '707': 'Orphanage',
    '708': 'Cemetery',
    
    // Government (800-899)
    '800': 'Undefined Government',
    '801': 'Military',
    '802': 'Forest/Park/Recreational',
    '803': 'Public School',
    '804': 'College',
    '805': 'Hospital',
    '806': 'County',
    '807': 'State',
    '808': 'Federal',
    '809': 'Municipal',
    
    // Miscellaneous (900-999)
    '900': 'Leasehold Interest',
    '901': 'Utility',
    '902': 'Mining/Petroleum',
    '903': 'Subsurface Rights',
    '904': 'Right of Way',
    '905': 'Rivers/Lakes',
    '906': 'Submerged Land',
    '907': 'Waste Land'
  };
  
  const description = useCodes[useCode] || propertyType || 'Unknown';
  // Return code and description
  return `${useCode} - ${description}`;
};

// Get property category based on DOR use code
export const getPropertyCategory = (useCode?: string, propertyType?: string): string => {
  if (!useCode) {
    // Try to determine from property type description
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
    }
    return 'Unknown';
  }
  
  const firstDigit = useCode.charAt(0);
  
  // Florida DOR Use Code Categories
  if (firstDigit === '0') return 'Residential';
  if (firstDigit === '1' || firstDigit === '2' || firstDigit === '3') return 'Commercial';
  if (firstDigit === '4') return 'Industrial';
  if (firstDigit === '5' || firstDigit === '6') return 'Agricultural';
  if (firstDigit === '7' || firstDigit === '8') return 'Institutional';
  if (firstDigit === '9') return 'Miscellaneous';
  
  return 'Unknown';
};

// Property type badges with colors
const getPropertyTypeBadge = (useCode?: string, propertyType?: string) => {
  const category = getPropertyCategory(useCode, propertyType);
  const useDescription = useCode ? getPropertyUse(useCode, propertyType) : propertyType || 'Unknown';
  
  // Return both category badge and detailed use badge
  return (
    <div className="flex items-center space-x-2">
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
      {category === 'Institutional' && (
        <Badge className="bg-purple-100 text-purple-800 border-purple-200 font-medium">
          Institutional
        </Badge>
      )}
      {category === 'Miscellaneous' && (
        <Badge className="bg-gray-100 text-gray-800 border-gray-200 font-medium">
          Miscellaneous
        </Badge>
      )}
      {category === 'Unknown' && (
        <Badge variant="outline" className="font-medium">
          Unknown
        </Badge>
      )}
      
      {/* Detailed use code badge (smaller, secondary) */}
      {useCode && (
        <Badge variant="outline" className="text-xs">
          {useCode}
        </Badge>
      )}
    </div>
  );
};

export function MiniPropertyCard({
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
  console.log('Specific jv value:', data.jv);

  // TEMPORARILY DISABLED: Fetch sales data for this property
  // const { salesData } = useSalesData(parcelId);

  // TEMPORARILY DISABLED: Get latest sale info to augment the property data
  // const latestSaleInfo = getLatestSaleInfo(salesData);

  // SIMPLIFIED: Use data directly instead of enhanced data to debug the issue
  const enhancedData = data;

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
            {getPropertyTypeBadge(data.dor_uc, data.property_type)}
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
              <div>
                <p className="font-semibold text-sm mb-0.5" style={{color: '#2c3e50'}}>
                  {data.phy_addr1 || 'No Street Address'}
                </p>
                <p className="text-xs" style={{color: '#7f8c8d'}}>
                  {data.phy_city}, FL {data.phy_zipcd}
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
                <p className="text-xs font-medium truncate" style={{color: '#2c3e50'}}>{data.own_name || 'Unknown'}</p>
              </div>
            </div>
          </div>

          {/* Key Metrics Grid */}
          <div className="space-y-1.5">
            {/* Last Sale */}
            {enhancedData.sale_prc1 && (
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-1">
                  <Tag className="w-3 h-3" style={{color: '#95a5a6'}} />
                  <span className="text-xs" style={{color: '#95a5a6'}}>Last Sold</span>
                </div>
                <div className="text-right">
                  <span className="font-semibold text-sm" style={{color: '#2c3e50'}}>{formatCurrency(enhancedData.sale_prc1)}</span>
                  {enhancedData.sale_yr1 && (
                    <span className="text-xs ml-1" style={{color: '#7f8c8d'}}>({enhancedData.sale_yr1})</span>
                  )}
                </div>
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
                className="hover-lift h-6 px-2"
                style={{color: '#2c3e50'}}
                onClick={(e) => {
                  e.stopPropagation();
                }}
              >
                <Eye className="w-3 h-3 mr-1" />
                View
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
              <p className="font-semibold text-sm truncate">
                {data.phy_addr1 || 'No Street Address'}
              </p>
              {getPropertyTypeBadge(data.dor_uc, data.property_type)}
            </div>
            <p className="text-xs text-gray-500">
              {data.phy_city}, FL {data.phy_zipcd} • Parcel: {parcelId}
            </p>
          </div>
        </div>

        {/* Middle section - Owner */}
        <div className="px-4 min-w-0 flex-1 max-w-xs">
          <p className="text-xs text-gray-500 mb-1">Owner</p>
          <p className="text-sm font-medium truncate">{data.own_name || 'Unknown'}</p>
        </div>

        {/* Values section */}
        <div className="flex items-center space-x-6">
          {/* Last Sale */}
          {enhancedData.sale_prc1 && (
            <div className="text-right">
              <p className="text-xs text-gray-500">Last Sale</p>
              <p className="font-semibold">{formatCurrency(enhancedData.sale_prc1)}</p>
              {enhancedData.sale_yr1 && (
                <p className="text-xs text-gray-500">{enhancedData.sale_yr1}</p>
              )}
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
}