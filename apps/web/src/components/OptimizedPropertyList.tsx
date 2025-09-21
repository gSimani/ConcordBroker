import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { VariableSizeList as List } from 'react-window';
import InfiniteLoader from 'react-window-infinite-loader';
import AutoSizer from 'react-virtualized-auto-sizer';
import { debounce } from 'lodash';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Search, Filter, Home, MapPin, DollarSign, Calendar, TrendingUp, Building } from 'lucide-react';
import { formatCurrency, formatNumber } from '@/lib/utils';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface Property {
  id: string;
  parcel_id: string;
  address: string;
  city: string;
  county: string;
  state: string;
  zipCode: string;
  owner: string;
  marketValue: number;
  assessedValue: number;
  landSqFt: number;
  buildingSqFt: number;
  yearBuilt: number;
  propertyType: string;
  lastSaleDate: string;
  lastSalePrice: number;
  latitude: number;
  longitude: number;
}

interface FilterState {
  city: string;
  minValue: string;
  maxValue: string;
  propertyType: string;
  sortBy: string;
  sortOrder: string;
}

const ITEM_HEIGHT = 120; // Height of each property card
const BUFFER_SIZE = 5; // Number of items to load ahead
const PAGE_SIZE = 50; // Items per page

export const OptimizedPropertyList: React.FC = () => {
  const [properties, setProperties] = useState<Property[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [cursor, setCursor] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<FilterState>({
    city: '',
    minValue: '',
    maxValue: '',
    propertyType: '',
    sortBy: 'parcel_id',
    sortOrder: 'asc'
  });
  const [totalCount, setTotalCount] = useState<number | null>(null);
  const [popularCities, setPopularCities] = useState<string[]>([]);

  const infiniteLoaderRef = useRef<any>(null);
  const hasMountedRef = useRef(false);

  // Fetch popular cities for quick filters
  useEffect(() => {
    fetch('http://localhost:8000/api/fast/cities')
      .then(res => res.json())
      .then(data => setPopularCities(data.map((c: any) => c.city)));
  }, []);

  // Debounced search function
  const debouncedSearch = useMemo(
    () => debounce((query: string) => {
      resetAndSearch(query);
    }, 500),
    []
  );

  const resetAndSearch = (query?: string) => {
    setProperties([]);
    setCursor(null);
    setHasMore(true);
    if (infiniteLoaderRef.current) {
      infiniteLoaderRef.current.resetloadMoreItemsCache();
    }
    loadMoreProperties(0, query);
  };

  const loadMoreProperties = async (startIndex: number, searchOverride?: string) => {
    if (isLoading) return;

    setIsLoading(true);

    try {
      const params = new URLSearchParams({
        limit: PAGE_SIZE.toString(),
        cursor: cursor || '',
        q: searchOverride !== undefined ? searchOverride : searchQuery,
        city: filters.city,
        minValue: filters.minValue,
        maxValue: filters.maxValue,
        propertyType: filters.propertyType,
        sortBy: filters.sortBy,
        sortOrder: filters.sortOrder,
        use_cache: 'true',
        include_total: startIndex === 0 ? 'true' : 'false'
      });

      // Remove empty params
      Array.from(params.keys()).forEach(key => {
        if (!params.get(key)) params.delete(key);
      });

      const response = await fetch(`http://localhost:8000/api/properties/search?${params}`);
      const data = await response.json();

      if (data.success) {
        setProperties(prev => [...prev, ...data.data]);
        setCursor(data.cursor);
        setHasMore(data.hasMore);
        if (data.total !== null) {
          setTotalCount(data.total);
        }
      }
    } catch (error) {
      console.error('Error loading properties:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle search input changes
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchQuery(value);
    debouncedSearch(value);
  };

  // Handle filter changes
  const handleFilterChange = (key: keyof FilterState, value: string) => {
    setFilters(prev => ({
      ...prev,
      [key]: value === 'all' ? '' : value
    }));
    resetAndSearch();
  };

  // Property card component
  const PropertyCard = ({ property, style }: { property: Property; style: React.CSSProperties }) => (
    <div style={style} className="px-4">
      <Card className="h-full hover:shadow-lg transition-shadow cursor-pointer">
        <CardContent className="p-4">
          <div className="flex justify-between items-start">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <Home className="w-4 h-4 text-gray-500" />
                <span className="font-semibold text-sm truncate">
                  {property.address || 'No Address'}
                </span>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-600">
                <MapPin className="w-3 h-3" />
                <span>{property.city}, {property.state} {property.zipCode}</span>
              </div>
              <div className="mt-2 text-xs text-gray-500">
                Owner: {property.owner || 'Unknown'}
              </div>
            </div>
            <div className="text-right">
              <div className="flex items-center gap-1 text-green-600">
                <DollarSign className="w-4 h-4" />
                <span className="font-bold">{formatCurrency(property.marketValue)}</span>
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {formatNumber(property.landSqFt)} sqft
              </div>
              {property.yearBuilt && (
                <Badge variant="outline" className="mt-1 text-xs">
                  Built {property.yearBuilt}
                </Badge>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  // Check if more items need to be loaded
  const isItemLoaded = (index: number) => !hasMore || index < properties.length;

  // Load more items
  const loadMoreItems = (startIndex: number, stopIndex: number) => {
    return loadMoreProperties(startIndex);
  };

  // Render a property or loading skeleton
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    if (!isItemLoaded(index)) {
      return (
        <div style={style} className="px-4">
          <Card className="h-full">
            <CardContent className="p-4">
              <Skeleton className="h-4 w-3/4 mb-2" />
              <Skeleton className="h-3 w-1/2 mb-2" />
              <Skeleton className="h-3 w-1/3" />
            </CardContent>
          </Card>
        </div>
      );
    }

    const property = properties[index];
    return <PropertyCard property={property} style={style} />;
  };

  return (
    <div className="flex flex-col h-full">
      {/* Search and Filters Header */}
      <div className="bg-white border-b p-4 space-y-4">
        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <Input
            type="text"
            placeholder="Search by address, owner, or city..."
            value={searchQuery}
            onChange={handleSearchChange}
            className="pl-10 pr-4"
          />
        </div>

        {/* Quick Filters */}
        <div className="flex flex-wrap gap-2">
          {/* Popular Cities */}
          <Select value={filters.city || 'all'} onValueChange={(value) => handleFilterChange('city', value)}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select City" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Cities</SelectItem>
              {popularCities.map(city => (
                <SelectItem key={city} value={city}>{city}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* Price Range */}
          <div className="flex gap-2">
            <Input
              type="number"
              placeholder="Min Price"
              value={filters.minValue}
              onChange={(e) => handleFilterChange('minValue', e.target.value)}
              className="w-32"
            />
            <Input
              type="number"
              placeholder="Max Price"
              value={filters.maxValue}
              onChange={(e) => handleFilterChange('maxValue', e.target.value)}
              className="w-32"
            />
          </div>

          {/* Sort Options */}
          <Select value={filters.sortBy} onValueChange={(value) => handleFilterChange('sortBy', value)}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Sort By" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="parcel_id">Property ID</SelectItem>
              <SelectItem value="just_value">Market Value</SelectItem>
              <SelectItem value="phy_city">City</SelectItem>
            </SelectContent>
          </Select>

          <Button
            variant="outline"
            onClick={() => {
              setFilters({
                city: '',
                minValue: '',
                maxValue: '',
                propertyType: '',
                sortBy: 'parcel_id',
                sortOrder: 'asc'
              });
              setSearchQuery('');
              resetAndSearch('');
            }}
          >
            Clear Filters
          </Button>
        </div>

        {/* Results Count */}
        {totalCount !== null && (
          <div className="text-sm text-gray-600">
            Found {formatNumber(totalCount)} properties
            {isLoading && ' (Loading more...)'}
          </div>
        )}
      </div>

      {/* Virtualized Property List */}
      <div className="flex-1">
        <AutoSizer>
          {({ height, width }) => (
            <InfiniteLoader
              ref={infiniteLoaderRef}
              isItemLoaded={isItemLoaded}
              itemCount={hasMore ? properties.length + 1 : properties.length}
              loadMoreItems={loadMoreItems}
            >
              {({ onItemsRendered, ref }) => (
                <List
                  ref={ref}
                  height={height}
                  itemCount={hasMore ? properties.length + 1 : properties.length}
                  itemSize={() => ITEM_HEIGHT}
                  width={width}
                  onItemsRendered={onItemsRendered}
                  overscanCount={BUFFER_SIZE}
                >
                  {Row}
                </List>
              )}
            </InfiniteLoader>
          )}
        </AutoSizer>
      </div>
    </div>
  );
};