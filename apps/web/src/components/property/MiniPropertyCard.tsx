import React, { useMemo, useCallback } from 'react';
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
  Building2,
  Square,
  Tag,
  CheckSquare,
  AlertTriangle,
  ExternalLink,
  Factory,
  TreePine,
  Church,
  Shield,
  Leaf,
  Landmark,
  Store,
  Truck,
  Utensils,
  Banknote,
  Wrench,
  Hotel,
  GraduationCap,
  Cross,
  Zap,
  type LucideIcon
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useSalesData, getLatestSaleInfo } from '@/hooks/useSalesData';
import { getUseCodeInfo, getPropertyCategory as getDORCategory, getUseCodeShortName, getUseCodeDescription, getPropertyIcon, getPropertyIconColor } from '@/lib/dorUseCodes';
import { useSunbizMatching, getSunbizSearchUrl } from '@/hooks/useSunbizMatching';
import { getDorCodeFromPropertyUse, getPropertyUseDescription, getPropertyCategory as getUseCategoryFromText } from '@/lib/propertyUseToDorCode';
import { getPropertySubtype, getPropertyCategory as getStandardizedCategory } from '@/utils/property-types';
import { getPropertyUseShortName } from '@/lib/property-types';

// Icon mapper to convert string icon names to React components
const ICON_MAP: Record<string, LucideIcon> = {
  Home,
  Building,
  Building2,
  Store,
  Factory,
  TreePine,
  Church,
  Landmark,
  Truck,
  Utensils,
  Banknote,
  Wrench,
  Hotel,
  GraduationCap,
  Cross,
  Zap,
  MapPin
};

// Helper function to get border color based on property type for visual distinction
const getPropertyTypeBorderColor = (standardizedUse?: string): string => {
  if (!standardizedUse) return '';

  const useLower = standardizedUse.toLowerCase();

  // Residential properties (Single Family, Condo, etc.) - Blue
  if (useLower.includes('residential') || useLower.includes('condominium') || useLower.includes('home')) {
    return 'border-l-4 border-l-blue-500';
  }
  // Commercial properties - Green
  else if (useLower.includes('commercial')) {
    return 'border-l-4 border-l-green-500';
  }
  // Industrial properties - Orange
  else if (useLower.includes('industrial')) {
    return 'border-l-4 border-l-orange-500';
  }
  // Multi-Family properties - Purple
  else if (useLower.includes('multi-family')) {
    return 'border-l-4 border-l-purple-500';
  }
  // Agricultural properties - Emerald
  else if (useLower.includes('agricultural')) {
    return 'border-l-4 border-l-emerald-500';
  }
  // Institutional/Government properties - Indigo
  else if (useLower.includes('institutional') || useLower.includes('government')) {
    return 'border-l-4 border-l-indigo-500';
  }
  // Vacant land - Gray
  else if (useLower.includes('vacant')) {
    return 'border-l-4 border-l-gray-400';
  }

  return '';
};

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
    owner_addr1?: string;  // Owner address field
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
    standardized_property_use?: string; // Standardized property use category from database
    sale_prc1?: number;    // Last sale price
    sale_yr1?: number;     // Last sale year
    sale_date?: string;    // Last sale date (YYYY-MM-DD)
    sale_month?: number;   // Last sale month (1-12)
    property_type?: string; // Property type description
    has_tax_certificates?: boolean; // Tax certificate indicator
    certificate_count?: number;     // Number of tax certificates
    taxable_value?: number;         // Taxable value
    assessed_value?: number;        // Assessed value
    // Tax deed auction details
    auction_date?: string;          // Auction date (YYYY-MM-DD)
    opening_bid?: number;           // Starting bid amount
    tax_deed_number?: string;       // Tax deed number
    auction_url?: string;           // Direct link to auction
    total_certificate_amount?: number; // Total certificate amount
  };
  salesData?: any[];  // Optional: pre-fetched sales data from batch query (eliminates N+1 queries)
  isBatchLoading?: boolean;  // Indicates whether batch sales data is currently loading
  onClick?: () => void;
  variant?: 'grid' | 'list';
  showQuickActions?: boolean;
  isWatched?: boolean;
  hasNotes?: boolean;
  priority?: 'low' | 'medium' | 'high';
  isSelected?: boolean;
  onToggleSelection?: () => void;
}

// Get property category based on DOR use code (moved outside component for stability)
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

// Property type badges with colors (moved outside component for stability)
const getPropertyTypeBadge = (standardizedPropertyUse?: string, useCode?: string, propertyType?: string, ownerName?: string, justValue?: number, hasAddress?: boolean, propertyUse?: string | number, propertyUseDesc?: string) => {
  // **PRIORITY 1**: Use standardized_property_use from database (most accurate!)
  let category = 'Unknown';
  let dorCode: string | undefined;
  let useDescription: string | undefined;
  let IconComponent: any;
  let iconColor: string = '';

  // PRIORITY 1: Use standardized_property_use directly from database (100% accurate)
  if (standardizedPropertyUse) {
    category = getPropertyUseShortName(standardizedPropertyUse);
    useDescription = standardizedPropertyUse; // Use full name as description

    // Debug logging
    if (import.meta.env.DEV) {
      console.log('[MiniPropertyCard] Using standardized_property_use:', {
        standardizedPropertyUse,
        category,
        ownerName: ownerName?.substring(0, 30)
      });
    }

    // Get icon and color based on standardized category
    // Map standardized categories to icon names
    const categoryLower = standardizedPropertyUse.toLowerCase();
    if (categoryLower.includes('residential') || categoryLower.includes('condominium') || categoryLower.includes('home')) {
      IconComponent = Home;
      iconColor = 'text-blue-600';
    } else if (categoryLower.includes('commercial')) {
      IconComponent = Store;
      iconColor = 'text-green-600';
    } else if (categoryLower.includes('industrial')) {
      IconComponent = Factory;
      iconColor = 'text-orange-600';
    } else if (categoryLower.includes('agricultural')) {
      IconComponent = TreePine;
      iconColor = 'text-emerald-600';
    } else if (categoryLower.includes('institutional') || categoryLower.includes('government')) {
      IconComponent = Landmark;
      iconColor = 'text-purple-600';
    } else if (categoryLower.includes('vacant')) {
      IconComponent = Square;
      iconColor = 'text-gray-500';
    } else {
      IconComponent = Home;
      iconColor = 'text-gray-500';
    }
  }
  // PRIORITY 2: Fallback to property_use parsing if standardized field is missing
  else if (propertyUse) {
    const propertyUseStr = String(propertyUse);
    category = getStandardizedCategory(propertyUseStr);
    useDescription = getPropertySubtype(propertyUseStr);

    // Debug logging
    if (import.meta.env.DEV) {
      console.log('[MiniPropertyCard] Fallback to property_use parsing:', {
        propertyUse: propertyUseStr,
        category,
        useDescription,
        ownerName: ownerName?.substring(0, 30)
      });
    }

    // Get icon and color from existing DOR system
    dorCode = getDorCodeFromPropertyUse(propertyUseStr);
    const iconName = getPropertyIcon(dorCode || propertyUseStr);
    IconComponent = ICON_MAP[iconName] || Home; // Convert string to React component
    iconColor = getPropertyIconColor(dorCode || propertyUseStr);
  } else {
    // Log when both fields are missing
    if (import.meta.env.DEV) {
      console.warn('[MiniPropertyCard] No standardized_property_use or property_use field, will use fallback categorization:', {
        ownerName: ownerName?.substring(0, 30),
        propertyType,
        useCode
      });
    }
    // Set fallback icon when property_use is not available
    IconComponent = Home;
    iconColor = 'text-gray-500';
  }

  // PRIORITY 2: Check API's propertyType if standardized utility didn't provide category
  if (category === 'Unknown' && propertyType) {
    category = getPropertyCategory(useCode, propertyType);
  }

  // PRIORITY 3: Fallback to DOR code mapping if TEXT system didn't work
  if (category === 'Unknown' && propertyUse) {
    // Use correct DOR code category mapping
    const dorCategory = getDORCategory(String(propertyUse));
    if (dorCategory !== 'UNKNOWN') {
      category = dorCategory.charAt(0) + dorCategory.slice(1).toLowerCase();
    }
  }

  // PRIORITY 4 (FINAL FALLBACK): Only use owner-based categorization if API didn't provide propertyType
  // AND property_use codes didn't provide a category
  if (category === 'Unknown' && ownerName) {
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

  // Category styling configuration (icon + color)
  const getCategoryStyle = (cat: string) => {
    const styles = {
      'Residential': {
        icon: Home,
        color: 'rgb(46, 204, 113)',
        bg: 'rgba(46, 204, 113, 0.1)'
      },
      'Commercial': {
        icon: Building,
        color: 'rgb(155, 89, 182)',
        bg: 'rgba(155, 89, 182, 0.1)'
      },
      'Industrial': {
        icon: Factory,
        color: 'rgb(230, 126, 34)',
        bg: 'rgba(230, 126, 34, 0.1)'
      },
      'Agricultural': {
        icon: TreePine,
        color: 'rgb(241, 196, 15)',
        bg: 'rgba(241, 196, 15, 0.1)'
      },
      'Government': {
        icon: Shield,
        color: 'rgb(231, 76, 60)',
        bg: 'rgba(231, 76, 60, 0.1)'
      },
      'Governmental': {
        icon: Landmark,
        color: 'rgb(231, 76, 60)',
        bg: 'rgba(231, 76, 60, 0.1)'
      },
      'Conservation': {
        icon: Leaf,
        color: 'rgb(39, 174, 96)',
        bg: 'rgba(39, 174, 96, 0.1)'
      },
      'Religious': {
        icon: Church,
        color: 'rgb(142, 68, 173)',
        bg: 'rgba(142, 68, 173, 0.1)'
      },
      'Vacant/Special': {
        icon: Square,
        color: 'rgb(243, 156, 18)',
        bg: 'rgba(243, 156, 18, 0.1)'
      },
      'Vacant Land': {
        icon: Square,
        color: 'rgb(149, 165, 166)',
        bg: 'rgba(149, 165, 166, 0.1)'
      },
      'Institutional': {
        icon: Building,
        color: 'rgb(155, 89, 182)',
        bg: 'rgba(155, 89, 182, 0.1)'
      },
      'Miscellaneous': {
        icon: Tag,
        color: 'rgb(149, 165, 166)',
        bg: 'rgba(149, 165, 166, 0.1)'
      },
      'Unknown': {
        icon: Tag,
        color: 'rgb(149, 165, 166)',
        bg: 'rgba(149, 165, 166, 0.1)'
      }
    };
    return styles[cat as keyof typeof styles] || styles['Unknown'];
  };

  const categoryStyle = getCategoryStyle(category);
  const CategoryIconComponent = categoryStyle.icon;

  // Return both category badge and detailed use badge
  return (
    <div className="flex items-center flex-wrap gap-1.5">
      {/* Main category badge with icon - ELEGANT STYLE */}
      <div
        className="badge-elegant inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors"
        style={{
          borderColor: categoryStyle.color,
          color: categoryStyle.color,
          background: categoryStyle.bg
        }}
      >
        {CategoryIconComponent && React.createElement(CategoryIconComponent, { className: "w-3 h-3 mr-1" })}
        {category}
      </div>

      {/* NEW: Property USE description badge with icon (from property_use field) */}
      {useDescription && useDescription !== 'Property' && IconComponent && (
        <Badge variant="outline" className="flex items-center gap-1.5 text-xs font-medium border-blue-300 bg-blue-50 text-blue-700">
          <IconComponent className={`w-3.5 h-3.5 ${iconColor}`} />
          <span>{useDescription}</span>
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

// Helper functions moved outside component to prevent recreation
const getAppraisedValue = (data: any) => {
  return data.jv || data.just_value || data.appraised_value || data.market_value || data.assessed_value;
};

const getTaxableValue = (data: any) => {
  return data.tv_sd || data.taxable_value || data.tax_value;
};

const getLandValue = (data: any) => {
  return data.lnd_val || data.land_value;
};

const formatCurrency = (value?: number) => {
  if (!value && value !== 0) return 'N/A';
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

export const MiniPropertyCard = React.memo(function MiniPropertyCard({
  parcelId,
  data,
  salesData: salesDataProp,
  isBatchLoading = false,
  onClick,
  variant = 'grid',
  showQuickActions = true,
  isWatched = false,
  hasNotes = false,
  priority,
  isSelected = false,
  onToggleSelection
}: MiniPropertyCardProps) {

  // Use prop salesData if provided (batch query), otherwise fetch individually
  // This eliminates N+1 query problem when parent provides batch data
  // CRITICAL: Don't fetch individually if batch is loading (race condition fix)
  const shouldFetchIndividually = !salesDataProp && !isBatchLoading;

  const { salesData: fetchedSalesData } = useSalesData(shouldFetchIndividually ? parcelId : null);
  const salesData = salesDataProp || fetchedSalesData;

  // Sunbiz matching - only fetches on manual trigger (button click)
  const { bestMatch, hasMatches, loading: sunbizLoading, fetchMatches } = useSunbizMatching(
    parcelId,
    data.owner_name || data.own_name,
    false // Don't auto-fetch - only fetch when user clicks "View Sunbiz" button
  );

  // Memoize latest sale info
  const latestSaleInfo = useMemo(() => getLatestSaleInfo(salesData), [salesData]);

  // Memoize enhanced data
  const enhancedData = useMemo(() => {
    const base = {
      ...data,
      ...latestSaleInfo
    };

    // Use real sales data if available
    if (salesData && Array.isArray(salesData) && salesData.length > 0) {
      const latestSale = salesData[0];
      const salePrice = typeof latestSale.sale_price === 'string' ? parseFloat(latestSale.sale_price) : latestSale.sale_price;
      if (salePrice && salePrice >= 1000) {
        base.sale_prc1 = salePrice;
        base.sale_yr1 = latestSale.sale_date ? new Date(latestSale.sale_date).getFullYear() : null;
        base.sale_date = latestSale.sale_date;
        base.sale_month = latestSale.sale_date ? new Date(latestSale.sale_date).getMonth() + 1 : null;
      }
    }

    return base;
  }, [data, latestSaleInfo, salesData]);

  // Memoize formatted address
  const formattedAddress = useMemo(() => {
    if (!data.phy_addr1 || data.phy_addr1 === '-' || data.phy_addr1 === 'No Street Address') {
      if (data.owner_addr1 && data.owner_addr1 !== '-') {
        return data.owner_addr1;
      }
      if (data.owner_name && (data.owner_name.includes('TRUSTEE') || data.owner_name.includes('BRD OF'))) {
        return 'No Street Address';
      }
      return 'Address Not Available';
    }
    return data.phy_addr1;
  }, [data.phy_addr1, data.owner_addr1, data.owner_name]);

  // Memoize Google Maps URL
  const googleMapsUrl = useMemo(() => {
    if (data.phy_addr1 && data.phy_city && data.phy_addr1 !== '-' && data.phy_addr1 !== 'No Street Address') {
      return `https://www.google.com/maps/search/${encodeURIComponent(
        `${data.phy_addr1}, ${data.phy_city}, FL ${data.phy_zipcd || ''}`
      )}`;
    } else if (data.owner_addr1 && data.owner_addr1 !== '-') {
      return `https://www.google.com/maps/search/${encodeURIComponent(
        `${data.owner_addr1}, FL`
      )}`;
    } else if (parcelId) {
      return `https://www.google.com/maps/search/${encodeURIComponent(
        `Parcel ${parcelId} Florida`
      )}`;
    }
    return '#';
  }, [data.phy_addr1, data.phy_city, data.phy_zipcd, data.owner_addr1, parcelId]);

  // Memoize property badge
  const propertyBadge = useMemo(() => {
    return getPropertyTypeBadge(
      data.standardized_property_use, // PRIORITY 1: Use standardized field from database
      data.dor_uc,
      data.property_type,
      data.owner_name || data.own_name,
      getAppraisedValue(data),
      !!(data.phy_addr1 && data.phy_addr1 !== '-'),
      data.property_use,        // FIXED: Was data.propertyUse (camelCase)
      data.property_use_desc    // FIXED: Was data.propertyUseDesc (camelCase)
    );
  }, [data.standardized_property_use, data.dor_uc, data.property_type, data.owner_name, data.own_name, data.phy_addr1, data.property_use, data.property_use_desc, data.jv]);

  // Memoize Sunbiz click handler - triggers fetch and opens Sunbiz search
  const handleSunbizClick = useCallback(async (e: React.MouseEvent) => {
    e.stopPropagation();
    const ownerName = data.owner_name || data.own_name || '';
    if (!ownerName) return;

    // Trigger the Sunbiz match fetch (only runs once, on first click)
    if (!hasMatches && !sunbizLoading && fetchMatches) {
      await fetchMatches();
    }

    // Open Sunbiz search URL (with best match if available)
    const searchUrl = getSunbizSearchUrl(ownerName, bestMatch);
    window.open(searchUrl, '_blank');
  }, [data.owner_name, data.own_name, bestMatch, hasMatches, sunbizLoading, fetchMatches]);

  // Memoize Google Maps click handler
  const handleMapClick = useCallback((e: React.MouseEvent) => {
    if (!data.phy_addr1 && !data.owner_addr1 && !parcelId) {
      e.preventDefault();
    } else {
      e.stopPropagation();
    }
  }, [data.phy_addr1, data.owner_addr1, parcelId]);

  // Memoize selection toggle handler
  const handleToggleSelection = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    onToggleSelection?.();
  }, [onToggleSelection]);

  // Grid variant - Elegant card design
  if (variant === 'grid') {
    return (
      <div
        className={`
          elegant-card hover-lift cursor-pointer animate-in
          ${getPropertyTypeBorderColor(data.standardized_property_use)}
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
              onClick={handleToggleSelection}
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
            {propertyBadge}
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
                  href={googleMapsUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline"
                  onClick={handleMapClick}
                >
                  <p className="font-semibold text-sm mb-0.5 hover:text-blue-600 transition-colors flex items-center gap-1" style={{color: '#2c3e50'}}>
                    {formattedAddress}
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
                onClick={handleSunbizClick}
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
        ${!priority ? getPropertyTypeBorderColor(data.standardized_property_use) : ''}
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
              {propertyBadge}
              <a
                href={googleMapsUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:underline truncate"
                onClick={handleMapClick}
              >
                <p className="font-semibold text-sm truncate hover:text-blue-600 transition-colors flex items-center gap-1">
                  {formattedAddress}
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
              onClick={handleToggleSelection}
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
}, (prevProps, nextProps) => {
  // Custom comparison function for React.memo
  return (
    prevProps.parcelId === nextProps.parcelId &&
    prevProps.variant === nextProps.variant &&
    prevProps.showQuickActions === nextProps.showQuickActions &&
    prevProps.isWatched === nextProps.isWatched &&
    prevProps.hasNotes === nextProps.hasNotes &&
    prevProps.priority === nextProps.priority &&
    prevProps.isSelected === nextProps.isSelected &&
    // Sales data props (CRITICAL: ensures update when batch data arrives)
    prevProps.salesData === nextProps.salesData &&
    prevProps.isBatchLoading === nextProps.isBatchLoading &&
    // Deep comparison of data object key fields
    prevProps.data.phy_addr1 === nextProps.data.phy_addr1 &&
    prevProps.data.owner_name === nextProps.data.owner_name &&
    prevProps.data.jv === nextProps.data.jv &&
    prevProps.data.sale_prc1 === nextProps.data.sale_prc1 &&
    prevProps.data.has_tax_certificates === nextProps.data.has_tax_certificates &&
    prevProps.data.auction_date === nextProps.data.auction_date
  );
});
