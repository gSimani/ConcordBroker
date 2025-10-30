/**
 * Optimized Search Bar Component
 * Lightning-fast search with intelligent caching, debouncing, and suggestions
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Search, Clock, Zap, TrendingUp, X, Filter, MapPin, User, Home, Building2,
  Store, Factory, TreePine, Landmark, Church, Hotel, Wrench, Truck, Banknote,
  Utensils, Building, GraduationCap, Cross
} from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { useOptimizedSearch } from '@/hooks/useOptimizedSearch';
import { useSearchDebounce } from '@/hooks/useDebounce';
import { api } from '@/api/client';
import { usePropertyAutocomplete } from '@/hooks/usePropertyAutocomplete';
import { getPropertyIcon, getPropertyIconColor, type PropertyIconType } from '@/lib/dorUseCodes';

interface Suggestion {
  type: 'address' | 'owner' | 'city' | 'history';
  display: string;
  value: string;
  property_type?: string;
  metadata?: any;
}

interface SearchBarProps {
  onResults: (results: any) => void;
  onFiltersChange?: (filters: Record<string, any>) => void;
  placeholder?: string;
  showMetrics?: boolean;
  enableVoiceSearch?: boolean;
  county?: string; // Dynamic county filter for autocomplete
}

interface SearchMetrics {
  cacheHitRate: number;
  avgResponseTime: number;
  cacheSize: number;
  totalRequests: number;
}

// Icon component map - maps icon names from DOR codes to actual Lucide React components
const ICON_MAP: Record<PropertyIconType, React.ComponentType<any>> = {
  'Home': Home,
  'Building2': Building2,
  'Store': Store,
  'Factory': Factory,
  'TreePine': TreePine,
  'Landmark': Landmark,
  'Church': Church,
  'Hotel': Hotel,
  'MapPin': MapPin,
  'Wrench': Wrench,
  'Truck': Truck,
  'Banknote': Banknote,
  'Utensils': Utensils,
  'Building': Building,
  'GraduationCap': GraduationCap,
  'Cross': Cross,
  'Zap': Zap,
};

// Helper function to get the actual icon component for a property type
const getPropertyIconComponent = (propertyUseCode?: string): React.ComponentType<any> => {
  if (!propertyUseCode) return Home;

  const iconName = getPropertyIcon(propertyUseCode);
  return ICON_MAP[iconName] || Home;
};

export function OptimizedSearchBar({
  onResults,
  onFiltersChange,
  placeholder = "Search by address (e.g. '123 Main St'), city, county, or owner name...",
  showMetrics = true,
  enableVoiceSearch = false,
  county
}: SearchBarProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [isVoiceSearching, setIsVoiceSearching] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeFilters, setActiveFilters] = useState<Record<string, any>>({});
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  const [autocompleteLoading, setAutocompleteLoading] = useState(false);
  const [combinedSuggestions, setCombinedSuggestions] = useState<Suggestion[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);
  const autocompleteTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const {
    search,
    searchInstant,
    getSuggestions,
    loading,
    results,
    suggestions,
    metrics,
    clearCache,
    preloadPopularSearches
  } = useOptimizedSearch();

  // Use Supabase-powered autocomplete for real data (with dynamic county filtering)
  const { suggestions: supabaseSuggestions, loading: supabaseLoading, searchProperties } = usePropertyAutocomplete(county);

  // Performance metrics state
  const [performanceMetrics, setPerformanceMetrics] = useState<SearchMetrics>({
    cacheHitRate: 0,
    avgResponseTime: 0,
    cacheSize: 0,
    totalRequests: 0
  });

  // Smart debounced search with instant results for cached queries
  const debouncedSearch = useSearchDebounce(
    useCallback((filters: Record<string, any>) => {
      search(filters);
    }, [search]),
    250, // Faster debounce for better UX
    useCallback((args) => {
      // Check if query might be cached (simple heuristic)
      const [filters] = args;
      return searchHistory.includes(filters.address || filters.city || '');
    }, [searchHistory])
  );

  // Fetch autocomplete suggestions using Supabase
  const fetchAutocompleteData = useCallback((query: string) => {
    if (query.length < 3) {
      setCombinedSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    // Trigger Supabase search
    searchProperties(query);
    setShowSuggestions(true);
  }, [searchProperties]);

  // Sync Supabase suggestions to combined suggestions
  useEffect(() => {
    if (supabaseSuggestions.length > 0) {
      // Map Supabase suggestions to combined format with correct property names
      const suggestions: Suggestion[] = supabaseSuggestions.map(s => ({
        type: s.type,                    // Use existing type (address/owner/city)
        display: s.display,              // Correct: s.display not s.address
        value: s.value,                  // Correct: s.value directly
        property_type: s.property_type,  // Correct: s.property_type
        metadata: {
          city: s.metadata?.city,              // Correct: nested in metadata
          county: county,                      // Dynamic county filter (no default)
          zip_code: s.metadata?.zip_code,      // Correct: nested, note underscore
          parcel_id: s.metadata?.parcel_id,    // Correct: nested, note underscore
          owner_name: s.metadata?.owner_name,  // Correct: nested, note underscore
          just_value: s.metadata?.just_value,  // Correct: nested, note underscore
          matchScore: 1.0                      // Default match score
        }
      }));
      setCombinedSuggestions(suggestions);
      setAutocompleteLoading(false);
    } else if (!supabaseLoading && searchTerm.length >= 3) {
      // No results from Supabase, show search history
      if (searchHistory.length > 0) {
        const historySuggestions: Suggestion[] = searchHistory.slice(0, 5).map(term => ({
          type: 'history',
          display: term,
          value: term
        }));
        setCombinedSuggestions(historySuggestions);
      } else {
        setCombinedSuggestions([]);
      }
      setAutocompleteLoading(false);
    }
  }, [supabaseSuggestions, supabaseLoading, searchTerm, searchHistory]);

  // Update autocomplete loading state
  useEffect(() => {
    setAutocompleteLoading(supabaseLoading);
  }, [supabaseLoading]);

  // Handle search input changes
  const handleSearchChange = useCallback((value: string) => {
    setSearchTerm(value);

    // Clear existing timeout
    if (autocompleteTimeoutRef.current) {
      clearTimeout(autocompleteTimeoutRef.current);
    }

    // Only fetch autocomplete suggestions - DO NOT trigger search on every keystroke
    autocompleteTimeoutRef.current = setTimeout(() => {
      fetchAutocompleteData(value);
    }, 150); // Reduced from 300ms to 150ms for faster response
  }, [fetchAutocompleteData]);

  // Handle suggestion selection
  const handleSuggestionSelect = useCallback((suggestion: Suggestion) => {
    const selectedValue = suggestion.value;
    setSearchTerm(selectedValue);
    setShowSuggestions(false);
    setCombinedSuggestions([]);

    // Clear autocomplete timeout
    if (autocompleteTimeoutRef.current) {
      clearTimeout(autocompleteTimeoutRef.current);
    }

    // Add to search history
    setSearchHistory(prev => {
      const updated = [selectedValue, ...prev.filter(s => s !== selectedValue)].slice(0, 10);
      localStorage.setItem('search-history', JSON.stringify(updated));
      return updated;
    });

    // Determine search field based on suggestion type
    const searchFilters = {
      ...activeFilters,
      [suggestion.type === 'owner' ? 'owner' : 'address']: selectedValue
    };

    // Perform instant search
    if (searchInstant) {
      searchInstant(searchFilters).then(result => {
        onResults(result);
      });
    }

    if (onFiltersChange) {
      onFiltersChange(searchFilters);
    }

    inputRef.current?.focus();
  }, [activeFilters, onResults, onFiltersChange, searchInstant]);

  // Voice search functionality
  const handleVoiceSearch = useCallback(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Voice search not supported in this browser');
      return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    setIsVoiceSearching(true);

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      handleSearchChange(transcript);
      setIsVoiceSearching(false);
    };

    recognition.onerror = () => {
      setIsVoiceSearching(false);
    };

    recognition.onend = () => {
      setIsVoiceSearching(false);
    };

    recognition.start();
  }, [handleSearchChange]);

  // Execute search with current search term
  const executeSearch = useCallback(async () => {
    // Prevent multiple simultaneous searches
    if (isSearching || !searchTerm.trim()) {
      return;
    }

    const searchFilters = {
      ...activeFilters,
      address: searchTerm
    };

    // Set loading state immediately for instant visual feedback
    setIsSearching(true);

    try {
      if (onFiltersChange) {
        onFiltersChange(searchFilters);
      }

      // Perform instant search with proper error handling
      if (searchInstant) {
        const result = await searchInstant(searchFilters);
        onResults(result);
      }

      // Hide suggestions after successful search
      setShowSuggestions(false);
      setCombinedSuggestions([]);
    } catch (error) {
      // Handle errors gracefully
      console.error('Search execution failed:', error);
      // Don't clear results on error - keep previous results visible
    } finally {
      // Always clear loading state
      setIsSearching(false);
    }
  }, [activeFilters, searchTerm, onFiltersChange, searchInstant, onResults, isSearching]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setShowSuggestions(false);
      setCombinedSuggestions([]);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (combinedSuggestions.length > 0) {
        // Select first suggestion
        handleSuggestionSelect(combinedSuggestions[0]);
      } else {
        // Execute search with current term
        executeSearch();
      }
    }
  }, [combinedSuggestions, handleSuggestionSelect, executeSearch]);

  // Handle click outside to close suggestions
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target as Node) &&
        !inputRef.current?.contains(event.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Update performance metrics
  useEffect(() => {
    const updateMetrics = () => {
      const currentMetrics = metrics();
      setPerformanceMetrics(currentMetrics);
    };

    const interval = setInterval(updateMetrics, 1000);
    return () => clearInterval(interval);
  }, [metrics]);

  // Load search history on mount
  useEffect(() => {
    const saved = localStorage.getItem('search-history');
    if (saved) {
      try {
        setSearchHistory(JSON.parse(saved));
      } catch {
        // Ignore invalid JSON
      }
    }

    // Preload popular searches
    preloadPopularSearches();
  }, [preloadPopularSearches]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (autocompleteTimeoutRef.current) {
        clearTimeout(autocompleteTimeoutRef.current);
      }
    };
  }, []);

  // Clear search
  const handleClear = useCallback(() => {
    setSearchTerm('');
    setShowSuggestions(false);
    setActiveFilters({});
    if (onFiltersChange) {
      onFiltersChange({});
    }
    inputRef.current?.focus();
  }, [onFiltersChange]);

  // Delete individual search history item
  const handleDeleteSearchHistory = useCallback((term: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent triggering the search
    const updated = searchHistory.filter(s => s !== term);
    setSearchHistory(updated);
    localStorage.setItem('search-history', JSON.stringify(updated));
  }, [searchHistory]);

  // Clear all search history
  const handleClearAllHistory = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setSearchHistory([]);
    localStorage.removeItem('search-history');
  }, []);

  // Get performance status color
  const getPerformanceColor = (responseTime: number) => {
    if (responseTime < 100) return 'text-green-600';
    if (responseTime < 300) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="relative w-full">
      {/* Performance Metrics */}
      {showMetrics && performanceMetrics.totalRequests > 0 && (
        <div className="flex gap-2 mb-2 text-xs text-gray-500">
          <Badge variant="outline" className="flex items-center gap-1">
            <TrendingUp className="w-3 h-3" />
            Cache: {performanceMetrics.cacheHitRate.toFixed(1)}%
          </Badge>
          <Badge variant="outline" className={`flex items-center gap-1 ${getPerformanceColor(performanceMetrics.avgResponseTime)}`}>
            <Clock className="w-3 h-3" />
            {performanceMetrics.avgResponseTime.toFixed(0)}ms
          </Badge>
          <Badge variant="outline" className="flex items-center gap-1">
            <Zap className="w-3 h-3" />
            {performanceMetrics.cacheSize} cached
          </Badge>
        </div>
      )}

      {/* Search Input */}
      <div className="relative">
        <div className="relative flex items-center">
          <Search className="absolute left-3 w-4 h-4 text-gray-400" />

          <Input
            ref={inputRef}
            type="text"
            value={searchTerm}
            onChange={(e) => handleSearchChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="pl-10 pr-24 h-12 text-base"
            disabled={loading}
          />

          <div className="absolute right-2 flex items-center gap-1">
            {/* Search Button - only show when there's text */}
            {searchTerm && !loading && (
              <Button
                size="sm"
                onClick={executeSearch}
                disabled={isSearching || loading || !searchTerm.trim()}
                className="h-8 px-3 bg-[#d4af37] hover:bg-[#c4a137] text-white disabled:opacity-50 disabled:cursor-not-allowed"
                title="Search (or press Enter)"
              >
                {isSearching ? (
                  <>
                    <div className="w-3 h-3 mr-1 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Searching...
                  </>
                ) : (
                  <>
                    <Search className="w-3 h-3 mr-1" />
                    Search
                  </>
                )}
              </Button>
            )}

            {/* Voice Search Button */}
            {enableVoiceSearch && !searchTerm && (
              <Button
                size="sm"
                variant="ghost"
                onClick={handleVoiceSearch}
                disabled={isVoiceSearching}
                className="h-8 w-8 p-0"
              >
                {isVoiceSearching ? (
                  <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                ) : (
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                    <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                  </svg>
                )}
              </Button>
            )}

            {/* Clear Button */}
            {searchTerm && (
              <Button
                size="sm"
                variant="ghost"
                onClick={handleClear}
                className="h-8 w-8 p-0"
              >
                <X className="w-3 h-3" />
              </Button>
            )}

            {/* Loading Indicator */}
            {loading && (
              <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            )}
          </div>
        </div>

        {/* Enhanced Suggestions Dropdown */}
        {showSuggestions && combinedSuggestions.length > 0 && (
          <Card
            ref={suggestionsRef}
            className="absolute top-full left-0 right-0 z-50 mt-1 max-h-80 overflow-y-auto shadow-xl border-gray-200"
          >
            <CardContent className="p-0">
              {autocompleteLoading && (
                <div className="p-3 text-center">
                  <div className="inline-flex items-center gap-2 text-sm text-gray-500">
                    <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                    Loading suggestions...
                  </div>
                </div>
              )}
              {combinedSuggestions.map((suggestion, index) => {
                // DEBUG: Log property type data
                if (suggestion.type === 'address' && index === 0) {
                  console.log('[AUTOCOMPLETE DEBUG]', {
                    display: suggestion.display,
                    property_type: suggestion.property_type,
                    iconName: getPropertyIcon(suggestion.property_type),
                    iconColor: getPropertyIconColor(suggestion.property_type),
                    metadata: suggestion.metadata
                  });
                }

                // Select icon based on suggestion type
                // For both ADDRESS and OWNER types, use property-specific icons based on USE code
                const Icon = (suggestion.type === 'address' || suggestion.type === 'owner')
                  ? getPropertyIconComponent(suggestion.property_type)
                  : suggestion.type === 'city'
                  ? MapPin
                  : Clock;

                // Select color based on DOR use code
                // For both ADDRESS and OWNER types, use property-specific colors based on USE code
                const iconColor = (suggestion.type === 'address' || suggestion.type === 'owner')
                  ? getPropertyIconColor(suggestion.property_type)
                  : suggestion.type === 'city'
                  ? 'text-purple-500'
                  : 'text-gray-400';

                const bgColor = suggestion.type === 'address' ? 'hover:bg-blue-50' :
                               suggestion.type === 'owner' ? 'hover:bg-green-50' :
                               suggestion.type === 'city' ? 'hover:bg-purple-50' : 'hover:bg-gray-50';

                return (
                  <div
                    key={`${suggestion.type}-${index}`}
                    className={`p-3 ${bgColor} cursor-pointer border-b last:border-b-0 flex items-center gap-3 transition-colors`}
                    onClick={() => handleSuggestionSelect(suggestion)}
                  >
                    <Icon className={`w-4 h-4 ${iconColor} flex-shrink-0`} />
                    <div className="flex-1 min-w-0">
                      <span className="text-sm text-gray-900 block truncate">{suggestion.display}</span>
                      {/* Show USE description for both ADDRESS and OWNER types */}
                      {(suggestion.type === 'address' || suggestion.type === 'owner') && suggestion.metadata?.property_use_desc && (
                        <span className="text-xs text-blue-600 font-medium">
                          {suggestion.metadata.property_use_desc}
                        </span>
                      )}
                      {suggestion.type === 'address' && suggestion.metadata && (
                        <span className="text-xs text-gray-500 block">
                          {suggestion.metadata.city} {suggestion.metadata.zip_code}
                          {suggestion.metadata.owner_name && suggestion.metadata.owner_name !== '-' && suggestion.metadata.owner_name !== '' && (
                            <span className="text-green-600 font-medium"> • {suggestion.metadata.owner_name}</span>
                          )}
                        </span>
                      )}
                      {suggestion.type === 'owner' && suggestion.metadata && (
                        <span className="text-xs text-gray-500 block">
                          {suggestion.metadata.city} {suggestion.metadata.zip_code}
                        </span>
                      )}
                      {suggestion.type === 'city' && (
                        <span className="text-xs text-gray-500 block">City</span>
                      )}
                      {suggestion.type === 'history' && (
                        <span className="text-xs text-gray-500 block">Recent Search</span>
                      )}
                    </div>
                    {suggestion.type === 'history' && (
                      <Clock className="w-3 h-3 text-gray-400 flex-shrink-0" />
                    )}
                  </div>
                );
              })}
            </CardContent>
          </Card>
        )}

        {/* Search History - when no current suggestions */}
        {!showSuggestions && searchTerm === '' && searchHistory.length > 0 && (
          <Card className="absolute top-full left-0 right-0 z-50 mt-1">
            <CardContent className="p-0">
              <div className="p-2 text-xs text-gray-500 border-b bg-gray-50 flex items-center justify-between">
                <span>Recent Searches</span>
                <button
                  onClick={handleClearAllHistory}
                  className="text-xs text-red-500 hover:text-red-700 hover:underline transition-colors"
                  title="Clear all recent searches"
                >
                  Clear All
                </button>
              </div>
              {searchHistory.slice(0, 5).map((term, index) => (
                <div
                  key={index}
                  className="group p-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0 flex items-center gap-2"
                  onClick={() => handleSuggestionSelect({
                    type: 'history',
                    display: term,
                    value: term
                  })}
                >
                  <Clock className="w-4 h-4 text-gray-400 flex-shrink-0" />
                  <span className="text-sm text-gray-600 flex-1">{term}</span>
                  <button
                    onClick={(e) => handleDeleteSearchHistory(term, e)}
                    className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-red-100 rounded"
                    title="Delete this search"
                  >
                    <X className="w-3 h-3 text-red-500" />
                  </button>
                </div>
              ))}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Quick Actions */}
      <div className="flex gap-2 mt-2">
        <Button
          size="sm"
          variant="outline"
          onClick={clearCache}
          className="text-xs"
        >
          Clear Cache
        </Button>

        <Button
          size="sm"
          variant="outline"
          onClick={preloadPopularSearches}
          className="text-xs"
        >
          Preload Popular
        </Button>

        {results && (
          <Badge variant="secondary" className="text-xs">
            {results.total.toLocaleString()} results
            {results.cached && <span className="ml-1">(cached)</span>}
          </Badge>
        )}
      </div>
    </div>
  );
}

export default OptimizedSearchBar;
