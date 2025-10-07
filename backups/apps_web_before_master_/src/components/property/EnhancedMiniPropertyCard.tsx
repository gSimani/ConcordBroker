import React, { useState, useEffect, memo } from 'react';
import { motion } from 'framer-motion';
import { LazyLoadImage } from 'react-lazy-load-image-component';
import { useInView } from 'react-intersection-observer';
import { useQuery } from '@tanstack/react-query';
import {
  MapPin, TrendingUp, TrendingDown, Star, Eye, DollarSign,
  Home, Ruler, Calendar, AlertCircle, Sparkles, Camera
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import 'react-lazy-load-image-component/src/effects/blur.css';

interface EnhancedMiniPropertyCardProps {
  property: any;
  variant?: 'grid' | 'list' | 'compact';
  onCompare?: (property: any) => void;
  onFavorite?: (property: any) => void;
  onClick?: (property: any) => void;
}

// Memoized component for performance with 7.31M properties
export const EnhancedMiniPropertyCard = memo(({
  property,
  variant = 'grid',
  onCompare,
  onFavorite,
  onClick
}: EnhancedMiniPropertyCardProps) => {
  const [isFavorited, setIsFavorited] = useState(false);
  const [isComparing, setIsComparing] = useState(false);
  const { ref, inView } = useInView({
    threshold: 0,
    triggerOnce: true
  });

  // Fetch additional data only when card is in view
  const { data: enhancedData } = useQuery({
    queryKey: ['property-enhanced', property.parcel_id],
    queryFn: async () => {
      const response = await fetch(`/api/properties/${property.parcel_id}/enhanced`);
      return response.json();
    },
    enabled: inView, // Only fetch when visible
    staleTime: 1000 * 60 * 5, // Cache for 5 minutes
  });

  // Calculate investment score (AI-powered in production)
  const investmentScore = enhancedData?.investmentScore || calculateBasicScore(property);

  // Price trend indicator
  const priceTrend = property.sale_price > property.just_value ? 'up' : 'down';
  const priceDiff = ((property.sale_price - property.just_value) / property.just_value * 100).toFixed(1);

  // Status badge logic
  const getStatusBadge = () => {
    const daysSinceListing = enhancedData?.daysSinceListing || 0;
    if (daysSinceListing < 7) return { text: 'New', color: 'bg-green-500' };
    if (property.sale_price < property.just_value * 0.9) return { text: 'Hot Deal', color: 'bg-red-500' };
    if (enhancedData?.foreclosure) return { text: 'Foreclosure', color: 'bg-orange-500' };
    if (priceTrend === 'down') return { text: 'Price Reduced', color: 'bg-blue-500' };
    return null;
  };

  const statusBadge = getStatusBadge();

  // Format currency
  const formatPrice = (price: number) => {
    if (price >= 1000000) return `$${(price / 1000000).toFixed(2)}M`;
    if (price >= 1000) return `$${(price / 1000).toFixed(0)}K`;
    return `$${price.toFixed(0)}`;
  };

  // Google Street View image URL
  const streetViewUrl = `https://maps.googleapis.com/maps/api/streetview?size=400x300&location=${encodeURIComponent(
    `${property.phy_addr1}, ${property.phy_city}, FL ${property.phy_zipcd}`
  )}&key=${process.env.VITE_GOOGLE_MAPS_API_KEY}`;

  // Placeholder image with blur hash
  const placeholderImage = `data:image/svg+xml,%3Csvg width='400' height='300' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='400' height='300' fill='%23e2e8f0'/%3E%3C/svg%3E`;

  const handleFavoriteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsFavorited(!isFavorited);
    onFavorite?.(property);
  };

  const handleCompareClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsComparing(!isComparing);
    onCompare?.(property);
  };

  if (variant === 'list') {
    return (
      <motion.div
        ref={ref}
        initial={{ opacity: 0, x: -20 }}
        animate={inView ? { opacity: 1, x: 0 } : {}}
        className="bg-white rounded-lg shadow-sm hover:shadow-lg transition-all p-4 cursor-pointer border border-gray-100"
        onClick={() => onClick?.(property)}
      >
        <div className="flex gap-4">
          {/* Property Image */}
          <div className="relative w-32 h-24 flex-shrink-0">
            <LazyLoadImage
              src={streetViewUrl}
              placeholderSrc={placeholderImage}
              effect="blur"
              className="w-full h-full object-cover rounded-md"
              alt={property.phy_addr1}
            />
            {statusBadge && (
              <Badge className={cn("absolute top-1 left-1 text-xs", statusBadge.color)}>
                {statusBadge.text}
              </Badge>
            )}
          </div>

          {/* Property Details */}
          <div className="flex-1 min-w-0">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-semibold text-gray-900 truncate">
                  {property.phy_addr1}
                </h3>
                <p className="text-sm text-gray-500 flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  {property.phy_city}, FL {property.phy_zipcd}
                </p>
              </div>
              <div className="text-right">
                <p className="text-xl font-bold text-gray-900">
                  {formatPrice(property.just_value || 0)}
                </p>
                <div className="flex items-center gap-1 text-sm">
                  {priceTrend === 'up' ? (
                    <TrendingUp className="w-3 h-3 text-green-500" />
                  ) : (
                    <TrendingDown className="w-3 h-3 text-red-500" />
                  )}
                  <span className={priceTrend === 'up' ? 'text-green-500' : 'text-red-500'}>
                    {priceDiff}%
                  </span>
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="flex gap-4 mt-2 text-xs text-gray-600">
              <span className="flex items-center gap-1">
                <Home className="w-3 h-3" />
                {property.bedrooms || 0} bed / {property.bathrooms || 0} bath
              </span>
              <span className="flex items-center gap-1">
                <Ruler className="w-3 h-3" />
                {property.total_living_area?.toLocaleString() || 'N/A'} sqft
              </span>
              <span className="flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                Built {property.year_built || 'N/A'}
              </span>
            </div>

            {/* Investment Score */}
            <div className="flex items-center justify-between mt-2">
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1">
                  <Sparkles className="w-3 h-3 text-purple-500" />
                  <span className="text-xs font-medium">Score: {investmentScore}/100</span>
                </div>
                <div className="flex items-center gap-1 text-xs text-gray-500">
                  <Eye className="w-3 h-3" />
                  {enhancedData?.viewCount || 0} views
                </div>
              </div>
              <div className="flex gap-1">
                <button
                  onClick={handleFavoriteClick}
                  className={cn(
                    "p-1 rounded-full transition-colors",
                    isFavorited ? "text-yellow-500 bg-yellow-50" : "text-gray-400 hover:text-yellow-500"
                  )}
                >
                  <Star className="w-4 h-4" fill={isFavorited ? "currentColor" : "none"} />
                </button>
                <input
                  type="checkbox"
                  checked={isComparing}
                  onChange={handleCompareClick}
                  className="ml-2"
                  onClick={(e) => e.stopPropagation()}
                />
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    );
  }

  // Grid variant (default)
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      whileHover={{ y: -4 }}
      className="bg-white rounded-lg shadow-sm hover:shadow-xl transition-all cursor-pointer overflow-hidden group"
      onClick={() => onClick?.(property)}
    >
      {/* Property Image with Street View */}
      <div className="relative h-48 overflow-hidden">
        <LazyLoadImage
          src={streetViewUrl}
          placeholderSrc={placeholderImage}
          effect="blur"
          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
          alt={property.phy_addr1}
        />

        {/* Status Badge */}
        {statusBadge && (
          <Badge className={cn("absolute top-2 left-2", statusBadge.color)}>
            {statusBadge.text}
          </Badge>
        )}

        {/* Investment Score Badge */}
        <div className="absolute top-2 right-2 bg-purple-600 text-white px-2 py-1 rounded-full text-xs font-bold">
          Score: {investmentScore}
        </div>

        {/* Quick Actions */}
        <div className="absolute bottom-2 right-2 flex gap-1">
          <button
            onClick={handleFavoriteClick}
            className={cn(
              "p-1.5 rounded-full bg-white/90 backdrop-blur transition-colors",
              isFavorited ? "text-yellow-500" : "text-gray-600 hover:text-yellow-500"
            )}
          >
            <Star className="w-4 h-4" fill={isFavorited ? "currentColor" : "none"} />
          </button>
          <button className="p-1.5 rounded-full bg-white/90 backdrop-blur text-gray-600 hover:text-blue-500">
            <Camera className="w-4 h-4" />
          </button>
        </div>

        {/* View Counter */}
        <div className="absolute bottom-2 left-2 bg-black/60 text-white px-2 py-1 rounded text-xs flex items-center gap-1">
          <Eye className="w-3 h-3" />
          {enhancedData?.viewCount || 0}
        </div>
      </div>

      {/* Property Details */}
      <div className="p-4">
        {/* Address */}
        <h3 className="font-semibold text-gray-900 truncate group-hover:text-blue-600 transition-colors">
          {property.phy_addr1}
        </h3>
        <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
          <MapPin className="w-3 h-3" />
          {property.phy_city}, FL {property.phy_zipcd}
        </p>

        {/* Price and Trend */}
        <div className="flex justify-between items-center mt-3">
          <p className="text-2xl font-bold text-gray-900">
            {formatPrice(property.just_value || 0)}
          </p>
          <div className="flex items-center gap-1">
            {priceTrend === 'up' ? (
              <TrendingUp className="w-4 h-4 text-green-500" />
            ) : (
              <TrendingDown className="w-4 h-4 text-red-500" />
            )}
            <span className={cn(
              "text-sm font-medium",
              priceTrend === 'up' ? 'text-green-500' : 'text-red-500'
            )}>
              {priceDiff}%
            </span>
          </div>
        </div>

        {/* Property Stats */}
        <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t">
          <div className="text-center">
            <p className="text-xs text-gray-500">Beds/Bath</p>
            <p className="text-sm font-medium">
              {property.bedrooms || 0}/{property.bathrooms || 0}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-500">Sqft</p>
            <p className="text-sm font-medium">
              {property.total_living_area?.toLocaleString() || 'N/A'}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-500">$/Sqft</p>
            <p className="text-sm font-medium">
              ${((property.just_value || 0) / (property.total_living_area || 1)).toFixed(0)}
            </p>
          </div>
        </div>

        {/* Smart Insights */}
        {enhancedData && (
          <div className="mt-3 pt-3 border-t">
            <div className="flex justify-between items-center text-xs">
              <span className="text-gray-500">Est. Rent</span>
              <span className="font-medium text-green-600">
                ${enhancedData.estimatedRent || 'N/A'}/mo
              </span>
            </div>
            {enhancedData.marketComparison && (
              <div className="flex justify-between items-center text-xs mt-1">
                <span className="text-gray-500">Market</span>
                <span className="font-medium">
                  {enhancedData.marketComparison}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Compare Checkbox */}
        <div className="flex items-center justify-between mt-3 pt-3 border-t">
          <label className="flex items-center gap-2 text-xs text-gray-600 cursor-pointer">
            <input
              type="checkbox"
              checked={isComparing}
              onChange={handleCompareClick}
              onClick={(e) => e.stopPropagation()}
              className="rounded border-gray-300"
            />
            Compare
          </label>
          <div className="flex items-center gap-1 text-xs text-gray-500">
            <Star className="w-3 h-3" />
            {enhancedData?.savedCount || 0} saved
          </div>
        </div>
      </div>
    </motion.div>
  );
});

// Basic investment score calculation (replace with AI model)
function calculateBasicScore(property: any): number {
  let score = 50; // Base score

  // Price factors
  const priceRatio = property.sale_price / property.just_value;
  if (priceRatio < 0.9) score += 20; // Undervalued
  if (priceRatio > 1.1) score -= 10; // Overvalued

  // Property characteristics
  if (property.year_built > 2010) score += 10; // Newer property
  if (property.total_living_area > 2000) score += 5; // Larger property
  if (property.bedrooms >= 3) score += 5; // Family-sized
  if (property.bathrooms >= 2) score += 5; // Multiple bathrooms

  // Location (simplified)
  const premiumCounties = ['MIAMI-DADE', 'BROWARD', 'PALM BEACH'];
  if (premiumCounties.includes(property.county)) score += 10;

  return Math.min(100, Math.max(0, Math.round(score)));
}

EnhancedMiniPropertyCard.displayName = 'EnhancedMiniPropertyCard';