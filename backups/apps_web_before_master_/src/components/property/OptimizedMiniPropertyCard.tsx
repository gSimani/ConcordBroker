import React, { memo, useCallback, useMemo } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import '@/styles/elegant-property.css';
import {
  MapPin,
  DollarSign,
  User,
  Square,
  Calendar,
  Eye,
  Star,
  MoreVertical,
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

// Optimized interfaces
interface PropertyData {
  phy_addr1?: string;
  phy_city?: string;
  phy_zipcd?: string;
  own_name?: string;
  owner_name?: string;
  jv?: number;
  tv_sd?: number;
  lnd_val?: number;
  tot_lvg_area?: number;
  lnd_sqfoot?: number;
  act_yr_blt?: number;
  dor_uc?: string;
  propertyUse?: string | number;
  propertyType?: string | number;
  propertyUseDesc?: string;
  sale_prc1?: number;
  sale_yr1?: number;
  has_tax_certificates?: boolean;
  certificate_count?: number;
  auction_date?: string;
  opening_bid?: number;
  total_certificate_amount?: number;
  owner_addr1?: string;
}

interface OptimizedMiniPropertyCardProps {
  parcelId: string;
  data: PropertyData;
  onClick?: () => void;
  variant?: 'grid' | 'list';
  showQuickActions?: boolean;
  isWatched?: boolean;
  hasNotes?: boolean;
  priority?: 'low' | 'medium' | 'high';
  isSelected?: boolean;
  onToggleSelection?: () => void;
}

// Memoized property category function
const getPropertyCategory = memo((useCode?: string): string => {
  const code = String(useCode || '').trim();

  if (code === '0' || code === '00') return 'Vacant Land';
  if (['1', '01', '2', '02', '3', '03'].includes(code)) return 'Residential';
  if (['4', '04', '5', '05', '6', '06', '7', '07'].includes(code)) return 'Commercial';
  if (['8', '08', '9', '09'].includes(code)) return 'Industrial';
  if (['10', '11', '12'].includes(code)) return 'Agricultural';
  if (code.startsWith('9')) return 'Government';

  return 'Unknown';
});

// Memoized currency formatter
const formatCurrency = (value?: number): string => {
  if (!value && value !== 0) return 'N/A';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

// Memoized area formatter
const formatArea = (sqft?: number): string => {
  if (!sqft) return 'N/A';
  return `${sqft.toLocaleString()} sqft`;
};

// Memoized date formatter
const formatDate = (date?: string): string => {
  if (!date) return 'N/A';
  try {
    return new Date(date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return 'N/A';
  }
};

// Memoized property type badge component
const PropertyTypeBadge = memo(({ category }: { category: string }) => {
  const badgeProps = useMemo(() => {
    switch (category) {
      case 'Residential':
        return { className: "bg-green-100 text-green-800 border-green-200 font-medium", text: "Residential" };
      case 'Commercial':
        return { className: "bg-blue-100 text-blue-800 border-blue-200 font-medium", text: "Commercial" };
      case 'Industrial':
        return { className: "bg-orange-100 text-orange-800 border-orange-200 font-medium", text: "Industrial" };
      case 'Agricultural':
        return { className: "bg-yellow-100 text-yellow-800 border-yellow-200 font-medium", text: "Agricultural" };
      case 'Vacant Land':
        return { className: "bg-gray-100 text-gray-800 border-gray-200 font-medium", text: "Vacant Land" };
      case 'Government':
        return { className: "bg-red-100 text-red-800 border-red-200 font-medium", text: "Government" };
      default:
        return { className: "bg-gray-100 text-gray-600 border-gray-200 font-medium", text: "Unknown" };
    }
  }, [category]);

  return <Badge className={badgeProps.className}>{badgeProps.text}</Badge>;
});

PropertyTypeBadge.displayName = 'PropertyTypeBadge';

// Main optimized component
const OptimizedMiniPropertyCard = memo<OptimizedMiniPropertyCardProps>(({
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
}) => {
  // Memoized computed values
  const propertyCategory = useMemo(() => getPropertyCategory(data.dor_uc), [data.dor_uc]);

  const formattedAddress = useMemo(() => {
    if (!data.phy_addr1 || data.phy_addr1 === '-' || data.phy_addr1 === 'No Street Address') {
      if (data.owner_addr1 && data.owner_addr1 !== '-') {
        return data.owner_addr1;
      }
      return 'Address Not Available';
    }
    return data.phy_addr1;
  }, [data.phy_addr1, data.owner_addr1]);

  const googleMapsUrl = useMemo(() => {
    if (data.phy_addr1 && data.phy_city && data.phy_addr1 !== '-' && data.phy_addr1 !== 'No Street Address') {
      return `https://www.google.com/maps/search/${encodeURIComponent(
        `${data.phy_addr1}, ${data.phy_city}, FL ${data.phy_zipcd || ''}`
      )}`;
    } else if (data.owner_addr1 && data.owner_addr1 !== '-') {
      return `https://www.google.com/maps/search/${encodeURIComponent(`${data.owner_addr1}, FL`)}`;
    } else if (parcelId) {
      return `https://www.google.com/maps/search/${encodeURIComponent(`Parcel ${parcelId} Florida`)}`;
    }
    return '#';
  }, [data.phy_addr1, data.phy_city, data.phy_zipcd, data.owner_addr1, parcelId]);

  const appraisedValue = useMemo(() => data.jv || 0, [data.jv]);
  const ownerName = useMemo(() => data.owner_name || data.own_name || 'Owner Not Available', [data.owner_name, data.own_name]);

  // Latest sale info via Supabase (filters out < $1,000)
  const { salesData } = useSalesData(parcelId);
  const latestSaleInfo = getLatestSaleInfo(salesData);

  // Memoized event handlers
  const handleClick = useCallback(() => {
    onClick?.();
  }, [onClick]);

  const handleSelectionToggle = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    onToggleSelection?.();
  }, [onToggleSelection]);

  const handleSunbizClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    if (ownerName) {
      const searchName = ownerName.replace(/LLC$|INC$|CORP$|LP$|LLP$/i, '').trim();
      window.open(
        `https://search.sunbiz.org/Inquiry/CorporationSearch/SearchResults?inquiryType=EntityName&searchNameOrder=&searchTerm=${encodeURIComponent(searchName)}`,
        '_blank'
      );
    }
  }, [ownerName]);

  const handleMapsClick = useCallback((e: React.MouseEvent) => {
    if (!data.phy_addr1 && !data.owner_addr1 && !parcelId) {
      e.preventDefault();
    } else {
      e.stopPropagation();
    }
  }, [data.phy_addr1, data.owner_addr1, parcelId]);

  // Grid variant (optimized)
  if (variant === 'grid') {
    return (
      <div
        className={`
          elegant-card hover-lift cursor-pointer animate-in
          ${priority === 'high' ? 'ring-2 ring-red-500' : ''}
          ${priority === 'medium' ? 'ring-2 ring-yellow-500' : ''}
          ${isSelected ? 'ring-2 ring-yellow-400 bg-yellow-50/30' : ''}
        `}
        onClick={handleClick}
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
              onClick={handleSelectionToggle}
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
          {/* Property Type Badge */}
          <div className="mb-2 flex items-center justify-between">
            <PropertyTypeBadge category={propertyCategory} />
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
                  onClick={handleMapsClick}
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
                <p className="text-xs font-medium truncate" style={{color: '#2c3e50'}}>{ownerName}</p>
              </div>
            </div>
          </div>

          {/* Key Metrics */}
          <div className="space-y-1.5">
            {/* Sale Price or Tax Info */}
            {data.sale_prc1 && data.sale_prc1 > 1000 ? (
              <div className="flex items-center justify-between">
                <span className="text-xs" style={{color: '#95a5a6'}}>Last Sold</span>
                <div className="text-right">
                  <span className="font-semibold text-sm" style={{color: '#2c3e50'}}>{formatCurrency(data.sale_prc1)}</span>
                  {data.sale_yr1 && (
                    <span className="text-sm ml-1 font-medium" style={{color: '#7f8c8d'}}>({data.sale_yr1})</span>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <span className="text-xs" style={{color: '#95a5a6'}}>Annual Tax</span>
                <span className="font-semibold text-sm" style={{color: '#2c3e50'}}>
                  {formatCurrency(data.tv_sd ? data.tv_sd * 0.02 : 0)}
                </span>
              </div>
            )}

            {/* Appraised Value */}
            <div className="flex items-center justify-between">
              <span className="text-xs" style={{color: '#95a5a6'}}>Appraised</span>
              <span className="font-semibold text-sm" style={{color: '#d4af37'}}>{formatCurrency(appraisedValue)}</span>
            </div>

            {/* Building Sq Ft */}
            {data.tot_lvg_area && (
              <div className="flex items-center justify-between">
                <span className="text-xs" style={{color: '#95a5a6'}}>Building</span>
                <span className="font-semibold text-xs" style={{color: '#2c3e50'}}>{formatArea(data.tot_lvg_area)}</span>
              </div>
            )}

            {/* Land Sq Ft */}
            {data.lnd_sqfoot && (
              <div className="flex items-center justify-between">
                <span className="text-xs" style={{color: '#95a5a6'}}>Land</span>
                <span className="font-semibold text-xs" style={{color: '#2c3e50'}}>{formatArea(data.lnd_sqfoot)}</span>
              </div>
            )}

            {/* Year Built */}
            {data.act_yr_blt && (
              <div className="flex items-center justify-between">
                <span className="text-xs" style={{color: '#95a5a6'}}>Built</span>
                <span className="font-semibold text-xs" style={{color: '#2c3e50'}}>{data.act_yr_blt}</span>
              </div>
            )}
          </div>

          {/* Last Sale (from Supabase, > $1,000) */}
          {((latestSaleInfo.sale_prc1 && latestSaleInfo.sale_prc1 > 1000) || (data.sale_prc1 && data.sale_prc1 > 1000)) && (
            <div className="mt-2" style={{borderTop: '1px solid #ecf0f1', paddingTop: '8px'}}>
              <div className="flex items-center justify-between">
                <span className="text-xs" style={{color: '#95a5a6'}}>Last Sale</span>
                <span className="font-semibold text-xs" style={{color: '#2c3e50'}}>
                  {formatCurrency(latestSaleInfo.sale_prc1 || data.sale_prc1)}
                </span>
              </div>
              <div className="text-right text-[11px]" style={{color: '#7f8c8d'}}>
                {formatDate((salesData?.most_recent_sale?.sale_date as any) || undefined)}
              </div>
            </div>
          )}

          {/* Quick Actions */}
          {showQuickActions && (
            <div className="mt-3 pt-2 flex justify-between items-center" style={{borderTop: '1px solid #ecf0f1'}}>
              <Button
                size="sm"
                variant="ghost"
                className="hover-lift h-6 px-2"
                style={{color: '#2c3e50'}}
                onClick={handleSunbizClick}
              >
                <Eye className="w-3 h-3 mr-1" />
                View Sunbiz
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

  // List variant (simplified for performance)
  return (
    <Card
      className={`
        relative p-3 hover:shadow-md transition-all cursor-pointer
        ${priority === 'high' ? 'border-l-4 border-l-red-500' : ''}
        ${priority === 'medium' ? 'border-l-4 border-l-yellow-500' : ''}
        ${isSelected ? 'ring-2 ring-yellow-400 bg-yellow-50/30' : ''}
      `}
      onClick={handleClick}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4 flex-1 min-w-0">
          <div className="min-w-0 flex-1">
            <div className="flex items-center space-x-2 mb-1">
              <PropertyTypeBadge category={propertyCategory} />
              <p className="font-semibold text-sm truncate">{formattedAddress}</p>
            </div>
            <p className="text-xs text-gray-500">
              {data.phy_city || 'Unknown City'}, FL {data.phy_zipcd || ''} • Parcel: {parcelId}
            </p>
          </div>
        </div>

        <div className="px-4 min-w-0 flex-1 max-w-xs">
          <p className="text-xs text-gray-500 mb-1">Owner</p>
          <p className="text-sm font-medium truncate">{ownerName}</p>
        </div>

        <div className="flex items-center space-x-6">
          {(latestSaleInfo.sale_prc1 && latestSaleInfo.sale_prc1 > 1000) || (data.sale_prc1 && data.sale_prc1 > 1000) ? (
            <div className="text-right">
              <p className="text-xs text-gray-500">Last Sale</p>
              <p className="font-semibold">{formatCurrency(latestSaleInfo.sale_prc1 || data.sale_prc1)}</p>
              <p className="text-[11px] text-gray-500">
                {formatDate((salesData?.most_recent_sale?.sale_date as any) || undefined)}
              </p>
            </div>
          ) : null}

          <div className="text-right">
            <p className="text-xs text-gray-500">Appraised</p>
            <p className="font-bold text-green-600">{formatCurrency(appraisedValue)}</p>
          </div>
        </div>

        {onToggleSelection && (
          <div
            className="hover:bg-gray-100 p-1 rounded ml-4"
            onClick={handleSelectionToggle}
          >
            {isSelected ? (
              <CheckSquare className="w-4 h-4" style={{color: '#d4af37'}} />
            ) : (
              <Square className="w-4 h-4" style={{color: '#95a5a6'}} />
            )}
          </div>
        )}
      </div>
    </Card>
  );
});

OptimizedMiniPropertyCard.displayName = 'OptimizedMiniPropertyCard';

export { OptimizedMiniPropertyCard };
