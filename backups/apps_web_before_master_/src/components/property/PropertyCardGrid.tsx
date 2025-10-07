import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Grid3X3,
  List,
  Filter,
  SortAsc,
  SortDesc,
  Search,
  MapPin,
  DollarSign,
  TrendingUp,
  Calendar,
  Zap,
  Eye,
  Settings
} from 'lucide-react';
import EnhancedPropertyMiniCard from './EnhancedPropertyMiniCard';
import { Badge } from '@/components/ui/badge';
import { motion, AnimatePresence } from 'framer-motion';

interface PropertyCardGridProps {
  properties: any[];
  loading?: boolean;
  onPropertyClick?: (property: any) => void;
  showInvestmentScore?: boolean;
  allowFiltering?: boolean;
  allowSorting?: boolean;
  defaultLayout?: 'grid' | 'list' | 'compact';
  pageSize?: number;
  title?: string;
  subtitle?: string;
}

type SortOption = 'market_value' | 'investment_score' | 'last_sale' | 'year_built' | 'address';
type FilterType = 'all' | 'residential' | 'commercial' | 'industrial' | 'vacant';

export function PropertyCardGrid({
  properties = [],
  loading = false,
  onPropertyClick,
  showInvestmentScore = true,
  allowFiltering = true,
  allowSorting = true,
  defaultLayout = 'grid',
  pageSize = 20,
  title,
  subtitle
}: PropertyCardGridProps) {
  const [layout, setLayout] = useState<'grid' | 'list' | 'compact'>(defaultLayout);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('market_value');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [filterType, setFilterType] = useState<FilterType>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [watchedProperties, setWatchedProperties] = useState<Set<string>>(new Set());

  // Filter and sort properties
  const filteredAndSortedProperties = React.useMemo(() => {
    let filtered = properties;

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(property =>
        property.phy_addr1?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        property.owner_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        property.phy_city?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        property.parcel_id?.includes(searchQuery)
      );
    }

    // Apply property type filter
    if (filterType !== 'all') {
      filtered = filtered.filter(property => {
        const propertyUse = property.property_use?.toString() || '';
        switch (filterType) {
          case 'residential':
            return ['1', '2', '3'].includes(propertyUse);
          case 'commercial':
            return ['4', '5', '6', '7'].includes(propertyUse);
          case 'industrial':
            return ['8', '9'].includes(propertyUse);
          case 'vacant':
            return propertyUse === '0';
          default:
            return true;
        }
      });
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aVal, bVal;

      switch (sortBy) {
        case 'market_value':
          aVal = a.market_value || a.just_value || 0;
          bVal = b.market_value || b.just_value || 0;
          break;
        case 'investment_score':
          // Would use API data if available, fallback to simple calculation
          aVal = calculateSimpleInvestmentScore(a);
          bVal = calculateSimpleInvestmentScore(b);
          break;
        case 'last_sale':
          aVal = a.sale_prc1 || 0;
          bVal = b.sale_prc1 || 0;
          break;
        case 'year_built':
          aVal = a.year_built || 0;
          bVal = b.year_built || 0;
          break;
        case 'address':
          aVal = a.phy_addr1 || '';
          bVal = b.phy_addr1 || '';
          return sortOrder === 'asc'
            ? aVal.localeCompare(bVal)
            : bVal.localeCompare(aVal);
        default:
          return 0;
      }

      return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
    });

    return filtered;
  }, [properties, searchQuery, filterType, sortBy, sortOrder]);

  // Simple investment score calculation
  const calculateSimpleInvestmentScore = (property: any) => {
    let score = 50;
    const marketValue = property.market_value || property.just_value || 0;
    const yearBuilt = property.year_built || 1950;
    const propertyAge = new Date().getFullYear() - yearBuilt;

    if (propertyAge < 20) score += 10;
    else if (propertyAge > 60) score -= 10;

    if (marketValue > 0 && marketValue < 200000) score += 15;
    else if (marketValue > 500000) score -= 10;

    if (!property.homestead) score += 10;
    if (property.building_sqft && property.building_sqft > 1200) score += 5;

    return Math.max(0, Math.min(100, score));
  };

  // Pagination
  const totalPages = Math.ceil(filteredAndSortedProperties.length / pageSize);
  const paginatedProperties = filteredAndSortedProperties.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  // Handle watchlist toggle
  const handleToggleWatchlist = (parcelId: string) => {
    setWatchedProperties(prev => {
      const newSet = new Set(prev);
      if (newSet.has(parcelId)) {
        newSet.delete(parcelId);
      } else {
        newSet.add(parcelId);
      }
      return newSet;
    });
  };

  // Reset pagination when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, filterType, sortBy, sortOrder]);

  if (loading) {
    return (
      <div className="space-y-6">
        {title && (
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
            {subtitle && <p className="text-gray-600 mt-2">{subtitle}</p>}
          </div>
        )}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, index) => (
            <div key={index} className="animate-pulse">
              <div className="bg-gray-200 rounded-lg h-80"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      {title && (
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
            {subtitle && <p className="text-gray-600 mt-2">{subtitle}</p>}
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <span>{filteredAndSortedProperties.length} properties</span>
            {filteredAndSortedProperties.length !== properties.length && (
              <span>({properties.length} total)</span>
            )}
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between bg-white p-4 rounded-lg border border-gray-200">
        {/* Search and filters */}
        <div className="flex flex-1 items-center gap-3">
          {/* Search */}
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search by address, owner, or parcel ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Property type filter */}
          {allowFiltering && (
            <Select value={filterType} onValueChange={(value: FilterType) => setFilterType(value)}>
              <SelectTrigger className="w-40">
                <Filter className="w-4 h-4 mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="residential">Residential</SelectItem>
                <SelectItem value="commercial">Commercial</SelectItem>
                <SelectItem value="industrial">Industrial</SelectItem>
                <SelectItem value="vacant">Vacant Land</SelectItem>
              </SelectContent>
            </Select>
          )}

          {/* Sort */}
          {allowSorting && (
            <div className="flex items-center gap-2">
              <Select value={sortBy} onValueChange={(value: SortOption) => setSortBy(value)}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="market_value">Market Value</SelectItem>
                  <SelectItem value="investment_score">Investment Score</SelectItem>
                  <SelectItem value="last_sale">Last Sale</SelectItem>
                  <SelectItem value="year_built">Year Built</SelectItem>
                  <SelectItem value="address">Address</SelectItem>
                </SelectContent>
              </Select>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              >
                {sortOrder === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />}
              </Button>
            </div>
          )}
        </div>

        {/* Layout controls */}
        <div className="flex items-center gap-2">
          <div className="flex items-center bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setLayout('grid')}
              className={`p-2 rounded ${
                layout === 'grid'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Grid3X3 className="w-4 h-4" />
            </button>
            <button
              onClick={() => setLayout('list')}
              className={`p-2 rounded ${
                layout === 'list'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <List className="w-4 h-4" />
            </button>
            <button
              onClick={() => setLayout('compact')}
              className={`p-2 rounded ${
                layout === 'compact'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Settings className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Property Grid/List */}
      <AnimatePresence mode="wait">
        <motion.div
          key={`${layout}-${currentPage}`}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
        >
          {paginatedProperties.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-24 h-24 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                <Search className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No properties found</h3>
              <p className="text-gray-600">
                Try adjusting your search criteria or filters to find what you're looking for.
              </p>
            </div>
          ) : (
            <>
              {/* Grid layout */}
              {layout === 'grid' && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                  {paginatedProperties.map((property, index) => (
                    <motion.div
                      key={property.parcel_id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: index * 0.05 }}
                    >
                      <EnhancedPropertyMiniCard
                        data={property}
                        variant="grid"
                        onClick={() => onPropertyClick?.(property)}
                        showInvestmentScore={showInvestmentScore}
                        isWatched={watchedProperties.has(property.parcel_id)}
                        onToggleWatchlist={() => handleToggleWatchlist(property.parcel_id)}
                      />
                    </motion.div>
                  ))}
                </div>
              )}

              {/* List layout */}
              {layout === 'list' && (
                <div className="space-y-4">
                  {paginatedProperties.map((property, index) => (
                    <motion.div
                      key={property.parcel_id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.3, delay: index * 0.02 }}
                    >
                      <EnhancedPropertyMiniCard
                        data={property}
                        variant="list"
                        onClick={() => onPropertyClick?.(property)}
                        showInvestmentScore={showInvestmentScore}
                        isWatched={watchedProperties.has(property.parcel_id)}
                        onToggleWatchlist={() => handleToggleWatchlist(property.parcel_id)}
                      />
                    </motion.div>
                  ))}
                </div>
              )}

              {/* Compact layout */}
              {layout === 'compact' && (
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-3">
                  {paginatedProperties.map((property, index) => (
                    <motion.div
                      key={property.parcel_id}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ duration: 0.2, delay: index * 0.02 }}
                    >
                      <EnhancedPropertyMiniCard
                        data={property}
                        variant="compact"
                        onClick={() => onPropertyClick?.(property)}
                        showInvestmentScore={showInvestmentScore}
                        isWatched={watchedProperties.has(property.parcel_id)}
                        onToggleWatchlist={() => handleToggleWatchlist(property.parcel_id)}
                      />
                    </motion.div>
                  ))}
                </div>
              )}
            </>
          )}
        </motion.div>
      </AnimatePresence>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-6">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <span>
              Showing {(currentPage - 1) * pageSize + 1} to{' '}
              {Math.min(currentPage * pageSize, filteredAndSortedProperties.length)} of{' '}
              {filteredAndSortedProperties.length} properties
            </span>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(currentPage - 1)}
            >
              Previous
            </Button>

            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const pageNum = i + 1;
                const isCurrentPage = pageNum === currentPage;

                return (
                  <Button
                    key={pageNum}
                    variant={isCurrentPage ? "default" : "outline"}
                    size="sm"
                    className="w-10 h-8"
                    onClick={() => setCurrentPage(pageNum)}
                  >
                    {pageNum}
                  </Button>
                );
              })}

              {totalPages > 5 && (
                <>
                  <span className="text-gray-400">...</span>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-10 h-8"
                    onClick={() => setCurrentPage(totalPages)}
                  >
                    {totalPages}
                  </Button>
                </>
              )}
            </div>

            <Button
              variant="outline"
              size="sm"
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage(currentPage + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {/* Summary stats */}
      {paginatedProperties.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">
              {filteredAndSortedProperties.length}
            </p>
            <p className="text-sm text-gray-600">Properties</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">
              ${Math.round(
                filteredAndSortedProperties.reduce(
                  (sum, p) => sum + (p.market_value || p.just_value || 0),
                  0
                ) / 1000000
              )}M
            </p>
            <p className="text-sm text-gray-600">Total Value</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">
              ${Math.round(
                filteredAndSortedProperties.reduce(
                  (sum, p) => sum + (p.market_value || p.just_value || 0),
                  0
                ) / filteredAndSortedProperties.length / 1000
              )}K
            </p>
            <p className="text-sm text-gray-600">Avg Value</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">
              {Math.round(
                filteredAndSortedProperties.reduce(
                  (sum, p) => sum + calculateSimpleInvestmentScore(p),
                  0
                ) / filteredAndSortedProperties.length
              )}
            </p>
            <p className="text-sm text-gray-600">Avg Score</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default PropertyCardGrid;