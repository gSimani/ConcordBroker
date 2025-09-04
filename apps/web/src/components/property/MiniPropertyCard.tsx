import React from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
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
  Building
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface MiniPropertyCardProps {
  parcelId: string;
  data: {
    PHY_ADDR1?: string;
    PHY_CITY?: string;
    PHY_ZIPCD?: string;
    OWN_NAME?: string;
    JV?: number;
    TV_SD?: number;
    LND_VAL?: number;
    TOT_LVG_AREA?: number;
    LND_SQFOOT?: number;
    ACT_YR_BLT?: number;
    DOR_UC?: string;
    SALE_PRC1?: number;
    SALE_YR1?: number;
    JV_CHNG?: number;
    JV_HMSTD?: number;
    NO_RES_UNTS?: number;
  };
  onClick?: () => void;
  variant?: 'grid' | 'list';
  showQuickActions?: boolean;
  isWatched?: boolean;
  hasNotes?: boolean;
  priority?: 'low' | 'medium' | 'high';
}

// Property type badges with colors
const getPropertyTypeBadge = (useCode?: string) => {
  if (!useCode) return null;
  
  const firstDigit = useCode.charAt(0);
  switch (firstDigit) {
    case '0':
      return <Badge className="bg-green-100 text-green-800 border-green-200">Residential</Badge>;
    case '1':
      return <Badge className="bg-blue-100 text-blue-800 border-blue-200">Commercial</Badge>;
    case '2':
      return <Badge className="bg-purple-100 text-purple-800 border-purple-200">Industrial</Badge>;
    case '3':
      return <Badge className="bg-yellow-100 text-yellow-800 border-yellow-200">Agricultural</Badge>;
    case '4':
    case '5':
      return <Badge className="bg-gray-100 text-gray-800 border-gray-200">Institutional</Badge>;
    default:
      return <Badge variant="outline">Other</Badge>;
  }
};

export function MiniPropertyCard({ 
  parcelId, 
  data, 
  onClick, 
  variant = 'grid',
  showQuickActions = true,
  isWatched = false,
  hasNotes = false,
  priority
}: MiniPropertyCardProps) {
  
  const formatCurrency = (value?: number) => {
    if (!value) return 'N/A';
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    }
    if (value >= 1000) {
      return `$${(value / 1000).toFixed(0)}K`;
    }
    return `$${value}`;
  };

  const formatArea = (sqft?: number) => {
    if (!sqft) return 'N/A';
    if (sqft >= 43560) {
      return `${(sqft / 43560).toFixed(1)} acres`;
    }
    return `${(sqft / 1000).toFixed(1)}K sqft`;
  };

  const getValueTrend = () => {
    if (!data.JV_CHNG) return null;
    const changePercent = (data.JV_CHNG / ((data.JV || 0) - data.JV_CHNG)) * 100;
    
    if (changePercent > 0) {
      return (
        <div className="flex items-center text-green-600 text-xs">
          <TrendingUp className="w-3 h-3 mr-1" />
          <span>+{changePercent.toFixed(0)}%</span>
        </div>
      );
    } else if (changePercent < 0) {
      return (
        <div className="flex items-center text-red-600 text-xs">
          <TrendingDown className="w-3 h-3 mr-1" />
          <span>{changePercent.toFixed(0)}%</span>
        </div>
      );
    }
    return null;
  };

  // Grid variant - Compact card
  if (variant === 'grid') {
    return (
      <Card 
        className={`
          relative p-4 hover:shadow-lg transition-all cursor-pointer
          ${priority === 'high' ? 'ring-2 ring-red-500' : ''}
          ${priority === 'medium' ? 'ring-2 ring-yellow-500' : ''}
        `}
        onClick={onClick}
      >
        {/* Status indicators */}
        <div className="absolute top-2 right-2 flex items-center space-x-1">
          {isWatched && (
            <div className="p-1 bg-yellow-100 rounded">
              <Star className="w-3 h-3 text-yellow-600 fill-current" />
            </div>
          )}
          {hasNotes && (
            <div className="p-1 bg-blue-100 rounded">
              <span className="text-xs font-bold text-blue-600">N</span>
            </div>
          )}
          {data.JV_HMSTD && (
            <div className="p-1 bg-green-100 rounded">
              <Home className="w-3 h-3 text-green-600" />
            </div>
          )}
        </div>

        {/* Property Type Badge */}
        <div className="mb-2">
          {getPropertyTypeBadge(data.DOR_UC)}
        </div>

        {/* Address */}
        <div className="mb-3">
          <p className="font-semibold text-sm truncate">
            {data.PHY_ADDR1 || 'No Street Address'}
          </p>
          <p className="text-xs text-gray-500">
            {data.PHY_CITY}, FL {data.PHY_ZIPCD}
          </p>
        </div>

        {/* Key Values */}
        <div className="grid grid-cols-2 gap-2 mb-3">
          <div>
            <p className="text-xs text-gray-500">Value</p>
            <p className="font-bold text-lg">{formatCurrency(data.JV)}</p>
            {getValueTrend()}
          </div>
          <div>
            <p className="text-xs text-gray-500">Size</p>
            <p className="font-semibold">
              {data.TOT_LVG_AREA ? `${(data.TOT_LVG_AREA / 1000).toFixed(1)}K sqft` : formatArea(data.LND_SQFOOT)}
            </p>
            {data.ACT_YR_BLT && (
              <p className="text-xs text-gray-500">Built {data.ACT_YR_BLT}</p>
            )}
          </div>
        </div>

        {/* Owner */}
        <div className="mb-3 pb-3 border-b">
          <p className="text-xs text-gray-500 mb-1">Owner</p>
          <p className="text-sm font-medium truncate">{data.OWN_NAME}</p>
        </div>

        {/* Recent Sale */}
        {data.SALE_PRC1 && (
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center text-gray-600">
              <Calendar className="w-3 h-3 mr-1" />
              <span>Sold {data.SALE_YR1}</span>
            </div>
            <span className="font-semibold">{formatCurrency(data.SALE_PRC1)}</span>
          </div>
        )}

        {/* Quick Actions */}
        {showQuickActions && (
          <div className="mt-3 flex justify-between items-center">
            <Button 
              size="sm" 
              variant="ghost" 
              className="h-7 px-2"
              onClick={(e) => {
                e.stopPropagation();
                // Open full profile
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
                  className="h-7 w-7 p-0"
                  onClick={(e) => e.stopPropagation()}
                >
                  <MoreVertical className="w-4 h-4" />
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
        <div className="mt-2 pt-2 border-t">
          <p className="text-xs text-gray-400">ID: {parcelId}</p>
        </div>
      </Card>
    );
  }

  // List variant - Horizontal layout
  return (
    <Card 
      className={`
        relative p-3 hover:shadow-md transition-all cursor-pointer
        ${priority === 'high' ? 'border-l-4 border-l-red-500' : ''}
        ${priority === 'medium' ? 'border-l-4 border-l-yellow-500' : ''}
      `}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        {/* Left section - Address & Type */}
        <div className="flex items-center space-x-4 flex-1 min-w-0">
          <div className="flex-shrink-0">
            {data.DOR_UC?.startsWith('0') && <Home className="w-5 h-5 text-green-600" />}
            {data.DOR_UC?.startsWith('1') && <Building className="w-5 h-5 text-blue-600" />}
            {!data.DOR_UC?.match(/^[01]/) && <MapPin className="w-5 h-5 text-gray-600" />}
          </div>
          
          <div className="min-w-0 flex-1">
            <div className="flex items-center space-x-2 mb-1">
              <p className="font-semibold text-sm truncate">
                {data.PHY_ADDR1 || 'No Street Address'}
              </p>
              {getPropertyTypeBadge(data.DOR_UC)}
            </div>
            <p className="text-xs text-gray-500">
              {data.PHY_CITY}, FL {data.PHY_ZIPCD} • {parcelId}
            </p>
          </div>
        </div>

        {/* Middle section - Owner */}
        <div className="px-4 min-w-0 flex-1 max-w-xs">
          <p className="text-xs text-gray-500 mb-1">Owner</p>
          <p className="text-sm font-medium truncate">{data.OWN_NAME}</p>
        </div>

        {/* Values section */}
        <div className="flex items-center space-x-6">
          <div className="text-right">
            <p className="text-xs text-gray-500">Value</p>
            <p className="font-bold">{formatCurrency(data.JV)}</p>
            {getValueTrend()}
          </div>
          
          <div className="text-right">
            <p className="text-xs text-gray-500">Size</p>
            <p className="font-semibold">
              {data.TOT_LVG_AREA ? `${(data.TOT_LVG_AREA / 1000).toFixed(1)}K sqft` : formatArea(data.LND_SQFOOT)}
            </p>
          </div>

          {data.SALE_PRC1 && (
            <div className="text-right">
              <p className="text-xs text-gray-500">Last Sale</p>
              <p className="font-semibold">{formatCurrency(data.SALE_PRC1)}</p>
              <p className="text-xs text-gray-500">{data.SALE_YR1}</p>
            </div>
          )}
        </div>

        {/* Status indicators */}
        <div className="flex items-center space-x-2 ml-4">
          {isWatched && <Star className="w-4 h-4 text-yellow-500 fill-current" />}
          {hasNotes && (
            <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
              <span className="text-xs font-bold text-blue-600">3</span>
            </div>
          )}
          {data.JV_HMSTD && <Home className="w-4 h-4 text-green-500" />}
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