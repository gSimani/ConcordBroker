import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Search, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { UseIcon, getUseIcon } from '@/lib/icons/useIcons';

interface AutocompleteSuggestion {
  address?: string;
  city?: string;
  zip_code?: string;
  owner_name?: string;
  property_type?: string;
  parcel_id?: string;
  type?: string;
  full_address?: string;

  // Unit information
  unit_number?: string;
  is_condo?: boolean;

  // Property data fields for mini cards
  own_name?: string;
  just_value?: number;
  jv?: number;
  market_value?: number;
  phy_addr1?: string;
  phy_addr2?: string;
  phy_city?: string;
  phy_zipcd?: string;
  property_use_desc?: string;
}

interface AutocompleteSearchBarProps {
  onSearch?: (value: string, suggestion?: AutocompleteSuggestion) => void;
  onSelect?: (suggestion: AutocompleteSuggestion) => void;
  placeholder?: string;
  className?: string;
  apiUrl?: string;
}

export function AutocompleteSearchBar({
  onSearch,
  onSelect,
  placeholder = "Search by address (e.g. '123 Main St') to find properties...",
  className,
  apiUrl = (
    typeof window !== 'undefined' && window.location.hostname === 'localhost'
      ? 'http://localhost:8003' // Use autocomplete API on port 8003 in development
      : '/api/autocomplete-ultra' // Use ultra-fast Vercel API in production
  )
}: AutocompleteSearchBarProps) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<AutocompleteSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [responseTime, setResponseTime] = useState<number | null>(null);
  const [apiStatus, setApiStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
  const [hasFocus, setHasFocus] = useState(false);

  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);
  const abortController = useRef<AbortController | null>(null);

  // Cache for faster repeat queries
  const queryCache = useRef<Map<string, { data: AutocompleteSuggestion[], timestamp: number }>>(new Map());
  const CACHE_TTL = 30000; // 30 seconds

  // Check API status on mount
  useEffect(() => {
    checkApiStatus();
  }, [apiUrl]);

  const checkApiStatus = async () => {
    try {
      const response = await fetch(`${apiUrl}/health`, {
        signal: AbortSignal.timeout(3000)
      });
      if (response.ok) {
        setApiStatus('connected');
      } else {
        setApiStatus('error');
      }
    } catch (error) {
      // Try the autocomplete endpoint directly
      try {
        const response = await fetch(`${apiUrl}/api/autocomplete/combined?q=test&limit=1`, {
          signal: AbortSignal.timeout(3000)
        });
        if (response.ok) {
          setApiStatus('connected');
        } else {
          setApiStatus('error');
        }
      } catch {
        setApiStatus('error');
      }
    }
  };

  // Get cached result if available
  const getCacheEntry = (searchQuery: string) => {
    const entry = queryCache.current.get(searchQuery.toUpperCase());
    if (entry && (Date.now() - entry.timestamp) < CACHE_TTL) {
      return entry.data;
    }
    queryCache.current.delete(searchQuery.toUpperCase());
    return null;
  };

  // Set cache entry
  const setCacheEntry = (searchQuery: string, data: AutocompleteSuggestion[]) => {
    queryCache.current.set(searchQuery.toUpperCase(), {
      data,
      timestamp: Date.now()
    });
  };

  const fetchSuggestions = async (searchQuery: string) => {
    if (!searchQuery || searchQuery.length < 2) {
      setSuggestions([]);
      setShowDropdown(false);
      return;
    }

    // Check cache first
    const cached = getCacheEntry(searchQuery);
    if (cached) {
      setSuggestions(cached);
      setShowDropdown(true);
      setResponseTime(0);
      return;
    }

    setIsLoading(true);
    const startTime = performance.now();

    // Cancel any pending request
    if (abortController.current) {
      abortController.current.abort();
    }

    abortController.current = new AbortController();

    try {
      // Handle both absolute URLs (localhost) and relative paths (Vercel API)
      const url = apiUrl.startsWith('http')
        ? `${apiUrl}/api/autocomplete/combined?q=${encodeURIComponent(searchQuery)}&limit=20`
        : `${apiUrl}?q=${encodeURIComponent(searchQuery)}&limit=20`;
      console.log('AutocompleteSearchBar fetching:', url);

      const response = await fetch(
        url,
        {
          signal: abortController.current.signal,
          headers: {
            'Accept': 'application/json',
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        const endTime = performance.now();
        setResponseTime(Math.round(endTime - startTime));

        // Handle both response formats (success wrapper and direct suggestions)
        let suggestionData = [];
        if (data.suggestions && Array.isArray(data.suggestions)) {
          suggestionData = data.suggestions;
        } else if (data.success && data.data && Array.isArray(data.data)) {
          suggestionData = data.data;
        } else if (data.data && Array.isArray(data.data)) {
          suggestionData = data.data;
        }

        if (suggestionData.length > 0) {
          console.log('AutocompleteSearchBar: Got', suggestionData.length, 'suggestions for:', searchQuery);
          setSuggestions(suggestionData);
          setShowDropdown(true);
          setCacheEntry(searchQuery, suggestionData);
          setApiStatus('connected');
        } else {
          console.log('AutocompleteSearchBar: No suggestions in response');
          setSuggestions([]);
          setShowDropdown(false);
        }
      } else {
        console.log('AutocompleteSearchBar: API error, status:', response.status);
        setSuggestions([]);
        setShowDropdown(false);
        setApiStatus('error');
      }
    } catch (error: any) {
      if (error.name !== 'AbortError') {
        console.error('Search error:', error);
        setSuggestions([]);
        setShowDropdown(false);
        setApiStatus('error');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    console.log('AutocompleteSearchBar input change:', value, 'apiUrl:', apiUrl);
    setQuery(value);
    setSelectedIndex(-1);

    // Clear existing timer
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    // Cancel any pending request
    if (abortController.current) {
      abortController.current.abort();
    }

    // Ultra-fast debounce for immediate responsiveness (50ms)
    debounceTimer.current = setTimeout(() => {
      fetchSuggestions(value);
    }, 50);

    // Call onSearch if provided
    if (onSearch) {
      onSearch(value);
    }
  };

  const handleSuggestionClick = (suggestion: AutocompleteSuggestion) => {
    // Use the full address or primary address for display
    const displayValue = suggestion.full_address || suggestion.address || suggestion.phy_addr1 || '';
    setQuery(displayValue);
    setShowDropdown(false);
    setSuggestions([]);

    if (onSelect) {
      onSelect(suggestion);
    }

    if (onSearch) {
      onSearch(displayValue, suggestion);
    }

    // Remove focus from input to prevent dropdown from reopening
    inputRef.current?.blur();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showDropdown || suggestions.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev =>
          prev < suggestions.length - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev =>
          prev > 0 ? prev - 1 : suggestions.length - 1
        );
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
          handleSuggestionClick(suggestions[selectedIndex]);
        }
        break;
      case 'Escape':
        setShowDropdown(false);
        setSelectedIndex(-1);
        break;
    }
  };

  const handleClear = () => {
    setQuery('');
    setSuggestions([]);
    setShowDropdown(false);
    setSelectedIndex(-1);
    if (onSearch) {
      onSearch('');
    }
  };

  // Close dropdown when clicking outside
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

    // Only close on window resize if dropdown is open
    const handleResize = () => {
      // Don't close dropdown, just let it reposition naturally
      // The fixed positioning with calculated coordinates will handle this
    };

    // Only close on scroll if scrolling outside the dropdown area
    const handleScroll = (event: Event) => {
      // Check if the scroll is happening within the dropdown itself
      if (dropdownRef.current && dropdownRef.current.contains(event.target as Node)) {
        // Allow scrolling within the dropdown
        return;
      }
      // Only close if we're scrolling the main window/document significantly
      // Small scrolls shouldn't close the dropdown
    };

    document.addEventListener('mousedown', handleClickOutside);
    window.addEventListener('resize', handleResize);
    // Note: We're not adding scroll listener to avoid closing on minor scrolls

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      window.removeEventListener('resize', handleResize);
    };
  }, [showDropdown]);

  // Get icon for suggestion type using centralized icon mapping
  const getSuggestionIcon = (suggestion: AutocompleteSuggestion) => {
    // If API provides icon, use it (decode if needed)
    if ((suggestion as any).icon) {
      const icon = (suggestion as any).icon;
      // Handle potential encoding issues
      if (typeof icon === 'string' && icon.length > 0) {
        return <span className="text-xl" style={{ fontFamily: 'emoji' }}>{icon}</span>;
      }
    }

    // Special case for owner/company suggestions
    if (suggestion.type === 'owner') {
      return <span className="text-xl" style={{ fontFamily: 'emoji' }}>👤</span>;
    }
    if (suggestion.type === 'company') {
      return <UseIcon category="commercial" showEmoji size={20} className="text-xl" />;
    }

    // Use centralized icon mapping for property types
    const propType = suggestion.property_type || (suggestion as any).use_category || '';
    return <UseIcon category={propType} showEmoji size={20} className="text-xl" />;
  };

  // Format suggestion display for address with unit numbers
  const formatSuggestion = (suggestion: AutocompleteSuggestion) => {
    // Format the property value
    const value = suggestion.just_value || suggestion.jv || suggestion.market_value;
    const valueStr = value ? ` • $${(value/1000).toFixed(0)}K` : '';

    // Format address and location - address already includes unit if available
    const address = suggestion.address || suggestion.phy_addr1 || '';
    const city = suggestion.city || suggestion.phy_city || '';
    const zip = suggestion.zip_code || suggestion.phy_zipcd || '';
    const owner = suggestion.owner_name || suggestion.own_name || '';

    // Add condo indicator if applicable
    const typeIndicator = suggestion.is_condo ? ' (Condo)' : '';

    return {
      primary: address,
      secondary: `${city} ${zip}${typeIndicator}${owner ? ` • ${owner}` : ''}${valueStr}`
    };
  };

  return (
    <div className="relative w-full">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground pointer-events-none" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            setHasFocus(true);
            if (suggestions.length > 0) {
              setShowDropdown(true);
            }
          }}
          onBlur={(e) => {
            // Don't hide dropdown immediately - let click events fire first
            setTimeout(() => {
              if (!dropdownRef.current?.contains(e.relatedTarget as Node)) {
                setHasFocus(false);
                setShowDropdown(false);
              }
            }, 200);
          }}
          placeholder={placeholder}
          className={cn(
            "flex w-full rounded-md border border-input bg-background px-3 py-2 ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
            "pl-10 pr-24 h-12 text-base",
            className
          )}
        />

        {/* Status and Clear button */}
        <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
          {responseTime !== null && (
            <span className="text-xs text-muted-foreground">
              {responseTime}ms
            </span>
          )}
          {apiStatus === 'connected' && (
            <span className="text-xs text-green-600">Live</span>
          )}
          {apiStatus === 'error' && (
            <span className="text-xs text-red-600">Offline</span>
          )}
          {query && (
            <button
              onClick={handleClear}
              className="p-1 hover:bg-gray-100 rounded"
              type="button"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          {isLoading && (
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-primary border-t-transparent" />
          )}
        </div>
      </div>

      {/* Dropdown - Keep stable and don't flicker */}
      {showDropdown && suggestions.length > 0 && (
        <div
          ref={dropdownRef}
          className="fixed bg-white rounded-md border shadow-lg max-h-96 overflow-y-auto z-[9999]"
          style={{
            top: inputRef.current ? inputRef.current.getBoundingClientRect().bottom + window.scrollY + 4 : 0,
            left: inputRef.current ? inputRef.current.getBoundingClientRect().left + window.scrollX : 0,
            width: inputRef.current ? inputRef.current.getBoundingClientRect().width : 0
          }}
        >
          {suggestions.map((suggestion, index) => {
            const { primary, secondary } = formatSuggestion(suggestion);
            return (
              <div
                key={index}
                onClick={() => handleSuggestionClick(suggestion)}
                className={cn(
                  "flex items-start gap-3 px-4 py-3 cursor-pointer transition-colors border-b last:border-b-0",
                  selectedIndex === index ? "bg-gray-100" : "hover:bg-gray-50"
                )}
              >
                <div className="mt-1 text-muted-foreground">
                  {getSuggestionIcon(suggestion)}
                </div>
                <div className="flex-1">
                  <div className="font-medium text-sm">
                    {primary}
                  </div>
                  <div className="text-xs text-muted-foreground mt-0.5">
                    {secondary}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* No results message */}
      {showDropdown && suggestions.length === 0 && !isLoading && query.length >= 2 && (
        <div
          className="fixed bg-white rounded-md border shadow-lg p-4"
          style={{
            top: inputRef.current ? inputRef.current.getBoundingClientRect().bottom + window.scrollY + 4 : 0,
            left: inputRef.current ? inputRef.current.getBoundingClientRect().left + window.scrollX : 0,
            width: inputRef.current ? inputRef.current.getBoundingClientRect().width : 0
          }}
        >
          <p className="text-sm text-muted-foreground text-center">
            No properties found for "{query}"
          </p>
        </div>
      )}
    </div>
  );
}
