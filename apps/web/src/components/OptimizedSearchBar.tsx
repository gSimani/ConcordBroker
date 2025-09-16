/**
 * Optimized Search Bar Component
 * Lightning-fast search with intelligent caching, debouncing, and suggestions
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Search, Clock, Zap, TrendingUp, X, Filter } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { useOptimizedSearch } from '@/hooks/useOptimizedSearch';
import { useSearchDebounce } from '@/hooks/useDebounce';

interface SearchBarProps {
  onResults: (results: any) => void;
  onFiltersChange?: (filters: Record<string, any>) => void;
  placeholder?: string;
  showMetrics?: boolean;
  enableVoiceSearch?: boolean;
}

interface SearchMetrics {
  cacheHitRate: number;
  avgResponseTime: number;
  cacheSize: number;
  totalRequests: number;
}

export function OptimizedSearchBar({
  onResults,
  onFiltersChange,
  placeholder = "Search properties by address, city, or owner...",
  showMetrics = true,
  enableVoiceSearch = false
}: SearchBarProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [isVoiceSearching, setIsVoiceSearching] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeFilters, setActiveFilters] = useState<Record<string, any>>({});
  const [searchHistory, setSearchHistory] = useState<string[]>([]);

  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

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

  // Handle search input changes
  const handleSearchChange = useCallback((value: string) => {
    setSearchTerm(value);

    // Get suggestions immediately for fast feedback
    if (value.length >= 2) {
      getSuggestions(value, 'address').then(() => {
        setShowSuggestions(true);
      });
    } else {
      setShowSuggestions(false);
    }

    // Trigger search with current filters
    const searchFilters = {
      ...activeFilters,
      address: value
    };

    if (onFiltersChange) {
      onFiltersChange(searchFilters);
    }

    // Perform debounced search
    debouncedSearch(searchFilters);
  }, [activeFilters, getSuggestions, onFiltersChange, debouncedSearch]);

  // Handle suggestion selection
  const handleSuggestionSelect = useCallback((suggestion: string) => {
    setSearchTerm(suggestion);
    setShowSuggestions(false);

    // Add to search history
    setSearchHistory(prev => {
      const updated = [suggestion, ...prev.filter(s => s !== suggestion)].slice(0, 10);
      localStorage.setItem('search-history', JSON.stringify(updated));
      return updated;
    });

    // Perform instant search
    const searchFilters = {
      ...activeFilters,
      address: suggestion
    };

    searchInstant(searchFilters).then(result => {
      onResults(result);
    });

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

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
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

  // Handle keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setShowSuggestions(false);
    } else if (e.key === 'Enter' && suggestions.length > 0) {
      handleSuggestionSelect(suggestions[0]);
    }
  }, [suggestions, handleSuggestionSelect]);

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

  // Update results when search completes
  useEffect(() => {
    if (results) {
      onResults(results);
    }
  }, [results, onResults]);

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
            {/* Voice Search Button */}
            {enableVoiceSearch && (
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
                <X className="w-4 h-4" />
              </Button>
            )}

            {/* Loading Indicator */}
            {loading && (
              <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            )}
          </div>
        </div>

        {/* Suggestions Dropdown */}
        {showSuggestions && suggestions.length > 0 && (
          <Card
            ref={suggestionsRef}
            className="absolute top-full left-0 right-0 z-50 mt-1 max-h-80 overflow-y-auto"
          >
            <CardContent className="p-0">
              {suggestions.map((suggestion, index) => (
                <div
                  key={index}
                  className="p-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0 flex items-center gap-2"
                  onClick={() => handleSuggestionSelect(suggestion)}
                >
                  <Search className="w-4 h-4 text-gray-400" />
                  <span className="text-sm">{suggestion}</span>
                  {searchHistory.includes(suggestion) && (
                    <Clock className="w-3 h-3 text-gray-400 ml-auto" />
                  )}
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Search History */}
        {!showSuggestions && searchTerm === '' && searchHistory.length > 0 && (
          <Card className="absolute top-full left-0 right-0 z-50 mt-1">
            <CardContent className="p-0">
              <div className="p-2 text-xs text-gray-500 border-b bg-gray-50">
                Recent Searches
              </div>
              {searchHistory.slice(0, 5).map((term, index) => (
                <div
                  key={index}
                  className="p-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0 flex items-center gap-2"
                  onClick={() => handleSuggestionSelect(term)}
                >
                  <Clock className="w-4 h-4 text-gray-400" />
                  <span className="text-sm text-gray-600">{term}</span>
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