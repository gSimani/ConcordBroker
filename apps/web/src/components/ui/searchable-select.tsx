import React, { useState, useRef, useEffect } from 'react';
import { Search, ChevronDown, X, MapPin, Building2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SearchableSelectOption {
  value: string;
  label: string;
  count?: number;
  icon?: React.ReactNode;
}

interface SearchableSelectProps {
  placeholder?: string;
  value?: string;
  options: SearchableSelectOption[];
  onValueChange: (value: string) => void;
  className?: string;
  icon?: React.ReactNode;
  emptyMessage?: string;
  allowClear?: boolean;
  maxHeight?: number;
  showCounts?: boolean;
}

export function SearchableSelect({
  placeholder = "Select...",
  value,
  options,
  onValueChange,
  className,
  icon,
  emptyMessage = "No options found",
  allowClear = true,
  maxHeight = 300,
  showCounts = true
}: SearchableSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredOptions, setFilteredOptions] = useState(options);
  const [highlightedIndex, setHighlightedIndex] = useState(0);

  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Filter options based on search query
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredOptions(options);
    } else {
      const filtered = options.filter(option =>
        option.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        option.value.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredOptions(filtered);
    }
    setHighlightedIndex(0);
  }, [searchQuery, options]);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setHighlightedIndex(prev =>
            prev < filteredOptions.length - 1 ? prev + 1 : 0
          );
          break;
        case 'ArrowUp':
          e.preventDefault();
          setHighlightedIndex(prev =>
            prev > 0 ? prev - 1 : filteredOptions.length - 1
          );
          break;
        case 'Enter':
          e.preventDefault();
          if (filteredOptions[highlightedIndex]) {
            onValueChange(filteredOptions[highlightedIndex].value);
            setIsOpen(false);
            setSearchQuery('');
          }
          break;
        case 'Escape':
          e.preventDefault();
          setIsOpen(false);
          setSearchQuery('');
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filteredOptions, highlightedIndex, onValueChange]);

  // Scroll highlighted option into view
  useEffect(() => {
    if (isOpen && listRef.current) {
      const highlightedElement = listRef.current.children[highlightedIndex] as HTMLElement;
      if (highlightedElement) {
        highlightedElement.scrollIntoView({
          block: 'nearest',
          behavior: 'smooth'
        });
      }
    }
  }, [highlightedIndex, isOpen]);

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchQuery('');
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus search input when opened
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen]);

  const selectedOption = options.find(option => option.value === value);

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onValueChange('');
    setSearchQuery('');
  };

  const handleOptionSelect = (optionValue: string) => {
    onValueChange(optionValue);
    setIsOpen(false);
    setSearchQuery('');
  };

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "flex items-center justify-between w-full px-3 py-2 text-sm",
          "bg-background border border-input rounded-lg",
          "hover:bg-accent hover:text-accent-foreground",
          "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
          "disabled:cursor-not-allowed disabled:opacity-50",
          "transition-colors duration-200",
          isOpen && "ring-2 ring-ring ring-offset-2"
        )}
        style={{
          borderColor: isOpen ? '#d4af37' : '#ecf0f1',
          backgroundColor: isOpen ? 'rgba(212, 175, 55, 0.05)' : 'white'
        }}
      >
        <div className="flex items-center space-x-2 flex-1 text-left">
          {icon && <span className="text-gray-500">{icon}</span>}
          <span className={cn(
            "truncate",
            !selectedOption && "text-muted-foreground"
          )}>
            {selectedOption ? (
              <div className="flex items-center space-x-2">
                {selectedOption.icon && selectedOption.icon}
                <span>{selectedOption.label}</span>
                {showCounts && selectedOption.count !== undefined && (
                  <span className="text-xs text-gray-500">
                    ({selectedOption.count.toLocaleString()})
                  </span>
                )}
              </div>
            ) : (
              placeholder
            )}
          </span>
        </div>

        <div className="flex items-center space-x-1">
          {allowClear && selectedOption && (
            <div
              role="button"
              tabIndex={0}
              onClick={handleClear}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleClear(e as any);
                }
              }}
              className="p-1 hover:bg-gray-100 rounded transition-colors cursor-pointer"
            >
              <X className="w-3 h-3 text-gray-500" />
            </div>
          )}
          <ChevronDown className={cn(
            "w-4 h-4 text-gray-500 transition-transform",
            isOpen && "rotate-180"
          )} />
        </div>
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg">
          {/* Search Input */}
          <div className="p-3 border-b border-gray-100">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                ref={searchInputRef}
                type="text"
                placeholder={`Search ${placeholder.toLowerCase()}...`}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              />
            </div>
          </div>

          {/* Options List */}
          <div
            ref={listRef}
            className="max-h-60 overflow-auto"
            style={{ maxHeight: `${maxHeight}px` }}
          >
            {filteredOptions.length === 0 ? (
              <div className="p-4 text-center text-gray-500 text-sm">
                {emptyMessage}
              </div>
            ) : (
              filteredOptions.map((option, index) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => handleOptionSelect(option.value)}
                  className={cn(
                    "w-full px-4 py-3 text-left hover:bg-gray-50 flex items-center justify-between",
                    "focus:outline-none focus:bg-gray-50 transition-colors",
                    index === highlightedIndex && "bg-blue-50",
                    value === option.value && "bg-blue-100 text-blue-900 font-medium"
                  )}
                >
                  <div className="flex items-center space-x-2">
                    {option.icon && <span className="text-gray-500">{option.icon}</span>}
                    <span className="text-sm">{option.label}</span>
                  </div>
                  {showCounts && option.count !== undefined && (
                    <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                      {option.count.toLocaleString()}
                    </span>
                  )}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}