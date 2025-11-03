import React, { useState, useEffect, useRef } from 'react';
import { Search, MapPin, Home, Building2, Loader2, User } from 'lucide-react';
import { cn } from '@/lib/utils';
import { usePropertyAutocomplete, type Suggestion } from '@/hooks/usePropertyAutocomplete';

// Use Suggestion from the hook
type AddressSuggestion = Suggestion;

interface AddressAutocompleteProps {
  value: string;
  onChange: (value: string) => void;
  onSelect?: (suggestion: AddressSuggestion) => void;
  placeholder?: string;
  className?: string;
  autoFocus?: boolean;
}

export function AddressAutocomplete({
  value,
  onChange,
  onSelect,
  placeholder = "Search by address (e.g. '123 Main St'), city, or owner name...",
  className,
  autoFocus = false
}: AddressAutocompleteProps) {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Use the Supabase-powered autocomplete hook
  const { suggestions, loading, searchProperties } = usePropertyAutocomplete();

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    onChange(newValue);
    setSelectedIndex(-1);

    if (newValue.length >= 3) {
      searchProperties(newValue);
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }
  };

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showSuggestions || suggestions.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev =>
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => prev > 0 ? prev - 1 : -1);
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
          handleSelectSuggestion(suggestions[selectedIndex]);
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        setSelectedIndex(-1);
        break;
    }
  };

  // Handle suggestion selection
  const handleSelectSuggestion = (suggestion: AddressSuggestion) => {
    onChange(suggestion.address);
    setShowSuggestions(false);
    setSelectedIndex(-1);

    if (onSelect) {
      onSelect(suggestion);
    }
  };

  // Close suggestions on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Scroll selected item into view
  useEffect(() => {
    if (selectedIndex >= 0 && suggestionsRef.current) {
      const selectedElement = suggestionsRef.current.children[selectedIndex] as HTMLElement;
      if (selectedElement) {
        selectedElement.scrollIntoView({
          behavior: 'smooth',
          block: 'nearest'
        });
      }
    }
  }, [selectedIndex]);

  const getIcon = (type: string) => {
    switch (type) {
      case 'property':
        return <Home className="w-4 h-4" />;
      case 'owner':
        return <User className="w-4 h-4" />;
      case 'city':
        return <Building2 className="w-4 h-4" />;
      default:
        return <MapPin className="w-4 h-4" />;
    }
  };

  return (
    <div className="relative flex items-center" ref={containerRef}>
      <Search className="absolute left-3 w-4 h-4 text-gray-400 pointer-events-none" />

      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onFocus={() => value.length >= 3 && suggestions.length > 0 && setShowSuggestions(true)}
        placeholder={placeholder}
        autoFocus={autoFocus}
        className={cn(
          "flex w-full rounded-md border border-input bg-background px-3 py-2",
          "ring-offset-background file:border-0 file:bg-transparent",
          "file:text-sm file:font-medium placeholder:text-muted-foreground",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          "focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
          "pl-10 pr-10 h-12 text-base",
          className
        )}
      />

      {loading && (
        <Loader2 className="absolute right-3 w-4 h-4 text-gray-400 animate-spin" />
      )}

      {showSuggestions && suggestions.length > 0 && (
        <div
          ref={suggestionsRef}
          className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-md shadow-lg z-50 max-h-80 overflow-y-auto"
        >
          {suggestions.map((suggestion, index) => (
            <div
              key={suggestion.id}
              onClick={() => handleSelectSuggestion(suggestion)}
              onMouseEnter={() => setSelectedIndex(index)}
              className={cn(
                "px-4 py-3 cursor-pointer transition-colors border-b border-gray-100 last:border-b-0",
                selectedIndex === index
                  ? "bg-blue-50 text-blue-900"
                  : "hover:bg-gray-50"
              )}
            >
              <div className="flex items-start gap-3">
                <div className="mt-1 text-gray-400">
                  {getIcon(suggestion.type)}
                </div>
                <div className="flex-1">
                  <div className="font-medium text-sm">
                    {suggestion.address}
                  </div>
                  <div className="text-xs text-gray-500 mt-1 flex items-center gap-2">
                    <span>{suggestion.city}, {suggestion.county} County</span>
                    {suggestion.metadata?.just_value && (
                      <span className="text-green-600 font-semibold">
                        ${(suggestion.metadata.just_value / 1000).toFixed(0)}K
                      </span>
                    )}
                  </div>
                  {suggestion.owner && (
                    <div className="text-xs text-gray-400 mt-1">
                      Owner: {suggestion.owner}
                    </div>
                  )}
                  {suggestion.parcelId && (
                    <div className="text-xs text-gray-400">
                      Parcel: {suggestion.parcelId}
                    </div>
                  )}
                </div>
                <div className="text-xs text-gray-400">
                  {Math.round(suggestion.matchScore * 100)}% match
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {showSuggestions && suggestions.length === 0 && !loading && value.length >= 3 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-md shadow-lg z-50 px-4 py-3 text-sm text-gray-500">
          No suggestions found for "{value}"
        </div>
      )}
    </div>
  );
}