/**
 * SearchFilters Component
 * =======================
 *
 * A comprehensive search and filter component for property search.
 * Supports text search, dropdown filters, range filters, and more.
 *
 * Features:
 * - Text search with debounce
 * - Dropdown/select filters
 * - Range filters (price, value)
 * - Date range filters
 * - Active filter chips with remove
 * - Collapsible advanced filters
 * - Mobile-friendly design
 */

import React, { useState, useCallback, useEffect, useMemo } from 'react';
import {
  Search,
  X,
  ChevronDown,
  SlidersHorizontal,
  RotateCcw,
} from 'lucide-react';
import { cn } from '@/lib/utils';

export interface FilterOption {
  value: string;
  label: string;
  count?: number;
}

export interface FilterConfig {
  id: string;
  label: string;
  type: 'select' | 'multi-select' | 'range' | 'date-range' | 'boolean';
  options?: FilterOption[];
  min?: number;
  max?: number;
  step?: number;
  placeholder?: string;
}

export interface FilterValues {
  [key: string]: string | string[] | [number, number] | [string, string] | boolean | undefined;
}

export interface SearchFiltersProps {
  /** Filter configuration */
  filters: FilterConfig[];
  /** Current filter values */
  values: FilterValues;
  /** Callback when filters change */
  onChange: (values: FilterValues) => void;
  /** Search placeholder */
  searchPlaceholder?: string;
  /** Show advanced filters toggle */
  showAdvanced?: boolean;
  /** Number of visible filters before "more" */
  visibleFilters?: number;
  /** Additional class names */
  className?: string;
}

/**
 * Debounce hook for search input
 */
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

/**
 * FilterChip component for displaying active filters
 */
const FilterChip: React.FC<{
  label: string;
  value: string;
  onRemove: () => void;
}> = ({ label, value, onRemove }) => (
  <span className="inline-flex items-center gap-1 px-2 py-1 text-sm bg-[#0ABAB5]/10 text-[#0ABAB5] rounded-full">
    <span className="text-neutral-600">{label}:</span>
    <span className="font-medium">{value}</span>
    <button
      onClick={onRemove}
      className="ml-1 p-0.5 hover:bg-[#0ABAB5]/20 rounded-full"
      aria-label={`Remove ${label} filter`}
    >
      <X size={14} />
    </button>
  </span>
);

/**
 * SelectFilter component
 */
const SelectFilter: React.FC<{
  config: FilterConfig;
  value: string | undefined;
  onChange: (value: string | undefined) => void;
}> = ({ config, value, onChange }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'w-full flex items-center justify-between gap-2 px-3 py-2',
          'border rounded-lg text-sm transition-colors',
          value
            ? 'border-[#0ABAB5] bg-[#0ABAB5]/5'
            : 'border-neutral-200 hover:border-neutral-300'
        )}
      >
        <span className={value ? 'text-neutral-900' : 'text-neutral-500'}>
          {value
            ? config.options?.find((o) => o.value === value)?.label
            : config.placeholder || config.label}
        </span>
        <ChevronDown
          size={16}
          className={cn('transition-transform', isOpen && 'rotate-180')}
        />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute top-full left-0 right-0 mt-1 py-1 bg-white border border-neutral-200 rounded-lg shadow-lg z-50 max-h-60 overflow-y-auto">
            <button
              onClick={() => {
                onChange(undefined);
                setIsOpen(false);
              }}
              className="w-full px-3 py-2 text-sm text-left text-neutral-500 hover:bg-neutral-50"
            >
              All {config.label}
            </button>
            {config.options?.map((option) => (
              <button
                key={option.value}
                onClick={() => {
                  onChange(option.value);
                  setIsOpen(false);
                }}
                className={cn(
                  'w-full px-3 py-2 text-sm text-left hover:bg-neutral-50',
                  'flex items-center justify-between',
                  value === option.value && 'bg-[#0ABAB5]/5 text-[#0ABAB5]'
                )}
              >
                <span>{option.label}</span>
                {option.count !== undefined && (
                  <span className="text-neutral-400">{option.count}</span>
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

/**
 * RangeFilter component
 */
const RangeFilter: React.FC<{
  config: FilterConfig;
  value: [number, number] | undefined;
  onChange: (value: [number, number] | undefined) => void;
}> = ({ config, value, onChange }) => {
  const [localMin, setLocalMin] = useState(value?.[0]?.toString() || '');
  const [localMax, setLocalMax] = useState(value?.[1]?.toString() || '');

  const handleBlur = () => {
    const min = localMin ? parseFloat(localMin) : undefined;
    const max = localMax ? parseFloat(localMax) : undefined;
    if (min !== undefined || max !== undefined) {
      onChange([min ?? config.min ?? 0, max ?? config.max ?? Infinity]);
    } else {
      onChange(undefined);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <input
        type="number"
        value={localMin}
        onChange={(e) => setLocalMin(e.target.value)}
        onBlur={handleBlur}
        placeholder="Min"
        className={cn(
          'w-24 px-3 py-2 border rounded-lg text-sm',
          'border-neutral-200 focus:border-[#0ABAB5] focus:ring-1 focus:ring-[#0ABAB5]',
          'outline-none transition-colors'
        )}
      />
      <span className="text-neutral-400">-</span>
      <input
        type="number"
        value={localMax}
        onChange={(e) => setLocalMax(e.target.value)}
        onBlur={handleBlur}
        placeholder="Max"
        className={cn(
          'w-24 px-3 py-2 border rounded-lg text-sm',
          'border-neutral-200 focus:border-[#0ABAB5] focus:ring-1 focus:ring-[#0ABAB5]',
          'outline-none transition-colors'
        )}
      />
    </div>
  );
};

/**
 * SearchFilters component for property search and filtering
 */
export const SearchFilters: React.FC<SearchFiltersProps> = ({
  filters,
  values,
  onChange,
  searchPlaceholder = 'Search properties...',
  showAdvanced = true,
  visibleFilters = 4,
  className,
}) => {
  const [searchInput, setSearchInput] = useState(
    (values.search as string) || ''
  );
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const debouncedSearch = useDebounce(searchInput, 300);

  // Update search value when debounced
  useEffect(() => {
    if (debouncedSearch !== values.search) {
      onChange({ ...values, search: debouncedSearch || undefined });
    }
  }, [debouncedSearch]);

  // Handle filter change
  const handleFilterChange = useCallback(
    (filterId: string, value: any) => {
      onChange({ ...values, [filterId]: value });
    },
    [values, onChange]
  );

  // Clear all filters
  const handleClearAll = useCallback(() => {
    setSearchInput('');
    onChange({});
  }, [onChange]);

  // Get active filters
  const activeFilters = useMemo(() => {
    const active: { id: string; label: string; value: string }[] = [];

    Object.entries(values).forEach(([key, value]) => {
      if (key === 'search' || !value) return;

      const config = filters.find((f) => f.id === key);
      if (!config) return;

      if (config.type === 'select' && typeof value === 'string') {
        const option = config.options?.find((o) => o.value === value);
        active.push({
          id: key,
          label: config.label,
          value: option?.label || value,
        });
      } else if (config.type === 'range' && Array.isArray(value)) {
        const [min, max] = value as [number, number];
        active.push({
          id: key,
          label: config.label,
          value: `$${min.toLocaleString()} - $${max.toLocaleString()}`,
        });
      }
    });

    return active;
  }, [values, filters]);

  const visibleFilterConfigs = filters.slice(0, visibleFilters);
  const advancedFilterConfigs = filters.slice(visibleFilters);
  const hasActiveFilters = activeFilters.length > 0 || searchInput;

  return (
    <div className={cn('space-y-4', className)}>
      {/* Search and primary filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        {/* Search input */}
        <div className="relative flex-1">
          <Search
            size={18}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400"
          />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder={searchPlaceholder}
            className={cn(
              'w-full h-10 pl-10 pr-4 rounded-lg',
              'border border-neutral-200',
              'text-neutral-900 placeholder:text-neutral-400',
              'focus:outline-none focus:border-[#0ABAB5] focus:ring-1 focus:ring-[#0ABAB5]',
              'transition-colors duration-150'
            )}
          />
          {searchInput && (
            <button
              onClick={() => setSearchInput('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-600"
              aria-label="Clear search"
            >
              <X size={16} />
            </button>
          )}
        </div>

        {/* Visible filters */}
        <div className="flex flex-wrap gap-2">
          {visibleFilterConfigs.map((config) => (
            <div key={config.id} className="w-40">
              {config.type === 'select' && (
                <SelectFilter
                  config={config}
                  value={values[config.id] as string | undefined}
                  onChange={(v) => handleFilterChange(config.id, v)}
                />
              )}
              {config.type === 'range' && (
                <RangeFilter
                  config={config}
                  value={values[config.id] as [number, number] | undefined}
                  onChange={(v) => handleFilterChange(config.id, v)}
                />
              )}
            </div>
          ))}

          {/* Advanced filters toggle */}
          {showAdvanced && advancedFilterConfigs.length > 0 && (
            <button
              onClick={() => setAdvancedOpen(!advancedOpen)}
              className={cn(
                'flex items-center gap-2 px-3 py-2',
                'border rounded-lg text-sm transition-colors',
                advancedOpen
                  ? 'border-[#0ABAB5] bg-[#0ABAB5]/5 text-[#0ABAB5]'
                  : 'border-neutral-200 hover:border-neutral-300 text-neutral-600'
              )}
            >
              <SlidersHorizontal size={16} />
              More Filters
            </button>
          )}

          {/* Clear all button */}
          {hasActiveFilters && (
            <button
              onClick={handleClearAll}
              className="flex items-center gap-2 px-3 py-2 text-sm text-neutral-600 hover:text-neutral-900"
            >
              <RotateCcw size={16} />
              Clear All
            </button>
          )}
        </div>
      </div>

      {/* Advanced filters panel */}
      {advancedOpen && advancedFilterConfigs.length > 0 && (
        <div className="p-4 bg-neutral-50 rounded-lg border border-neutral-200">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {advancedFilterConfigs.map((config) => (
              <div key={config.id}>
                <label className="block text-sm font-medium text-neutral-700 mb-1">
                  {config.label}
                </label>
                {config.type === 'select' && (
                  <SelectFilter
                    config={config}
                    value={values[config.id] as string | undefined}
                    onChange={(v) => handleFilterChange(config.id, v)}
                  />
                )}
                {config.type === 'range' && (
                  <RangeFilter
                    config={config}
                    value={values[config.id] as [number, number] | undefined}
                    onChange={(v) => handleFilterChange(config.id, v)}
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Active filter chips */}
      {activeFilters.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {activeFilters.map((filter) => (
            <FilterChip
              key={filter.id}
              label={filter.label}
              value={filter.value}
              onRemove={() => handleFilterChange(filter.id, undefined)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default SearchFilters;
