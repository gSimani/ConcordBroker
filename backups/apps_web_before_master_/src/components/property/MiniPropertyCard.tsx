import React from 'react';
import { Card } from '@/components/ui/card';
import { getPropertyCategoryFromCode, getSubUseType, getPropertyCategory } from '@/utils/propertyCategories';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import '@/styles/elegant-property.css';
import { ConcordBemPatterns } from '@/utils/bemClassNames';
import propertyCardStyles from '@/styles/components/property-card.module.css';
import { getUseIcon } from '@/lib/icons/useIcons';
import { usePropertyNavigation } from '@/hooks/usePropertyNavigation';
import {
  MapPin,
  DollarSign,
  User,
  TrendingUp,
  TrendingDown,
  Calendar,
  Eye,
  Star,
  MoreVertical,
  Phone,
  Mail,
  Square,
  Tag,
  CheckSquare,
  AlertTriangle,
  ExternalLink,
  Building,
  Home,
  Brain,
  Receipt,
  Activity,
  Loader2
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
import { SalesHistoryCard } from './SalesHistoryCard';
import { useAISalesHistory, formatCurrency, formatDate, getAppreciationColor, getInvestmentGradeColor } from '@/hooks/useAISalesHistory';
import { useNAVAssessments } from '@/hooks/useNAVAssessments';
// import { useWatchlist } from '@/hooks/useWatchlist';
// import { usePropertyNotes } from '@/hooks/usePropertyNotes';

// New function to categorize properties based on actual property_use numeric codes
// MOVED TO utils/propertyCategories.ts to fix React Fast Refresh
// export const getPropertyCategoryFromCode = (propertyUse?: string | number, propertyUseDesc?: string): string => {
/*
const getPropertyCategoryFromCode = (propertyUse?: string | number, propertyUseDesc?: string): string => {
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
}; */

// Function to extract sub-use type from property_use_desc
// MOVED TO utils/propertyCategories.ts
/* export const getSubUseType = (propertyUseDesc?: string, category?: string): string | null => {
  if (!propertyUseDesc) return null;

  const desc = propertyUseDesc.toUpperCase().trim();

  // Map based on main category and common sub-use patterns - prioritize keyword matching
  switch (category) {
    case 'Residential':
      if (desc.includes('SINGLE FAMILY') || desc.includes('SINGLE-FAMILY')) return 'Single Family';
      if (desc.includes('CONDO') || desc.includes('CONDOMINIUM')) return 'Condo';
      if (desc.includes('MULTI-FAMILY') || desc.includes('MULTI FAMILY') || desc.includes('MULTIFAMILY')) return 'Multi-Family';
      if (desc.includes('TOWNHOUSE') || desc.includes('TOWNHOME')) return 'Townhouse';
      if (desc.includes('MOBILE') || desc.includes('MANUFACTURED')) return 'Mobile Home';
      if (desc.includes('DUPLEX')) return 'Duplex';
      if (desc.includes('APARTMENT')) return 'Apartment';
      break;

    case 'Commercial':
      if (desc.includes('RETAIL')) return 'Retail';
      if (desc.includes('OFFICE')) return 'Office';
      if (desc.includes('HOTEL') || desc.includes('MOTEL')) return 'Hotel';
      if (desc.includes('RESTAURANT')) return 'Restaurant';
      if (desc.includes('SHOPPING') || desc.includes('MALL')) return 'Shopping';
      if (desc.includes('WAREHOUSE') && desc.includes('COMMERCIAL')) return 'Warehouse';
      if (desc.includes('MIXED USE')) return 'Mixed Use';
      if (desc.includes('MEDICAL')) return 'Medical';
      if (desc.includes('AUTO') || desc.includes('SERVICE')) return 'Auto/Service';
      break;

    case 'Industrial':
      if (desc.includes('WAREHOUSE')) return 'Warehouse';
      if (desc.includes('MANUFACTURING')) return 'Manufacturing';
      if (desc.includes('DISTRIBUTION')) return 'Distribution';
      if (desc.includes('STORAGE')) return 'Storage';
      if (desc.includes('UTILITY')) return 'Utility';
      if (desc.includes('LOGISTICS')) return 'Logistics';
      break;

    case 'Agricultural':
      if (desc.includes('FARM')) return 'Farm';
      if (desc.includes('GROVE') || desc.includes('ORCHARD')) return 'Grove';
      if (desc.includes('RANCH')) return 'Ranch';
      if (desc.includes('TIMBER')) return 'Timber';
      if (desc.includes('NURSERY')) return 'Nursery';
      if (desc.includes('LIVESTOCK')) return 'Livestock';
      break;

    case 'Government':
      if (desc.includes('SCHOOL')) return 'School';
      if (desc.includes('PARK')) return 'Park';
      if (desc.includes('MUNICIPAL')) return 'Municipal';
      if (desc.includes('COUNTY')) return 'County';
      if (desc.includes('STATE')) return 'State';
      if (desc.includes('FEDERAL')) return 'Federal';
      break;

    case 'Religious':
      if (desc.includes('CHURCH')) return 'Church';
      if (desc.includes('SYNAGOGUE')) return 'Synagogue';
      if (desc.includes('TEMPLE')) return 'Temple';
      if (desc.includes('MOSQUE')) return 'Mosque';
      break;

    case 'Conservation':
      if (desc.includes('PRESERVE')) return 'Preserve';
      if (desc.includes('CONSERVATION')) return 'Conservation';
      if (desc.includes('NATURE')) return 'Nature';
      if (desc.includes('WILDLIFE')) return 'Wildlife';
      break;
  }

  // If no specific sub-type found, try to extract meaningful parts
  if (desc.includes('RESIDENTIAL')) return 'Residential';
  if (desc.includes('COMMERCIAL')) return 'Commercial';
  if (desc.includes('VACANT')) return 'Vacant';

  // Return the original description if it's short, clean, and doesn't contain spaces/separators
  if (desc.length <= 15 && !desc.includes(',') && !desc.includes('/') && desc.split(/\s+/).length === 1) {
    return propertyUseDesc;
  }

  // For very short descriptions (2-3 words), return as-is if meaningful
  const words = desc.split(/\s+/);
  if (words.length <= 2 && desc.length <= 20 && !desc.includes(',') && !desc.includes('/')) {
    return propertyUseDesc;
  }

  return null;
}; */

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
    use_category?: string;          // Server-side normalized use category
    use_subcategory?: string;       // Server-side subcategory
    use_description?: string;       // Server-side generated description
    use_code?: string;              // DOR use code
    sale_prc1?: number;    // Last sale price
    sale_yr1?: number;     // Last sale year
    sale_date?: string;    // Last sale date (YYYY-MM-DD)
    sale_month?: number;   // Last sale month (1-12)
    last_sale_price?: number; // Alternative sale price field
    last_sale_year?: number;  // Alternative sale year field
    last_sale_date?: string;  // Alternative sale date field
    sale_price?: number;    // Sale price from sales data
    sale_qualification?: string; // Deed type/qualification
    property_type?: string; // Property type description
    has_tax_certificates?: boolean; // Tax certificate indicator
    certificate_count?: number;     // Number of tax certificates
    // Tax deed auction details
    auction_date?: string;          // Auction date (YYYY-MM-DD)
    opening_bid?: number;           // Starting bid amount
    tax_deed_number?: string;       // Tax deed number
    auction_url?: string;           // Direct link to auction
    total_certificate_amount?: number; // Total certificate amount
    county?: string;        // County name for clerk records links
    // Sales history props for SalesHistoryCard
    last_qualified_sale?: {
      sale_date: string;
      sale_price: number;
      instrument_type?: string;
      book_page?: string;
      qualification?: string;
    } | null;
    has_qualified_sale?: boolean;
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
// MOVED TO utils/propertyCategories.ts
/* export const getPropertyCategory = (useCode?: string, propertyType?: string): string => {
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
}; */

// Property type badges with colors
const getPropertyTypeBadge = (useCode?: string, propertyType?: string, ownerName?: string, justValue?: number, hasAddress?: boolean, propertyUse?: string | number, propertyUseDesc?: string, useCategory?: string, useSubcategory?: string, useDescription?: string) => {
  // First try to use server-side use_category if available
  let category = useCategory;

  // If no server-side category, try to get category from the property_use field
  if (!category) {
    category = getPropertyCategoryFromCode(propertyUse, propertyUseDesc);
  }

  // If that doesn't work, fall back to old method
  if (!category || category === 'Unknown') {
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
  // Try to get DOR code information first
  const dorInfo = getUseCodeInfo(useCode);

  // If we have DOR info, use it to enhance the category
  if (dorInfo && dorInfo.category !== 'Unknown') {
    category = dorInfo.category;
  }

  // Get icon configuration for the category
  const iconConfig = getUseIcon(category);
  const Icon = iconConfig.icon;

  // Get sub-use type - prioritize DOR subcategory, then server-side, then derived
  const subUseType = (dorInfo && dorInfo.subcategory) || useSubcategory || getSubUseType(propertyUseDesc, category);

  // Get description - prioritize DOR description, then server-side, then property desc
  const description = (dorInfo && dorInfo.description) || useDescription || propertyUseDesc;

  // Color mapping for consistent styling with PropertySearch filter buttons
  // These colors EXACTLY match the filter button styles
  const getColorTheme = (category: string) => {
    // Normalize category for case-insensitive matching
    const normalizedCategory = category?.toLowerCase() || '';

    if (normalizedCategory.includes('residential')) {
      return {
        primary: 'rgb(34, 197, 94)',
        background: 'rgb(240, 253, 244)',
        border: 'rgb(187, 247, 208)',
        text: 'rgb(34, 197, 94)'
      };
    }

    if (normalizedCategory.includes('commercial')) {
      return {
        primary: 'rgb(59, 130, 246)',
        background: 'rgb(239, 246, 255)',
        border: 'rgb(191, 219, 254)',
        text: 'rgb(59, 130, 246)'
      };
    }

    if (normalizedCategory.includes('industrial')) {
      return {
        primary: 'rgb(251, 146, 60)',
        background: 'rgb(255, 247, 237)',
        border: 'rgb(254, 215, 170)',
        text: 'rgb(251, 146, 60)'
      };
    }

    if (normalizedCategory.includes('agricultural')) {
      return {
        primary: 'rgb(245, 158, 11)',
        background: 'rgb(255, 251, 235)',
        border: 'rgb(253, 230, 138)',
        text: 'rgb(245, 158, 11)'
      };
    }

    if (normalizedCategory.includes('vacant')) {
      return {
        primary: 'rgb(107, 114, 128)',
        background: 'rgb(249, 250, 251)',
        border: 'rgb(209, 213, 219)',
        text: 'rgb(107, 114, 128)'
      };
    }

    if (normalizedCategory.includes('government')) {
      return {
        primary: 'rgb(239, 68, 68)',
        background: 'rgb(254, 242, 242)',
        border: 'rgb(254, 202, 202)',
        text: 'rgb(239, 68, 68)'
      };
    }

    if (normalizedCategory.includes('conservation')) {
      return {
        primary: 'rgb(16, 185, 129)',
        background: 'rgb(236, 253, 245)',
        border: 'rgb(167, 243, 208)',
        text: 'rgb(16, 185, 129)'
      };
    }

    if (normalizedCategory.includes('religious')) {
      return {
        primary: 'rgb(168, 85, 247)',
        background: 'rgb(250, 245, 255)',
        border: 'rgb(233, 213, 255)',
        text: 'rgb(168, 85, 247)'
      };
    }

    if (normalizedCategory.includes('special')) {
      return {
        primary: 'rgb(217, 119, 6)',
        background: 'rgb(255, 251, 235)',
        border: 'rgb(253, 230, 138)',
        text: 'rgb(217, 119, 6)'
      };
    }

    // Default fallback
    return {
      primary: 'rgb(107, 114, 128)',
      background: 'rgb(249, 250, 251)',
      border: 'rgb(209, 213, 219)',
      text: 'rgb(107, 114, 128)'
    };
  };

  const colorTheme = getColorTheme(category);
  const shortName = getUseCodeShortName(useCode);
  const useCodeInfo = getUseCodeInfo(useCode);

  // Return both category badge and sub-use badge
  return (
    <div className="flex items-center flex-wrap gap-1.5">
      {/* Main category badge with elegant gold styling */}
      <Badge
        data-testid="property-type-badge"
        className="font-medium flex items-center gap-1.5 text-sm border-yellow-400 bg-yellow-50 text-yellow-800"
        title={description || `${category} property`}
      >
        <Icon size={14} aria-hidden="true" />
        {category.toUpperCase()}
      </Badge>

      {/* Sub-use type badge - showing specific property sub-type */}
      {subUseType && (
        <Badge
          data-testid="property-subuse-badge"
          className="text-xs font-normal flex items-center gap-1"
          title={description || `${subUseType} property`}
          style={{
            backgroundColor: `${colorTheme.primary}10`, // 10% opacity for lighter appearance
            color: colorTheme.primary,
            borderColor: `${colorTheme.primary}30`, // 30% opacity for subtle border
            border: '1px solid'
          }}
        >
          {subUseType}
        </Badge>
      )}

      {/* DOR code badge (always show with fallback) */}
      <Badge
        data-testid="badge-container"
        className="text-xs font-mono inline-flex items-center"
        title={dorInfo ? `DOR Code ${dorInfo.code}: ${dorInfo.description}` : `Property Use Code: ${propertyUse || 'Unknown'}`}
        style={{
          backgroundColor: 'rgb(249, 250, 251)',
          color: 'rgb(107, 114, 128)',
          borderColor: 'rgb(209, 213, 219)',
          border: '1px solid'
        }}
      >
        {dorInfo ? `Code ${dorInfo.code}` : `Use ${propertyUse || '?'}`}
      </Badge>
    </div>
  );
};

export function MiniPropertyCard({
  parcelId,
  data,
  onClick,
  variant = 'grid',
  showQuickActions = true,
  isWatched: propsIsWatched = false,
  hasNotes: propsHasNotes = false,
  priority,
  isSelected = false,
  onToggleSelection
}: MiniPropertyCardProps) {
  // BEM class generator
  const propertyCard = ConcordBemPatterns.propertyCard;

  // Use property navigation hook
  const { navigateToProperty, getPropertyUrl, getPropertyTitle } = usePropertyNavigation();

  // Get property URL and title
  const propertyUrl = getPropertyUrl({ parcelId, ...data });
  const propertyTitle = getPropertyTitle({ parcelId, ...data });

  // Watchlist and notes integration - temporarily disabled for sales history demo
  // const {
  //   isInWatchlist,
  //   addToWatchlist,
  //   removeFromWatchlist,
  //   loading: watchlistLoading
  // } = useWatchlist();

  // const {
  //   propertyNotes,
  //   hasNotes: hasRealNotes
  // } = usePropertyNotes(parcelId);

  // AI Sales History Integration
  const { salesData, aiAnalysis, isLoading: salesLoading } = useAISalesHistory(parcelId, true);

  // NAV Assessments Integration
  const { navData, isLoading: navLoading } = useNAVAssessments(parcelId);

  // Determine actual watchlist and notes status - using props only for now
  const isWatched = propsIsWatched;
  const hasNotes = propsHasNotes;
  const watchlistLoading = false;
  const propertyNotes = [];
  const isInWatchlist = (parcelId: string) => false;

  // Handle card click navigation
  const handleCardClick = () => {
    if (onClick) {
      onClick(); // Call custom onClick if provided
    } else {
      // Navigate to AI-enhanced property profile page
      window.location.href = `/ai-property/${parcelId}`;
    }
  };

  // Handle watchlist toggle - temporarily disabled for sales history demo
  const handleWatchlistToggle = async (e: React.MouseEvent) => {
    e.stopPropagation();
    console.log('Watchlist toggle temporarily disabled for sales history demo');
    // Temporarily disabled - would require auth provider setup
  };

  // Sales data already fetched above with useAISalesHistory
  // const { salesData } = useSalesData(parcelId); // Removed duplicate

  // Fetch Sunbiz matching data for this property
  const { bestMatch, hasMatches, loading: sunbizLoading } = useSunbizMatching(
    parcelId,
    data.owner_name || data.own_name
  );

  // Get latest sale info to augment the property data (filters out sales ≤ $1,000)
  const latestSaleInfo = getLatestSaleInfo(salesData);

  // Combine property data with latest qualifying sale info
  const enhancedData = {
    ...data,
    ...latestSaleInfo
  };

  // Build last sale payload for SalesHistoryCard from hook (overrides internal fetch)
  const lastSaleFromHook = salesData?.most_recent_sale && salesData.most_recent_sale.sale_price > 1000
    ? {
        sale_date: salesData.most_recent_sale.sale_date,
        sale_price: salesData.most_recent_sale.sale_price,
        instrument_type: salesData.most_recent_sale.document_type || undefined,
        book_page: salesData.most_recent_sale.book && salesData.most_recent_sale.page
          ? `${salesData.most_recent_sale.book}/${salesData.most_recent_sale.page}`
          : undefined,
        qualification: salesData.most_recent_sale.qualified_sale ? 'Qualified' : 'Unqualified',
      }
    : null;

  // Use real sales data if available, NO mock data
  if (salesData && salesData.most_recent_sale && salesData.most_recent_sale.sale_price >= 1000) {
    const latestSale = salesData.most_recent_sale;
    enhancedData.sale_prc1 = latestSale.sale_price;
    enhancedData.sale_yr1 = latestSale.sale_year;
    enhancedData.sale_date = latestSale.sale_date;
    enhancedData.sale_month = latestSale.sale_month;
    enhancedData.sale_price = latestSale.sale_price;
    enhancedData.sale_qualification = latestSale.document_type;
  }

  // Helper function to get appraised value from multiple possible field names
  const getAppraisedValue = (data: any) => {
    // Check all possible appraised value field names
    const value = data.jv ||
                  data.just_value ||
                  data.appraised_value ||
                  data.market_value ||
                  data.assessed_value ||
                  data.total_value ||
                  data.property_value ||
                  data.current_value;

    // Debug logging only when value is not found
    if (!value) {
      console.log('getAppraisedValue - no value found, checking fields:', {
        jv: data.jv,
        just_value: data.just_value,
        appraised_value: data.appraised_value,
        market_value: data.market_value,
        assessed_value: data.assessed_value,
        total_value: data.total_value,
        property_value: data.property_value,
        current_value: data.current_value,
        available_keys: Object.keys(data).filter(key => key.toLowerCase().includes('val') || key.toLowerCase().includes('jv') || key.toLowerCase().includes('price'))
      });
    }
    return value;
  };

  // Helper function to get taxable value from API response or fallback fields
  const getTaxableValue = (data: any) => {
    // Use real taxable_value from API first, then fallback to other fields
    return data.taxable_value || data.tv_sd || data.tax_value;
  };

  // Helper function to get annual tax amount
  const getAnnualTax = (data: any) => {
    // Use real annual_tax from API first
    if (data.annual_tax) {
      return data.annual_tax;
    }

    // Fallback calculation using real millage rate from API if available
    const taxableValue = getTaxableValue(data);
    if (!taxableValue) return 0;

    // Use real tax_millage from API if available, otherwise use Florida average
    const millageRate = data.tax_millage || 17.2; // Florida average is 17.2 mills
    return (taxableValue * millageRate) / 1000; // Convert mills to actual rate
  };

  // Helper function to get year built from multiple possible field names
  const getYearBuilt = (data: any) => {
    const year = data.act_yr_blt ||
                 data.year_built ||
                 data.built_year ||
                 data.construction_year ||
                 data.yr_built;

    // Debug logging only when year is not found
    if (!year) {
      console.log('getYearBuilt - no year found, checking fields:', {
        act_yr_blt: data.act_yr_blt,
        year_built: data.year_built,
        built_year: data.built_year,
        construction_year: data.construction_year,
        yr_built: data.yr_built,
        available_keys: Object.keys(data).filter(key => key.toLowerCase().includes('year') || key.toLowerCase().includes('built') || key.toLowerCase().includes('yr'))
      });
    }

    return year || 'N/A';
  };

  // Helper function to get land value
  const getLandValue = (data: any) => {
    return data.lnd_val || data.land_value;
  };

  const formatCurrency = (value?: number) => {
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
      category = getPropertyCategory(data.property_use, data.property_type);
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

  // Grid variant - Modern, beautiful card design
  if (variant === 'grid') {
    return (
      <div
        id={`property-card-${parcelId}`}
        data-testid="property-card"
        className={`
          elegant-card group relative bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-xl
          transition-all duration-500 ease-out cursor-pointer overflow-hidden
          ${isSelected ? 'ring-2 ring-yellow-400 shadow-yellow-100' : ''}
          ${isWatched ? 'ring-2 ring-yellow-400 shadow-yellow-100' : ''}
          ${priority === 'high' ? 'border-l-4 border-l-red-400' : ''}
          ${priority === 'medium' ? 'border-l-4 border-l-yellow-400' : ''}
          hover:-translate-y-1 hover:scale-[1.02]
        `}
        onClick={handleCardClick}
        title={propertyTitle}
      >
        {/* Gold accent line - executive style */}
        <div className="absolute top-0 left-0 right-0 h-2" style={{background: 'linear-gradient(90deg, #d4af37 0%, transparent 100%)'}} />

        {/* Status indicators - top right */}
        <div className="absolute top-3 right-3 flex items-center gap-2 z-10">
          {isWatched && (
            <button
              className="flex items-center justify-center w-7 h-7 bg-yellow-50 rounded-full shadow-sm border border-yellow-200 hover:bg-yellow-100 transition-colors"
              onClick={handleWatchlistToggle}
              disabled={watchlistLoading}
              title="Remove from watchlist"
            >
              <Star className="w-4 h-4 text-yellow-600 fill-yellow-400" />
            </button>
          )}
          {hasNotes && (
            <div
              className="flex items-center justify-center w-7 h-7 bg-blue-50 rounded-full shadow-sm border border-blue-200"
              title={`${propertyNotes.length} note${propertyNotes.length !== 1 ? 's' : ''}`}
            >
              <span className="text-xs font-bold text-blue-600">{propertyNotes.length || 'N'}</span>
            </div>
          )}
          {onToggleSelection && (
            <button
              className="flex items-center justify-center w-7 h-7 bg-white rounded-full shadow-sm border border-gray-200 hover:border-gray-300 transition-colors"
              onClick={(e) => {
                e.stopPropagation();
                onToggleSelection();
              }}
            >
              {isSelected ? (
                <CheckSquare className="w-4 h-4 text-blue-600" />
              ) : (
                <Square className="w-4 h-4 text-gray-400" />
              )}
            </button>
          )}
        </div>

        <div className="p-6">
          {/* Property type badge */}
          <div className="mb-4">
            {getPropertyTypeBadge(data.property_use, data.property_type, data.owner_name || data.own_name, getAppraisedValue(data), !!(data.phy_addr1 && data.phy_addr1 !== '-'), data.propertyUse, data.propertyUseDesc, data.use_category, data.use_subcategory, data.use_description)}

            {/* Property Description */}
            {(data.use_description || data.propertyUseDesc) && (
              <div className="mt-2 px-2">
                <p className="text-xs text-gray-600 italic">
                  {data.use_description || data.propertyUseDesc}
                </p>
              </div>
            )}

            {/* Tax certificate and auction indicators */}
            <div className="flex flex-wrap gap-2 mt-2">
              {data.has_tax_certificates && (
                <Badge className="bg-orange-50 text-orange-700 border-orange-200 text-xs font-medium">
                  <AlertTriangle className="w-3 h-3 mr-1" />
                  {data.certificate_count} Certificate{data.certificate_count && data.certificate_count > 1 ? 's' : ''}
                </Badge>
              )}
              {data.auction_date && (
                <Badge className="bg-red-50 text-red-700 border-red-200 text-xs font-medium">
                  <Calendar className="w-3 h-3 mr-1" />
                  Tax Deed Auction
                </Badge>
              )}
            </div>
          </div>

          {/* Address Section */}
          <div className="mb-4">
            <a
              href={(() => {
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
              })()}
              target="_blank"
              rel="noopener noreferrer"
              className="group/address block"
              onClick={(e) => {
                if (!data.phy_addr1 && !data.owner_addr1 && !parcelId) {
                  e.preventDefault();
                } else {
                  e.stopPropagation();
                }
              }}
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center transition-colors" style={{backgroundColor: '#f4e5c2'}}>
                  <MapPin className="w-5 h-5" style={{color: '#2c3e50'}} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-sm mb-1 line-clamp-1 transition-colors flex items-center gap-1 hover:text-yellow-600" style={{color: '#2c3e50'}}>
                    {formatAddress()}
                    {(data.phy_addr1 || data.owner_addr1 || parcelId) && (
                      <ExternalLink className="w-3 h-3 opacity-0 group-hover/address:opacity-100 transition-opacity" />
                    )}
                  </p>
                  <p className="text-xs text-gray-500">
                    {data.phy_city || 'Unknown City'}, FL {data.phy_zipcd || ''}
                  </p>
                </div>
              </div>
            </a>
          </div>

          {/* Owner Section */}
          <div className="mb-5 pb-4 border-b border-gray-100">
            <div className="flex items-center gap-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center" style={{backgroundColor: '#f4e5c2'}}>
                <User className="w-4 h-4" style={{color: '#2c3e50'}} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium uppercase tracking-wider mb-1 text-gray-600">Owner</p>
                <p className="text-sm font-medium truncate" style={{color: '#2c3e50'}}>
                  {data.owner_name || data.own_name || 'Owner Not Available'}
                </p>
              </div>
            </div>
            {/* Parcel ID */}
            <div className="mt-3 text-xs text-gray-500">
              <span className="font-medium">Parcel:</span> {parcelId || data.parcel_id || 'N/A'}
            </div>
          </div>

          {/* Key Values - Featured prominently */}
          <div className="space-y-4 mb-5">
            {/* Primary Value - Appraised with AI Investment Grade */}
            <div className="text-center py-3 px-4 rounded-lg relative" style={{backgroundColor: '#f4e5c2'}}>
              {aiAnalysis?.investment_grade && (
                <div className="absolute top-2 right-2">
                  <Badge
                    className={`text-xs text-white ${getInvestmentGradeColor(aiAnalysis.investment_grade)}`}
                  >
                    <Brain className="w-3 h-3 mr-1" />
                    {aiAnalysis.investment_grade}
                  </Badge>
                </div>
              )}
              <p className="text-xs font-medium uppercase tracking-wider mb-1" style={{color: '#2c3e50'}}>Appraised Value</p>
              <p className="text-xl font-bold" style={{color: '#d4af37'}}>{formatCurrency(getAppraisedValue(data))}</p>
              {aiAnalysis?.investment_score && (
                <div className="mt-1 flex items-center justify-center gap-1">
                  <Star className="w-3 h-3 text-yellow-500 fill-yellow-500" />
                  <span className="text-xs font-medium text-gray-600">
                    AI Score: {aiAnalysis.investment_score}/100
                  </span>
                </div>
              )}
            </div>

            {/* Secondary Values Grid */}
            <div className="grid grid-cols-2 gap-3">
              {/* AI-Enhanced Sales History or Tax Info */}
              {salesData?.has_sales && salesData.last_sale_price ? (
                <div className="text-center p-3 bg-green-50 rounded-lg relative">
                  {salesData.price_trend && (
                    <div className="absolute top-1 right-1">
                      <span className="text-sm" title="Price trend">
                        {salesData.price_trend}
                      </span>
                    </div>
                  )}
                  <div className="flex items-center justify-center gap-1 mb-1">
                    <p className="text-xs font-medium text-green-600">Last Sale</p>
                    {salesData.total_sales > 1 && (
                      <Badge variant="outline" className="text-[10px] py-0 h-4">
                        <Activity className="w-2 h-2 mr-1" />
                        {salesData.total_sales}
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm font-semibold text-green-800">
                    {formatCurrency(salesData.last_sale_price)}
                  </p>
                  <p className="text-xs text-green-600 mt-1">
                    {formatDate(salesData.last_sale_date)}
                  </p>
                  {salesData.appreciation !== 0 && (
                    <div className="mt-1 flex items-center justify-center gap-1">
                      <TrendingUp className={`w-3 h-3 ${getAppreciationColor(salesData.appreciation)}`} />
                      <span className={`text-xs ${getAppreciationColor(salesData.appreciation)}`}>
                        {salesData.appreciation > 0 ? '+' : ''}{salesData.appreciation.toFixed(1)}%
                      </span>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center p-3 bg-orange-50 rounded-lg">
                  <p className="text-xs font-medium text-orange-600 mb-1">
                    Annual Tax {data.has_homestead && '(Homestead)'}
                  </p>
                  <p className="text-sm font-semibold text-orange-800">
                    {formatCurrency(getAnnualTax(data))}
                  </p>
                  {data.tax_millage && (
                    <p className="text-xs text-gray-500 mt-0.5">
                      {data.tax_millage} mills
                    </p>
                  )}
                </div>
              )}

              {/* Building/Land Info */}
              {data.tot_lvg_area ? (
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <p className="text-xs font-medium text-blue-600 mb-1">Building</p>
                  <p className="text-sm font-semibold text-blue-800">{formatArea(data.tot_lvg_area)}</p>
                </div>
              ) : data.lnd_sqfoot ? (
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs font-medium text-gray-600 mb-1">Land</p>
                  <p className="text-sm font-semibold text-gray-800">{formatArea(data.lnd_sqfoot)}</p>
                </div>
              ) : (
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs font-medium text-gray-600 mb-1">Year Built</p>
                  <p className="text-sm font-semibold text-gray-800">{getYearBuilt(data)}</p>
                </div>
              )}
            </div>

            {/* Special Alerts */}
            {data.has_tax_certificates && data.total_certificate_amount && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <AlertTriangle className="w-4 h-4 text-red-600" />
                  <p className="text-xs font-medium text-red-600 uppercase tracking-wider">Tax Liens</p>
                </div>
                <p className="text-sm font-semibold text-red-800">{formatCurrency(data.total_certificate_amount)}</p>
              </div>
            )}

            {data.auction_date && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <Calendar className="w-4 h-4 text-red-600" />
                  <p className="text-xs font-medium text-red-600 uppercase tracking-wider">Auction Date</p>
                </div>
                <p className="text-sm font-semibold text-red-800">
                  {new Date(data.auction_date).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
                </p>
                {data.opening_bid && (
                  <p className="text-xs text-red-600 mt-1">Starting bid: {formatCurrency(data.opening_bid)}</p>
                )}
              </div>
            )}
          </div>

          {/* AI Insights Section */}
          {(salesData?.quick_insight || aiAnalysis?.investment_insights) && (
            <div className="mb-4 p-3 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200">
              <div className="flex items-center gap-2 mb-2">
                <Brain className="w-4 h-4 text-purple-600" />
                <p className="text-xs font-medium text-purple-600 uppercase tracking-wider">AI Insights</p>
                {salesLoading && <Loader2 className="w-3 h-3 animate-spin text-purple-600" />}
              </div>

              {salesData?.quick_insight && (
                <p className="text-sm text-purple-800 mb-2">{salesData.quick_insight}</p>
              )}

              {aiAnalysis?.market_activity && (
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs text-purple-700">Market Activity:</span>
                  <Badge variant="outline" className="text-[10px] py-0 h-5 border-purple-300">
                    {aiAnalysis.market_activity.activity_emoji} {aiAnalysis.market_activity.activity_level}
                  </Badge>
                </div>
              )}

              {aiAnalysis?.investment_insights?.insights && aiAnalysis.investment_insights.insights.length > 0 && (
                <div className="text-xs text-purple-700 space-y-1">
                  {aiAnalysis.investment_insights.insights.slice(0, 2).map((insight, index) => (
                    <div key={index} className="flex items-start gap-1">
                      <span className="text-purple-400">•</span>
                      <span>{insight}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* NAV Assessments Section */}
          {navData && navData.assessments.length > 0 && (
            <div className="mb-4 p-3 bg-gradient-to-r from-green-50 to-teal-50 rounded-lg border border-green-200">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Receipt className="w-4 h-4 text-green-600" />
                  <p className="text-xs font-medium text-green-600 uppercase tracking-wider">NAV Assessments</p>
                  {navLoading && <Loader2 className="w-3 h-3 animate-spin text-green-600" />}
                </div>
                <Badge variant="outline" className="text-[10px] py-0 h-5 border-green-300">
                  {navData.assessment_count} items
                </Badge>
              </div>

              <div className="space-y-2">
                {navData.assessments.slice(0, 2).map((assessment, index) => (
                  <div key={index} className="flex items-center justify-between text-xs">
                    <span className="flex items-center gap-1 text-green-800 truncate max-w-32">
                      <span>🏛️</span>
                      <span className="truncate">{assessment.assessment_description}</span>
                    </span>
                    <span className="font-medium text-green-900">
                      ${assessment.assessment_amount.toFixed(0)}
                    </span>
                  </div>
                ))}

                {navData.assessments.length > 2 && (
                  <p className="text-xs text-green-600 text-center">
                    +{navData.assessments.length - 2} more assessments
                  </p>
                )}

                <div className="flex items-center justify-between pt-1 border-t border-green-200">
                  <span className="text-xs font-medium text-green-700">Total NAV:</span>
                  <span className="text-sm font-bold text-green-900">
                    ${navData.total_assessments.toFixed(0)}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Enhanced Sales History Section - Dynamic data from Supabase */}
          <div className="mb-5">
            <SalesHistoryCard
              parcelId={parcelId}
              county={data.county || data.phy_city || 'Unknown'}
              lastQualifiedSale={lastSaleFromHook || data.last_qualified_sale}
              hasQualifiedSale={Boolean(lastSaleFromHook) || Boolean(data.has_qualified_sale)}
            />
          </div>

          {/* Actions */}
          {showQuickActions && (
            <div className="flex items-center justify-between pt-4 border-t border-gray-100">
              <Button
                size="sm"
                variant="ghost"
                className={`h-8 px-3 text-xs font-medium transition-all duration-200 ${
                  hasMatches
                    ? 'bg-green-50 text-green-700 border border-green-200 hover:bg-green-100'
                    : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
                }`}
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
                <Eye className="w-3 h-3 mr-1.5" />
                {hasMatches ? (
                  <span className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
                    Match Found
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
                    className="h-8 w-8 p-0 text-gray-600 hover:text-gray-800 hover:bg-gray-50 transition-colors"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <MoreVertical className="w-4 h-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48">
                  <DropdownMenuItem
                    onClick={(e) => {
                      e.stopPropagation();
                      navigateToProperty({ parcelId, ...data });
                    }}
                  >
                    <Eye className="w-4 h-4 mr-2" />
                    View Full Details
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={(e) => {
                      e.stopPropagation();
                      handleWatchlistToggle(e);
                    }}
                    disabled={watchlistLoading}
                  >
                    <Star className={`w-4 h-4 mr-2 ${isInWatchlist(parcelId) ? 'fill-yellow-400 text-yellow-600' : ''}`} />
                    {isInWatchlist(parcelId) ? 'Remove from Watchlist' : 'Add to Watchlist'}
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

          {/* Parcel ID Footer */}
          <div className="mt-4 pt-3 border-t border-gray-100">
            <p className="text-xs text-gray-400 font-mono">Parcel: {parcelId}</p>
          </div>
        </div>
      </div>
    );
  }

  // List variant - Modern horizontal layout
  return (
    <div
      id={`property-card-list-${parcelId}`}
      data-testid="property-card-list"
      className={`
        group relative bg-white rounded-lg border border-gray-100 shadow-sm hover:shadow-lg
        transition-all duration-300 ease-out cursor-pointer p-4
        ${isSelected ? 'ring-2 ring-blue-400 bg-blue-50/30' : ''}
        ${isWatched ? 'ring-2 ring-yellow-400 bg-yellow-50/30' : ''}
        ${priority === 'high' ? 'border-l-4 border-l-red-400' : ''}
        ${priority === 'medium' ? 'border-l-4 border-l-yellow-400' : ''}
        hover:scale-[1.01]
      `}
      onClick={handleCardClick}
      title={propertyTitle}
    >
      <div className="flex items-center justify-between gap-4">
        {/* Left section - Property info */}
        <div className="flex items-center gap-4 flex-1 min-w-0">
          {/* Property type badge */}
          <div className="flex-shrink-0">
            {getPropertyTypeBadge(data.property_use, data.property_type, data.owner_name || data.own_name, getAppraisedValue(data), !!(data.phy_addr1 && data.phy_addr1 !== '-'), data.propertyUse, data.propertyUseDesc, data.use_category, data.use_subcategory, data.use_description)}
          </div>

          {/* Address */}
          <div className="min-w-0 flex-1">
            <a
              href={(() => {
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
              })()}
              target="_blank"
              rel="noopener noreferrer"
              className="group/address block"
              onClick={(e) => {
                if (!data.phy_addr1 && !data.owner_addr1 && !parcelId) {
                  e.preventDefault();
                } else {
                  e.stopPropagation();
                }
              }}
            >
              <p className="font-semibold text-sm text-gray-900 mb-1 truncate group-hover/address:text-blue-600 transition-colors flex items-center gap-1">
                {formatAddress()}
                {(data.phy_addr1 || data.owner_addr1 || parcelId) && (
                  <ExternalLink className="w-3 h-3 opacity-0 group-hover/address:opacity-100 transition-opacity flex-shrink-0" />
                )}
              </p>
            </a>
            <p className="text-xs text-gray-500">
              {data.phy_city || 'Unknown City'}, FL {data.phy_zipcd || ''} • Parcel: {parcelId}
            </p>
          </div>
        </div>

        {/* Owner section */}
        <div className="min-w-0 flex-1 max-w-xs px-4">
          <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">Owner</p>
          <p className="text-sm font-medium text-gray-900 truncate">
            {data.owner_name || data.own_name || 'Owner Not Available'}
          </p>
        </div>

        {/* Values section */}
        <div className="flex items-center gap-6">
          {/* Last Sale */}
          {((enhancedData.sale_prc1 && enhancedData.sale_prc1 > 1000) || (enhancedData.last_sale_price && enhancedData.last_sale_price > 1000)) && (
            <div className="text-center px-3 py-2 bg-green-50 rounded-lg">
              <p className="text-xs font-medium text-green-600 mb-1">Last Sale</p>
              <p className="text-sm font-semibold text-green-800">
                {formatCurrency(enhancedData.sale_prc1 || enhancedData.last_sale_price)}
              </p>
              <p className="text-xs text-green-600">
                {formatSaleDate(
                  enhancedData.sale_date || enhancedData.last_sale_date,
                  enhancedData.sale_yr1 || enhancedData.last_sale_year,
                  enhancedData.sale_month
                )}
              </p>
            </div>
          )}

          {/* Appraised Value */}
          <div className="text-center px-3 py-2 bg-blue-50 rounded-lg">
            <p className="text-xs font-medium text-blue-600 mb-1">Appraised</p>
            <p className="text-sm font-bold text-blue-800">{formatCurrency(getAppraisedValue(data))}</p>
          </div>

          {/* Building/Land */}
          {data.tot_lvg_area ? (
            <div className="text-center px-3 py-2 bg-gray-50 rounded-lg">
              <p className="text-xs font-medium text-gray-600 mb-1">Building</p>
              <p className="text-sm font-semibold text-gray-800">{formatArea(data.tot_lvg_area)}</p>
            </div>
          ) : data.lnd_sqfoot && (
            <div className="text-center px-3 py-2 bg-gray-50 rounded-lg">
              <p className="text-xs font-medium text-gray-600 mb-1">Land</p>
              <p className="text-sm font-semibold text-gray-800">{formatArea(data.lnd_sqfoot)}</p>
            </div>
          )}
        </div>

        {/* Status indicators and actions */}
        <div className="flex items-center gap-3 ml-4">
          {/* Status indicators */}
          <div className="flex items-center gap-2">
            {isWatched && (
              <button
                className="flex items-center justify-center w-8 h-8 bg-yellow-50 rounded-full border border-yellow-200 hover:bg-yellow-100 transition-colors"
                onClick={handleWatchlistToggle}
                disabled={watchlistLoading}
                title="Remove from watchlist"
              >
                <Star className="w-4 h-4 text-yellow-600 fill-yellow-400" />
              </button>
            )}
            {hasNotes && (
              <div
                className="flex items-center justify-center w-8 h-8 bg-blue-50 rounded-full border border-blue-200"
                title={`${propertyNotes.length} note${propertyNotes.length !== 1 ? 's' : ''}`}
              >
                <span className="text-xs font-bold text-blue-600">{propertyNotes.length || 'N'}</span>
              </div>
            )}
            {onToggleSelection && (
              <button
                className="flex items-center justify-center w-8 h-8 bg-white rounded-full border border-gray-200 hover:border-gray-300 transition-colors"
                onClick={(e) => {
                  e.stopPropagation();
                  onToggleSelection();
                }}
              >
                {isSelected ? (
                  <CheckSquare className="w-4 h-4 text-blue-600" />
                ) : (
                  <Square className="w-4 h-4 text-gray-400" />
                )}
              </button>
            )}
          </div>

          {/* Actions */}
          {showQuickActions && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-8 w-8 p-0 text-gray-600 hover:text-gray-800 hover:bg-gray-50 transition-colors"
                  onClick={(e) => e.stopPropagation()}
                >
                  <MoreVertical className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem
                  onClick={(e) => {
                    e.stopPropagation();
                    navigateToProperty({ parcelId, ...data });
                  }}
                >
                  <Eye className="w-4 h-4 mr-2" />
                  View Full Details
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={(e) => {
                    e.stopPropagation();
                    handleWatchlistToggle(e);
                  }}
                  disabled={watchlistLoading}
                >
                  <Star className={`w-4 h-4 mr-2 ${isInWatchlist(parcelId) ? 'fill-yellow-400 text-yellow-600' : ''}`} />
                  {isInWatchlist(parcelId) ? 'Remove from Watchlist' : 'Add to Watchlist'}
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Phone className="w-4 h-4 mr-2" />
                  Contact Owner
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </div>
    </div>
  );
}

export default MiniPropertyCard;
