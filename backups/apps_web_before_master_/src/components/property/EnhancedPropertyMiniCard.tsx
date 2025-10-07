import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
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
  ExternalLink,
  Building,
  Home,
  AlertTriangle,
  CheckCircle,
  Phone,
  Mail,
  Target,
  BarChart3,
  Percent,
  Clock,
  Zap,
  Shield,
  Award,
  Activity
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useCompletePropertyData } from '@/hooks/useCompletePropertyData';
import { motion } from 'framer-motion';

interface PropertyMiniCardData {
  parcel_id: string;
  phy_addr1?: string;
  phy_city?: string;
  phy_state?: string;
  phy_zipcd?: string;
  own_name?: string;      // Actual field name used
  owner_name?: string;    // Backup field name
  jv?: number;           // Just value - actual field name used
  just_value?: number;   // Backup field name
  market_value?: number; // Backup field name
  tv_sd?: number;        // Taxable value - actual field name
  assessed_value?: number; // Backup field name
  lnd_val?: number;      // Land value - actual field name
  land_value?: number;   // Backup field name
  bld_val?: number;      // Building value - actual field name
  building_value?: number; // Backup field name
  tot_lvg_area?: number; // Building sqft - actual field name
  building_sqft?: number; // Backup field name
  lnd_sqfoot?: number;   // Land sqft - actual field name
  land_sqft?: number;    // Backup field name
  act_yr_blt?: number;   // Year built - actual field name
  year_built?: number;   // Backup field name
  propertyUse?: string | number;  // Property use code
  property_use?: string;          // Backup field name
  propertyUseDesc?: string;       // Property use description
  property_use_desc?: string;     // Backup field name
  county?: string;
  sale_prc1?: number;
  sale_date1?: string;
  homestead?: boolean;
  bedrooms?: number;
  bathrooms?: number;
}

interface EnhancedPropertyMiniCardProps {
  data: PropertyMiniCardData;
  onClick?: () => void;
  variant?: 'grid' | 'list' | 'compact';
  showInvestmentScore?: boolean;
  showQuickActions?: boolean;
  isWatched?: boolean;
  onToggleWatchlist?: () => void;
}

export function EnhancedPropertyMiniCard({
  data,
  onClick,
  variant = 'grid',
  showInvestmentScore = true,
  showQuickActions = true,
  isWatched = false,
  onToggleWatchlist
}: EnhancedPropertyMiniCardProps) {
  const [isHovered, setIsHovered] = useState(false);

  // Fetch complete property data for investment scoring
  const propertyData = useCompletePropertyData(data.parcel_id);

  // Format currency values
  const formatCurrency = (value?: number) => {
    if (!value || value === 0) return 'N/A';
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `$${Math.round(value / 1000)}K`;
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Get property type and category
  const getPropertyType = () => {
    const propertyUse = data.propertyUse || data.property_use;
    if (!propertyUse) return { type: 'Unknown', color: 'gray' };

    const code = propertyUse.toString();
    if (code.startsWith('0')) return { type: 'Vacant Land', color: 'gray', icon: MapPin };
    if (['1', '2', '3'].includes(code)) return { type: 'Residential', color: 'green', icon: Home };
    if (['4', '5', '6', '7'].includes(code)) return { type: 'Commercial', color: 'blue', icon: Building };
    if (['8', '9'].includes(code)) return { type: 'Industrial', color: 'orange', icon: Building };
    return { type: 'Other', color: 'gray', icon: Building };
  };

  // Calculate investment score locally if not available
  const getInvestmentScore = () => {
    if (propertyData.investmentAnalysis?.investment_score?.overall_score) {
      return propertyData.investmentAnalysis.investment_score.overall_score;
    }

    // Simple local calculation using correct field names
    let score = 50;
    const marketValue = data.jv || data.just_value || data.market_value || 0;
    const yearBuilt = data.act_yr_blt || data.year_built || 1950;
    const propertyAge = new Date().getFullYear() - yearBuilt;

    if (propertyAge < 20) score += 10;
    else if (propertyAge > 60) score -= 10;

    if (marketValue > 0 && marketValue < 200000) score += 15;
    else if (marketValue > 500000) score -= 10;

    if (!data.homestead) score += 10;
    const buildingSize = data.tot_lvg_area || data.building_sqft || 0;
    if (buildingSize && buildingSize > 1200) score += 5;

    return Math.max(0, Math.min(100, score));
  };

  // Get investment score color and rating
  const getScoreDisplay = (score: number) => {
    if (score >= 80) return { color: 'green', rating: 'Excellent', bgColor: 'bg-green-50', textColor: 'text-green-700' };
    if (score >= 70) return { color: 'blue', rating: 'Very Good', bgColor: 'bg-blue-50', textColor: 'text-blue-700' };
    if (score >= 60) return { color: 'yellow', rating: 'Good', bgColor: 'bg-yellow-50', textColor: 'text-yellow-700' };
    if (score >= 40) return { color: 'orange', rating: 'Fair', bgColor: 'bg-orange-50', textColor: 'text-orange-700' };
    return { color: 'red', rating: 'Poor', bgColor: 'bg-red-50', textColor: 'text-red-700' };
  };

  // Get key opportunities
  const getOpportunities = () => {
    const opportunities = [];
    if (propertyData.investmentAnalysis?.opportunities?.primary_opportunities) {
      return propertyData.investmentAnalysis.opportunities.primary_opportunities.slice(0, 2);
    }

    // Local opportunity detection using correct field names
    if (!data.homestead) opportunities.push('Investment Property');
    const yearBuilt = data.act_yr_blt || data.year_built;
    if (yearBuilt && (new Date().getFullYear() - yearBuilt) > 30) {
      opportunities.push('Renovation Potential');
    }
    const marketValue = data.jv || data.just_value || data.market_value;
    if (marketValue && data.sale_prc1 && marketValue > data.sale_prc1 * 1.2) {
      opportunities.push('Below Market Value');
    }

    return opportunities.slice(0, 2);
  };

  const propertyType = getPropertyType();
  const investmentScore = getInvestmentScore();
  const scoreDisplay = getScoreDisplay(investmentScore);
  const opportunities = getOpportunities();

  const handleCardClick = () => {
    if (onClick) {
      onClick();
    } else {
      // Navigate to property detail page
      window.location.href = `/property/${data.parcel_id}`;
    }
  };

  // Grid variant - Elegant card design
  if (variant === 'grid') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        whileHover={{ y: -4, scale: 1.02 }}
        transition={{ duration: 0.3 }}
        onHoverStart={() => setIsHovered(true)}
        onHoverEnd={() => setIsHovered(false)}
      >
        <Card className="group relative overflow-hidden cursor-pointer bg-gradient-to-br from-white to-gray-50 border-0 shadow-md hover:shadow-xl transition-all duration-500">
          {/* Gradient header */}
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500" />

          {/* Top section with badges and actions */}
          <div className="relative p-4 pb-3">
            {/* Property type badge */}
            <div className="flex items-center justify-between mb-3">
              <Badge
                className={`flex items-center gap-1.5 text-xs font-medium px-2 py-1 bg-${propertyType.color}-100 text-${propertyType.color}-700 border border-${propertyType.color}-200`}
              >
                <propertyType.icon className="w-3 h-3" />
                {propertyType.type}
              </Badge>

              <div className="flex items-center gap-2">
                {isWatched && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onToggleWatchlist?.();
                    }}
                    className="p-1 rounded-full bg-yellow-100 text-yellow-600 hover:bg-yellow-200 transition-colors"
                  >
                    <Star className="w-3 h-3 fill-current" />
                  </button>
                )}
              </div>
            </div>

            {/* Investment score */}
            {showInvestmentScore && (
              <div className={`flex items-center justify-between p-3 rounded-lg ${scoreDisplay.bgColor} mb-3`}>
                <div className="flex items-center gap-2">
                  <Target className={`w-4 h-4 ${scoreDisplay.textColor}`} />
                  <span className={`text-sm font-medium ${scoreDisplay.textColor}`}>
                    Investment Score
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xl font-bold ${scoreDisplay.textColor}`}>
                    {investmentScore}
                  </span>
                  <span className={`text-xs font-medium ${scoreDisplay.textColor}`}>
                    {scoreDisplay.rating}
                  </span>
                </div>
              </div>
            )}

            {/* Address */}
            <div className="mb-3">
              <a
                href={`https://www.google.com/maps/search/${encodeURIComponent(
                  `${data.phy_addr1 || 'Parcel ' + data.parcel_id}, ${data.phy_city || ''}, FL ${data.phy_zipcd || ''}`
                )}`}
                target="_blank"
                rel="noopener noreferrer"
                className="group/address block"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center group-hover/address:bg-blue-100 transition-colors">
                    <MapPin className="w-4 h-4 text-gray-500 group-hover/address:text-blue-600 transition-colors" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-gray-900 text-sm mb-1 line-clamp-2 group-hover/address:text-blue-600 transition-colors">
                      {data.phy_addr1 || 'No Street Address'}
                      <ExternalLink className="w-3 h-3 inline ml-1 opacity-0 group-hover/address:opacity-100 transition-opacity" />
                    </p>
                    <p className="text-xs text-gray-500">
                      {data.phy_city || 'Unknown City'}, FL {data.phy_zipcd || ''}
                    </p>
                  </div>
                </div>
              </a>
            </div>

            {/* Owner */}
            <div className="flex items-center gap-3 mb-4 pb-3 border-b border-gray-100">
              <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                <User className="w-4 h-4 text-gray-500" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Owner</p>
                <p className="text-sm font-medium text-gray-900 truncate">
                  {data.own_name || data.owner_name || 'Unknown Owner'}
                </p>
              </div>
            </div>
          </div>

          {/* Values section */}
          <div className="px-4 pb-4">
            <div className="grid grid-cols-2 gap-3 mb-4">
              {/* Market Value */}
              <div className="text-center p-3 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg">
                <p className="text-xs font-medium text-gray-600 mb-1">Market Value</p>
                <p className="text-lg font-bold text-gray-900">
                  {formatCurrency(data.jv || data.just_value || data.market_value)}
                </p>
              </div>

              {/* Last Sale or Other Metric */}
              {data.sale_prc1 && data.sale_prc1 > 1000 ? (
                <div className="text-center p-3 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg">
                  <p className="text-xs font-medium text-green-600 mb-1">Last Sale</p>
                  <p className="text-lg font-bold text-green-800">
                    {formatCurrency(data.sale_prc1)}
                  </p>
                  {data.sale_date1 && (
                    <p className="text-xs text-green-600 mt-1">
                      {new Date(data.sale_date1).getFullYear()}
                    </p>
                  )}
                </div>
              ) : (
                <div className="text-center p-3 bg-gradient-to-br from-gray-50 to-slate-50 rounded-lg">
                  <p className="text-xs font-medium text-gray-600 mb-1">Year Built</p>
                  <p className="text-lg font-bold text-gray-800">
                    {data.act_yr_blt || data.year_built || 'N/A'}
                  </p>
                </div>
              )}
            </div>

            {/* Quick stats */}
            <div className="grid grid-cols-2 gap-2 text-xs text-gray-600 mb-4">
              {(data.tot_lvg_area || data.building_sqft) && (
                <div className="flex items-center gap-1">
                  <Building className="w-3 h-3" />
                  <span>{(data.tot_lvg_area || data.building_sqft || 0).toLocaleString()} sqft</span>
                </div>
              )}
              {data.bedrooms && data.bathrooms && (
                <div className="flex items-center gap-1">
                  <Home className="w-3 h-3" />
                  <span>{data.bedrooms}bed / {data.bathrooms}bath</span>
                </div>
              )}
              {(data.lnd_sqfoot || data.land_sqft) && (
                <div className="flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  <span>{((data.lnd_sqfoot || data.land_sqft || 0) / 43560).toFixed(2)} acres</span>
                </div>
              )}
              {data.homestead && (
                <div className="flex items-center gap-1">
                  <Shield className="w-3 h-3 text-green-600" />
                  <span className="text-green-600">Homesteaded</span>
                </div>
              )}
            </div>

            {/* Opportunities */}
            {opportunities.length > 0 && (
              <div className="mb-4">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
                  Investment Opportunities
                </p>
                <div className="flex flex-wrap gap-1">
                  {opportunities.map((opportunity, index) => (
                    <Badge
                      key={index}
                      variant="outline"
                      className="text-xs bg-green-50 text-green-700 border-green-200"
                    >
                      <CheckCircle className="w-3 h-3 mr-1" />
                      {opportunity}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            {showQuickActions && (
              <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-8 px-3 text-xs hover:bg-blue-50 hover:text-blue-700"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCardClick();
                  }}
                >
                  <Eye className="w-3 h-3 mr-1.5" />
                  View Details
                </Button>

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
                  <DropdownMenuContent align="end" className="w-48">
                    <DropdownMenuItem onClick={handleCardClick}>
                      <Eye className="w-4 h-4 mr-2" />
                      View Full Details
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={onToggleWatchlist}>
                      <Star className="w-4 h-4 mr-2" />
                      {isWatched ? 'Remove from Watchlist' : 'Add to Watchlist'}
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
            <div className="mt-3 pt-2 border-t border-gray-100">
              <p className="text-xs text-gray-400 font-mono">ID: {data.parcel_id}</p>
            </div>
          </div>

          {/* Loading indicator for additional data */}
          {propertyData.isLoading && (
            <div className="absolute inset-0 bg-white/80 flex items-center justify-center">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            </div>
          )}
        </Card>
      </motion.div>
    );
  }

  // List variant - Horizontal layout
  if (variant === 'list') {
    return (
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        whileHover={{ scale: 1.01 }}
        transition={{ duration: 0.2 }}
        onClick={handleCardClick}
      >
        <Card className="group cursor-pointer bg-white border border-gray-200 hover:border-gray-300 hover:shadow-md transition-all duration-300 p-4">
          <div className="flex items-center gap-4">
            {/* Property type and score */}
            <div className="flex-shrink-0">
              <div className="flex items-center gap-2 mb-2">
                <Badge className={`text-xs bg-${propertyType.color}-100 text-${propertyType.color}-700 border border-${propertyType.color}-200`}>
                  <propertyType.icon className="w-3 h-3 mr-1" />
                  {propertyType.type}
                </Badge>
              </div>
              {showInvestmentScore && (
                <div className={`text-center p-2 rounded ${scoreDisplay.bgColor}`}>
                  <p className="text-xs font-medium text-gray-500 mb-1">Score</p>
                  <p className={`text-lg font-bold ${scoreDisplay.textColor}`}>{investmentScore}</p>
                </div>
              )}
            </div>

            {/* Address and Owner */}
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-gray-900 mb-1 truncate">
                {data.phy_addr1 || 'No Street Address'}
              </p>
              <p className="text-sm text-gray-600 mb-2">
                {data.phy_city}, FL {data.phy_zipcd} • {data.owner_name}
              </p>
              <div className="flex items-center gap-4 text-xs text-gray-500">
                {data.building_sqft && <span>{data.building_sqft.toLocaleString()} sqft</span>}
                {data.year_built && <span>Built {data.year_built}</span>}
                {data.homestead && <span className="text-green-600">Homesteaded</span>}
              </div>
            </div>

            {/* Values */}
            <div className="flex items-center gap-6">
              <div className="text-center">
                <p className="text-xs text-gray-500 mb-1">Market Value</p>
                <p className="font-semibold text-gray-900">
                  {formatCurrency(data.market_value || data.just_value)}
                </p>
              </div>
              {data.sale_prc1 && data.sale_prc1 > 1000 && (
                <div className="text-center">
                  <p className="text-xs text-green-600 mb-1">Last Sale</p>
                  <p className="font-semibold text-green-800">
                    {formatCurrency(data.sale_prc1)}
                  </p>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              {isWatched && (
                <Star className="w-4 h-4 text-yellow-600 fill-yellow-400" />
              )}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button size="sm" variant="ghost" className="h-8 w-8 p-0">
                    <MoreVertical className="w-4 h-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={handleCardClick}>
                    <Eye className="w-4 h-4 mr-2" />
                    View Details
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </Card>
      </motion.div>
    );
  }

  // Compact variant - Minimal design
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.2 }}
      onClick={handleCardClick}
      className="group cursor-pointer bg-white rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-lg transition-all duration-300 p-3"
    >
      <div className="flex items-center justify-between mb-2">
        <Badge className={`text-xs bg-${propertyType.color}-100 text-${propertyType.color}-700`}>
          {propertyType.type}
        </Badge>
        {showInvestmentScore && (
          <span className={`text-sm font-bold ${scoreDisplay.textColor}`}>
            {investmentScore}
          </span>
        )}
      </div>
      <p className="font-semibold text-sm text-gray-900 mb-1 line-clamp-1">
        {data.phy_addr1 || 'No Street Address'}
      </p>
      <p className="text-xs text-gray-500 mb-2">{data.owner_name}</p>
      <p className="font-semibold text-gray-900">
        {formatCurrency(data.market_value || data.just_value)}
      </p>
    </motion.div>
  );
}

export default EnhancedPropertyMiniCard;