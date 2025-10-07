import React from 'react';
import { useSalesData } from '@/hooks/useSalesData';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  MapPin,
  DollarSign,
  TrendingUp,
  TrendingDown,
  Home,
  Building,
  Star,
  Eye,
  Target,
  Percent,
  Calendar,
  ExternalLink,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';
import { motion } from 'framer-motion';

interface SearchResultCardProps {
  property: {
    parcel_id: string;
    phy_addr1?: string;
    phy_city?: string;
    phy_state?: string;
    phy_zipcd?: string;
    owner_name?: string;
    market_value?: number;
    just_value?: number;
    assessed_value?: number;
    building_sqft?: number;
    land_sqft?: number;
    year_built?: number;
    property_use?: string;
    sale_prc1?: number;
    sale_date1?: string;
    homestead?: boolean;
    bedrooms?: number;
    bathrooms?: number;
    county?: string;
  };
  index: number;
  onClick?: () => void;
  onToggleWatchlist?: () => void;
  isWatched?: boolean;
  highlightTerms?: string[];
}

export function SearchResultCard({
  property,
  index,
  onClick,
  onToggleWatchlist,
  isWatched = false,
  highlightTerms = []
}: SearchResultCardProps) {
  // Calculate investment metrics
  const marketValue = property.market_value || property.just_value || 0;
  const { salesData } = useSalesData(property.parcel_id || null);
  const lastSalePrice = (salesData?.most_recent_sale?.sale_price && salesData.most_recent_sale.sale_price > 1000)
    ? salesData.most_recent_sale.sale_price
    : (property.sale_prc1 || 0);
  const lastSaleDate = salesData?.most_recent_sale?.sale_date || property.sale_date1 || '';
  const formatDate = (d: string) => {
    if (!d) return '';
    try { return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }); } catch { return ''; }
  };
  const yearBuilt = property.year_built || 0;
  const currentYear = new Date().getFullYear();
  const propertyAge = yearBuilt > 0 ? currentYear - yearBuilt : 0;

  // Simple investment score calculation
  const calculateInvestmentScore = () => {
    let score = 50;

    // Age bonus/penalty
    if (propertyAge < 20) score += 15;
    else if (propertyAge < 40) score += 5;
    else if (propertyAge > 60) score -= 10;

    // Value range scoring
    if (marketValue > 0 && marketValue < 200000) score += 10;
    else if (marketValue > 500000) score -= 5;

    // Non-homestead bonus
    if (!property.homestead) score += 15;

    // Building size bonus
    if (property.building_sqft && property.building_sqft > 1200) score += 5;

    // Recent sale activity
    if (lastSalePrice > 0 && (property.sale_date1 || salesData?.most_recent_sale?.sale_date)) {
      const saleYear = new Date(salesData?.most_recent_sale?.sale_date || property.sale_date1!).getFullYear();
      if (currentYear - saleYear < 3) score += 5;
    }

    return Math.max(0, Math.min(100, Math.round(score)));
  };

  // Get property type and color
  const getPropertyType = () => {
    if (!property.property_use) return { type: 'Unknown', color: 'gray', icon: Building };

    const code = property.property_use.toString();
    if (code === '0' || code === '00') return { type: 'Vacant Land', color: 'gray', icon: MapPin };
    if (['1', '2', '3'].includes(code)) return { type: 'Residential', color: 'green', icon: Home };
    if (['4', '5', '6', '7'].includes(code)) return { type: 'Commercial', color: 'blue', icon: Building };
    if (['8', '9'].includes(code)) return { type: 'Industrial', color: 'orange', icon: Building };
    return { type: 'Other', color: 'gray', icon: Building };
  };

  // Format currency
  const formatCurrency = (value: number) => {
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

  // Highlight search terms in text
  const highlightText = (text: string) => {
    if (!highlightTerms.length) return text;

    let highlightedText = text;
    highlightTerms.forEach(term => {
      const regex = new RegExp(`(${term})`, 'gi');
      highlightedText = highlightedText.replace(
        regex,
        '<mark class="bg-yellow-200 px-1 rounded">$1</mark>'
      );
    });

    return <span dangerouslySetInnerHTML={{ __html: highlightedText }} />;
  };

  const propertyType = getPropertyType();
  const investmentScore = calculateInvestmentScore();
  const scoreColor = investmentScore >= 70 ? 'green' : investmentScore >= 50 ? 'yellow' : 'red';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className="group bg-white rounded-lg border border-gray-200 hover:border-gray-300 hover:shadow-lg transition-all duration-300 cursor-pointer"
      onClick={onClick}
    >
      <div className="p-6">
        {/* Header with property type and actions */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <Badge className={`bg-${propertyType.color}-100 text-${propertyType.color}-700 border border-${propertyType.color}-200`}>
              <propertyType.icon className="w-3 h-3 mr-1" />
              {propertyType.type}
            </Badge>

            {/* Investment Score */}
            <div className={`px-3 py-1 rounded-full bg-${scoreColor}-100 text-${scoreColor}-700 border border-${scoreColor}-200`}>
              <div className="flex items-center gap-1.5">
                <Target className="w-3 h-3" />
                <span className="text-sm font-medium">{investmentScore}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {property.homestead && (
              <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 text-xs">
                Homestead
              </Badge>
            )}
            <button
              onClick={(e) => {
                e.stopPropagation();
                onToggleWatchlist?.();
              }}
              className={`p-2 rounded-full transition-colors ${
                isWatched
                  ? 'bg-yellow-100 text-yellow-600 hover:bg-yellow-200'
                  : 'bg-gray-100 text-gray-400 hover:bg-gray-200'
              }`}
            >
              <Star className={`w-4 h-4 ${isWatched ? 'fill-current' : ''}`} />
            </button>
          </div>
        </div>

        {/* Address */}
        <div className="mb-4">
          <a
            href={`https://www.google.com/maps/search/${encodeURIComponent(
              `${property.phy_addr1 || 'Parcel ' + property.parcel_id}, ${property.phy_city || ''}, FL ${property.phy_zipcd || ''}`
            )}`}
            target="_blank"
            rel="noopener noreferrer"
            className="group/address block hover:text-blue-600 transition-colors"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center group-hover/address:bg-blue-100 transition-colors">
                <MapPin className="w-5 h-5 text-gray-500 group-hover/address:text-blue-600 transition-colors" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-lg text-gray-900 mb-1 group-hover/address:text-blue-600 transition-colors flex items-center gap-2">
                  {highlightText(property.phy_addr1 || 'No Street Address')}
                  <ExternalLink className="w-4 h-4 opacity-0 group-hover/address:opacity-100 transition-opacity" />
                </h3>
                <p className="text-sm text-gray-600">
                  {highlightText(`${property.phy_city || 'Unknown City'}, FL ${property.phy_zipcd || ''}`)}
                </p>
              </div>
            </div>
          </a>
        </div>

        {/* Owner */}
        <div className="mb-5 pb-4 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
              <propertyType.icon className="w-4 h-4 text-gray-500" />
            </div>
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Owner</p>
              <p className="font-medium text-gray-900">
                {highlightText(property.owner_name || 'Unknown Owner')}
              </p>
            </div>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
          {/* Market Value */}
          <div className="text-center p-3 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
            <DollarSign className="w-5 h-5 text-blue-600 mx-auto mb-1" />
            <p className="text-xs font-medium text-blue-600 mb-1">Market Value</p>
            <p className="text-lg font-bold text-blue-800">
              {formatCurrency(marketValue)}
            </p>
          </div>

          {/* Last Sale */}
          {lastSalePrice > 0 ? (
            <div className="text-center p-3 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
              <TrendingUp className="w-5 h-5 text-green-600 mx-auto mb-1" />
              <p className="text-xs font-medium text-green-600 mb-1">Last Sale</p>
              <p className="text-lg font-bold text-green-800">
                {formatCurrency(lastSalePrice)}
              </p>
              {lastSaleDate && (
                <p className="text-xs text-green-600 mt-1">{formatDate(lastSaleDate)}</p>
              )}
            </div>
          ) : (
            <div className="text-center p-3 bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg">
              <Calendar className="w-5 h-5 text-gray-600 mx-auto mb-1" />
              <p className="text-xs font-medium text-gray-600 mb-1">Year Built</p>
              <p className="text-lg font-bold text-gray-800">
                {property.year_built || 'N/A'}
              </p>
            </div>
          )}

          {/* Building Info */}
          {property.building_sqft ? (
            <div className="text-center p-3 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg">
              <Building className="w-5 h-5 text-purple-600 mx-auto mb-1" />
              <p className="text-xs font-medium text-purple-600 mb-1">Building</p>
              <p className="text-lg font-bold text-purple-800">
                {property.building_sqft.toLocaleString()}
              </p>
              <p className="text-xs text-purple-600 mt-1">sqft</p>
            </div>
          ) : (
            <div className="text-center p-3 bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg">
              <MapPin className="w-5 h-5 text-gray-600 mx-auto mb-1" />
              <p className="text-xs font-medium text-gray-600 mb-1">Land</p>
              <p className="text-lg font-bold text-gray-800">
                {property.land_sqft ? (property.land_sqft / 43560).toFixed(2) : 'N/A'}
              </p>
              <p className="text-xs text-gray-600 mt-1">acres</p>
            </div>
          )}

          {/* Investment Indicator */}
          <div className={`text-center p-3 bg-gradient-to-br from-${scoreColor}-50 to-${scoreColor}-100 rounded-lg`}>
            <Target className={`w-5 h-5 text-${scoreColor}-600 mx-auto mb-1`} />
            <p className={`text-xs font-medium text-${scoreColor}-600 mb-1`}>Potential</p>
            <p className={`text-lg font-bold text-${scoreColor}-800`}>
              {investmentScore >= 70 ? 'High' : investmentScore >= 50 ? 'Medium' : 'Low'}
            </p>
          </div>
        </div>

        {/* Quick Details */}
        <div className="flex flex-wrap items-center gap-4 text-xs text-gray-600 mb-4">
          {property.bedrooms && property.bathrooms && (
            <div className="flex items-center gap-1">
              <Home className="w-3 h-3" />
              <span>{property.bedrooms}bed / {property.bathrooms}bath</span>
            </div>
          )}
          {propertyAge > 0 && (
            <div className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              <span>{propertyAge} years old</span>
            </div>
          )}
          <div className="flex items-center gap-1">
            <MapPin className="w-3 h-3" />
            <span>{property.county || 'Unknown'} County</span>
          </div>
        </div>

        {/* Investment Insights */}
        <div className="mb-4">
          <div className="flex flex-wrap gap-2">
            {!property.homestead && (
              <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 text-xs">
                <CheckCircle className="w-3 h-3 mr-1" />
                Investment Property
              </Badge>
            )}
            {propertyAge > 30 && propertyAge < 60 && (
              <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 text-xs">
                <CheckCircle className="w-3 h-3 mr-1" />
                Renovation Potential
              </Badge>
            )}
            {marketValue > 0 && marketValue < 200000 && (
              <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200 text-xs">
                <CheckCircle className="w-3 h-3 mr-1" />
                Affordable Entry
              </Badge>
            )}
            {lastSalePrice > 0 && marketValue > lastSalePrice * 1.2 && (
              <Badge variant="outline" className="bg-orange-50 text-orange-700 border-orange-200 text-xs">
                <TrendingUp className="w-3 h-3 mr-1" />
                Appreciation Potential
              </Badge>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
          <div className="text-xs text-gray-500 font-mono">
            Parcel: {property.parcel_id}
          </div>

          <Button
            size="sm"
            className="h-8 px-4 bg-blue-600 hover:bg-blue-700 text-white"
            onClick={(e) => {
              e.stopPropagation();
              onClick?.();
            }}
          >
            <Eye className="w-3 h-3 mr-2" />
            View Details
          </Button>
        </div>
      </div>
    </motion.div>
  );
}

export default SearchResultCard;
