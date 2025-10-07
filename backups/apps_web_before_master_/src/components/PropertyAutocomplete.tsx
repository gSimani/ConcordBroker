import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Search, MapPin, Home, TrendingUp, User, Calendar, DollarSign, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { debounce } from 'lodash';
import { supabase } from '../lib/supabase';

interface PropertyResult {
  parcel_id: string;
  address: string;
  city: string;
  zip: string;
  owner: string;
  value: number;
  year_built: number;
  sqft: number;
  sale_date?: string;
  sale_price?: number;
  relevance?: number;
}

interface AutocompleteProps {
  onSelect?: (property: PropertyResult) => void;
  placeholder?: string;
  className?: string;
  showFullResults?: boolean;
}

// Function to normalize address and create variations for better matching
const normalizeAddress = (address: string): string[] => {
  const variations = [address];
  
  // Original address
  const upper = address.toUpperCase();
  variations.push(upper);
  
  // Remove periods and commas
  const noPunctuation = address.replace(/[.,]/g, '');
  variations.push(noPunctuation);
  variations.push(noPunctuation.toUpperCase());
  
  // Handle numbered streets (e.g., "53 Ct" -> "53RD CT", "53rd Court")
  const numberPattern = /(\d+)\s*(st|nd|rd|th)?\s*(street|st|avenue|ave|av|court|ct|place|pl|drive|dr|road|rd|boulevard|blvd|lane|ln|terrace|ter|way|circle|cir)?\b/gi;
  const matches = address.match(numberPattern);
  
  if (matches) {
    matches.forEach(match => {
      const num = match.match(/\d+/)?.[0];
      if (num) {
        // Add ordinal suffix variations
        const ordinalNum = addOrdinalSuffix(parseInt(num));
        
        // Common street type variations
        const streetTypes = {
          'ct': ['CT', 'COURT', 'CRT'],
          'court': ['COURT', 'CT', 'CRT'],
          'st': ['ST', 'STREET', 'STR'],
          'street': ['STREET', 'ST', 'STR'],
          'ave': ['AVE', 'AVENUE', 'AV'],
          'avenue': ['AVENUE', 'AVE', 'AV'],
          'dr': ['DR', 'DRIVE', 'DRV'],
          'drive': ['DRIVE', 'DR', 'DRV'],
          'rd': ['RD', 'ROAD'],
          'road': ['ROAD', 'RD'],
          'pl': ['PL', 'PLACE'],
          'place': ['PLACE', 'PL'],
          'ln': ['LN', 'LANE'],
          'lane': ['LANE', 'LN'],
          'blvd': ['BLVD', 'BOULEVARD'],
          'boulevard': ['BOULEVARD', 'BLVD'],
          'ter': ['TER', 'TERRACE', 'TERR'],
          'terrace': ['TERRACE', 'TER', 'TERR'],
          'cir': ['CIR', 'CIRCLE'],
          'circle': ['CIRCLE', 'CIR'],
          'way': ['WAY', 'WY']
        };
        
        // Create variations with ordinal numbers
        variations.push(address.replace(match, ordinalNum));
        variations.push(address.toUpperCase().replace(match.toUpperCase(), ordinalNum.toUpperCase()));
        
        // Replace with just the number
        variations.push(address.replace(match, num));
        
        // Try different street type variations
        Object.keys(streetTypes).forEach(key => {
          if (match.toLowerCase().includes(key)) {
            streetTypes[key].forEach(replacement => {
              const newAddress = address.replace(new RegExp(key, 'gi'), replacement);
              variations.push(newAddress);
            });
          }
        });
      }
    });
  }
  
  // Handle direction abbreviations (N, S, E, W, NE, NW, SE, SW)
  const directions = {
    'north': 'N',
    'south': 'S',
    'east': 'E',
    'west': 'W',
    'northeast': 'NE',
    'northwest': 'NW',
    'southeast': 'SE',
    'southwest': 'SW',
    'n': 'NORTH',
    's': 'SOUTH',
    'e': 'EAST',
    'w': 'WEST',
    'ne': 'NORTHEAST',
    'nw': 'NORTHWEST',
    'se': 'SOUTHEAST',
    'sw': 'SOUTHWEST'
  };
  
  Object.keys(directions).forEach(dir => {
    const pattern = new RegExp(`\\b${dir}\\b`, 'gi');
    if (pattern.test(address)) {
      variations.push(address.replace(pattern, directions[dir]));
    }
  });
  
  // Remove extra spaces and trim
  const cleanedVariations = variations.map(v => v.replace(/\s+/g, ' ').trim());
  
  // Remove duplicates
  return [...new Set(cleanedVariations)];
};

// Helper function to add ordinal suffix to numbers
const addOrdinalSuffix = (num: number): string => {
  const j = num % 10;
  const k = num % 100;
  
  if (j === 1 && k !== 11) {
    return num + 'ST';
  }
  if (j === 2 && k !== 12) {
    return num + 'ND';
  }
  if (j === 3 && k !== 13) {
    return num + 'RD';
  }
  return num + 'TH';
};

export const PropertyAutocomplete: React.FC<AutocompleteProps> = ({
  onSelect,
  placeholder = "Search by address, city, owner, or parcel ID...",
  className = "",
  showFullResults = true
}) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<PropertyResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [totalResults, setTotalResults] = useState(0);
  const [searchTime, setSearchTime] = useState(0);
  const [cached, setCached] = useState(false);
  
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const abortControllerRef = useRef<AbortController | null>(null);

  // Format currency
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Format date
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      year: 'numeric'
    });
  };

  // Search function using Supabase directly - optimized
  const searchProperties = useCallback(async (searchQuery: string) => {
    if (searchQuery.length < 1) {
      setResults([]);
      setShowDropdown(false);
      return;
    }

    setLoading(true);
    setShowDropdown(true);

    try {
      const startTime = Date.now();
      const normalizedQuery = searchQuery.trim();
      
      // Normalize address for better matching
      // Handle variations like "SW 53 Ct" vs "SW 53RD CT"
      const addressVariations = normalizeAddress(normalizedQuery);
      
      // Build OR conditions for all variations
      const orConditions = [];
      addressVariations.forEach(variation => {
        orConditions.push(`phy_addr1.ilike.%${variation}%`);
      });
      
      // Add other fields to search
      orConditions.push(
        `parcel_id.ilike.%${normalizedQuery}%`,
        `owner_name.ilike.%${normalizedQuery}%`,
        `phy_city.ilike.%${normalizedQuery}%`
      );
      
      // Single optimized query that searches all fields at once
      let query = supabase
        .from('florida_parcels')
        .select('parcel_id, phy_addr1, phy_city, phy_zipcd, owner_name, taxable_value, year_built, total_living_area, sale_date, sale_price')
        .eq('is_redacted', false)
        .or(orConditions.join(','))
        .order('taxable_value', { ascending: false })
        .limit(30); // Get more results for better selection
      
      const { data: results, error } = await query;
      
      if (error) {
        console.error('Search error:', error);
        setResults([]);
        return;
      }
      
      // Sort results to prioritize address matches
      const allResults = (results || []).sort((a, b) => {
        const queryLower = normalizedQuery.toLowerCase();
        const aAddress = a.phy_addr1?.toLowerCase() || '';
        const bAddress = b.phy_addr1?.toLowerCase() || '';
        
        // Check for exact match at start of address
        const aStartsWith = aAddress.startsWith(queryLower);
        const bStartsWith = bAddress.startsWith(queryLower);
        
        if (aStartsWith && !bStartsWith) return -1;
        if (!aStartsWith && bStartsWith) return 1;
        
        // Check for any address match
        const aAddressMatch = aAddress.includes(queryLower);
        const bAddressMatch = bAddress.includes(queryLower);
        
        if (aAddressMatch && !bAddressMatch) return -1;
        if (!aAddressMatch && bAddressMatch) return 1;
        
        // Secondary sort by taxable value
        return (b.taxable_value || 0) - (a.taxable_value || 0);
      }).slice(0, 20); // Show top 20 results
      
      // Map Supabase response to expected format
      const mappedResults = allResults.map((prop: any, index: number) => ({
        parcel_id: prop.parcel_id,
        address: prop.phy_addr1 || '',
        city: prop.phy_city || '',
        zip: prop.phy_zipcd || '',
        owner: prop.owner_name || '',
        value: prop.taxable_value || 0,
        year_built: prop.year_built || 0,
        sqft: prop.total_living_area || 0,
        sale_date: prop.sale_date,
        sale_price: prop.sale_price,
        // Mark address matches with higher relevance
        relevance: prop.phy_addr1?.toLowerCase().includes(normalizedQuery) ? 1.0 : 0.7
      }));
      
      setResults(mappedResults);
      setTotalResults(mappedResults.length);
      setSearchTime((Date.now() - startTime) / 1000);
      setCached(false);
      
    } catch (error: any) {
      console.error('Search error:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Debounced search - reduced delay for faster response
  const debouncedSearch = useCallback(
    debounce(searchProperties, 150),
    []
  );

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    setSelectedIndex(-1);
    
    if (value.length >= 1) {
      debouncedSearch(value);
    } else {
      setResults([]);
      setShowDropdown(false);
    }
  };

  // Handle keyboard navigation with scroll into view
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showDropdown || results.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => {
          const newIndex = prev < results.length - 1 ? prev + 1 : prev;
          // Scroll to selected item
          setTimeout(() => {
            const element = document.getElementById(`property-result-${newIndex}`);
            element?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
          }, 0);
          return newIndex;
        });
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => {
          const newIndex = prev > 0 ? prev - 1 : -1;
          // Scroll to selected item
          if (newIndex >= 0) {
            setTimeout(() => {
              const element = document.getElementById(`property-result-${newIndex}`);
              element?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }, 0);
          }
          return newIndex;
        });
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < results.length) {
          handleSelectProperty(results[selectedIndex]);
        } else if (results.length > 0) {
          handleSelectProperty(results[0]);
        }
        break;
      case 'Escape':
        setShowDropdown(false);
        setSelectedIndex(-1);
        break;
    }
  };

  // Handle property selection
  const handleSelectProperty = (property: PropertyResult) => {
    setQuery(property.address);
    setShowDropdown(false);
    setSelectedIndex(-1);
    
    if (onSelect) {
      onSelect(property);
    } else {
      // Navigate to property detail page
      navigate(`/property/${property.parcel_id}`);
    }
  };

  // Click outside handler
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className={`relative ${className}`}>
      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => query.length >= 1 && results.length > 0 && setShowDropdown(true)}
          placeholder={placeholder}
          className="w-full pl-10 pr-10 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm"
          autoComplete="off"
        />
        {loading && (
          <Loader2 className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 animate-spin" />
        )}
      </div>

      {/* Results Dropdown */}
      {showDropdown && (results.length > 0 || loading) && (
        <div
          ref={dropdownRef}
          className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-xl"
          style={{ maxHeight: '450px', overflowY: 'auto', overflowX: 'hidden' }}
        >
          {/* Loading State */}
          {loading && results.length === 0 && (
            <div className="p-4 space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="animate-pulse">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-gray-200 rounded"></div>
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                      <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                    </div>
                    <div className="h-4 bg-gray-200 rounded w-20"></div>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          {/* Search Stats */}
          {!loading && totalResults > 0 && (
            <div className="px-4 py-2 border-b border-gray-100 bg-gray-50 sticky top-0">
              <div className="flex items-center justify-between text-xs text-gray-600">
                <span>
                  Found {totalResults} {totalResults === 1 ? 'property' : 'properties'}
                </span>
                <div className="flex items-center gap-2">
                  {searchTime > 0 && searchTime < 0.5 && (
                    <span className="text-green-600">Fast</span>
                  )}
                  {searchTime > 0 && (
                    <span>{(searchTime * 1000).toFixed(0)}ms</span>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Property Results */}
          <div className="divide-y divide-gray-100">
            {results.map((property, index) => (
              <div
                key={property.parcel_id}
                id={`property-result-${index}`}
                className={`px-4 py-3 cursor-pointer transition-colors ${
                  index === selectedIndex
                    ? 'bg-blue-50'
                    : 'hover:bg-gray-50'
                }`}
                onClick={() => handleSelectProperty(property)}
                onMouseEnter={() => setSelectedIndex(index)}
              >
                {showFullResults ? (
                  <div className="space-y-2">
                    {/* Address and City */}
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <Home className="w-4 h-4 text-gray-400 flex-shrink-0" />
                          <div>
                            <p className="font-medium text-gray-900 text-sm">
                              {property.address}
                            </p>
                            <p className="text-xs text-gray-500">
                              {property.city}, FL {property.zip}
                            </p>
                          </div>
                        </div>
                      </div>
                      {/* Value */}
                      <div className="text-right">
                        <p className="font-semibold text-gray-900 text-sm">
                          {formatCurrency(property.value)}
                        </p>
                        {property.relevance && (
                          <p className="text-xs text-gray-500">
                            {property.relevance === 1.0 ? 'Address match' : 'Other match'}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Property Details */}
                    <div className="flex items-center gap-4 text-xs text-gray-600">
                      {/* Owner */}
                      <div className="flex items-center gap-1">
                        <User className="w-3 h-3" />
                        <span className="truncate max-w-[150px]">{property.owner}</span>
                      </div>
                      
                      {/* Year Built */}
                      {property.year_built && (
                        <div className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          <span>{property.year_built}</span>
                        </div>
                      )}
                      
                      {/* Square Feet */}
                      {property.sqft && (
                        <div className="flex items-center gap-1">
                          <Home className="w-3 h-3" />
                          <span>{property.sqft.toLocaleString()} sqft</span>
                        </div>
                      )}
                      
                      {/* Recent Sale */}
                      {property.sale_date && property.sale_price && (
                        <div className="flex items-center gap-1">
                          <DollarSign className="w-3 h-3" />
                          <span>
                            Sold {formatDate(property.sale_date)} for {formatCurrency(property.sale_price)}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Parcel ID */}
                    <div className="text-xs text-gray-400">
                      Parcel: {property.parcel_id}
                    </div>
                  </div>
                ) : (
                  /* Simple View */
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-gray-400" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {property.address}
                        </p>
                        <p className="text-xs text-gray-500">
                          {property.city}, FL
                        </p>
                      </div>
                    </div>
                    <p className="text-sm font-medium text-gray-900">
                      {formatCurrency(property.value)}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* View All Results - Show when we have max results */}
          {results.length >= 15 && (
            <div className="px-4 py-3 border-t border-gray-100 bg-gray-50 sticky bottom-0">
              <button
                onClick={() => {
                  navigate(`/properties?q=${encodeURIComponent(query)}`);
                  setShowDropdown(false);
                }}
                className="w-full text-center text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
              >
                View more results →
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};