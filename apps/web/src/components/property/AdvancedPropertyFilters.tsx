/**
 * Advanced Property Filters Component
 * Maps the HTML filter inputs (Min Value to Sub-Usage Code) to optimized database queries
 * Uses the exact CSS classes from the provided HTML structure
 */

import React, { useState, useCallback, useMemo } from 'react';
import { useAdvancedPropertySearch, usePropertyUseCodes } from '../../hooks/useAdvancedPropertySearch';

const inputClassName = "flex w-full border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 h-12 rounded-lg";

interface AdvancedPropertyFiltersProps {
  onResultsChange?: (results: any[], metadata: any) => void;
  className?: string;
}

export const AdvancedPropertyFilters: React.FC<AdvancedPropertyFiltersProps> = ({
  onResultsChange,
  className
}) => {
  // Use the advanced search hook
  const {
    results,
    metadata,
    isLoading,
    isError,
    error,
    search,
    setFilters,
    resetFilters,
    filters,
    suggestions
  } = useAdvancedPropertySearch();

  // Property use codes for validation
  const propertyUseCodes = usePropertyUseCodes();

  // Local state for form inputs
  const [formValues, setFormValues] = useState({
    minValue: '',
    maxValue: '',
    minSqft: '',
    maxSqft: '',
    minLandSqft: '',
    maxLandSqft: '',
    minYearBuilt: '',
    maxYearBuilt: '',
    propertyUseCode: '',
    subUsageCode: '',
    county: '',
    city: '',
    zipCode: '',
    minAssessedValue: '',
    maxAssessedValue: '',
    taxExempt: '',
    hasPool: '',
    waterfront: '',
    recentlySold: ''
  });

  // Handle input changes
  const handleInputChange = useCallback((field: string, value: string | boolean) => {
    setFormValues(prev => ({
      ...prev,
      [field]: value
    }));

    // Convert string values to numbers where appropriate
    const numericFields = [
      'minValue', 'maxValue', 'minSqft', 'maxSqft', 'minLandSqft', 'maxLandSqft',
      'minYearBuilt', 'maxYearBuilt', 'minAssessedValue', 'maxAssessedValue'
    ];

    const filterValue = numericFields.includes(field) && value !== ''
      ? parseInt(value as string, 10) || undefined
      : value || undefined;

    // Update filters with debouncing through the hook
    setFilters({
      [field]: filterValue
    });
  }, [setFilters]);

  // Handle form submission
  const handleSearch = useCallback(async (e?: React.FormEvent) => {
    e?.preventDefault();

    // Build filter object from form values
    const searchFilters = Object.entries(formValues).reduce((acc, [key, value]) => {
      if (value !== '' && value !== undefined) {
        const numericFields = [
          'minValue', 'maxValue', 'minSqft', 'maxSqft', 'minLandSqft', 'maxLandSqft',
          'minYearBuilt', 'maxYearBuilt', 'minAssessedValue', 'maxAssessedValue'
        ];

        acc[key] = numericFields.includes(key) ? parseInt(value as string, 10) : value;
      }
      return acc;
    }, {} as any);

    await search(searchFilters);
  }, [formValues, search]);

  // Handle reset
  const handleReset = useCallback(() => {
    setFormValues({
      minValue: '',
      maxValue: '',
      minSqft: '',
      maxSqft: '',
      minLandSqft: '',
      maxLandSqft: '',
      minYearBuilt: '',
      maxYearBuilt: '',
      propertyUseCode: '',
      subUsageCode: '',
      county: '',
      city: '',
      zipCode: '',
      minAssessedValue: '',
      maxAssessedValue: '',
      taxExempt: '',
      hasPool: '',
      waterfront: '',
      recentlySold: ''
    });
    resetFilters();
  }, [resetFilters]);

  // Notify parent component of results changes
  React.useEffect(() => {
    if (onResultsChange) {
      onResultsChange(results, metadata);
    }
  }, [results, metadata, onResultsChange]);

  // Quick filter buttons
  const quickFilters = useMemo(() => [
    { label: 'Under $300K', filters: { minValue: 0, maxValue: 300000 } },
    { label: '$300K - $600K', filters: { minValue: 300000, maxValue: 600000 } },
    { label: '$600K - $1M', filters: { minValue: 600000, maxValue: 1000000 } },
    { label: 'Over $1M', filters: { minValue: 1000000 } },
    { label: 'Single Family', filters: { propertyUseCode: '01' } },
    { label: 'Condos', filters: { propertyUseCode: '04' } },
    { label: 'New Construction', filters: { minYearBuilt: 2020 } },
    { label: 'Recently Sold', filters: { recentlySold: true } }
  ], []);

  return (
    <div className={`space-y-6 ${className || ''}`}>
      {/* Quick Filters */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {quickFilters.map((filter, index) => (
          <button
            key={index}
            onClick={() => {
              Object.entries(filter.filters).forEach(([key, value]) => {
                setFormValues(prev => ({ ...prev, [key]: value?.toString() || '' }));
                setFilters({ [key]: value });
              });
            }}
            className="px-3 py-2 text-sm bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg border border-blue-200 transition-colors"
          >
            {filter.label}
          </button>
        ))}
      </div>

      <form onSubmit={handleSearch} className="space-y-6">
        {/* Value Filters - Starting with Min Value as specified */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Min Value:</label>
            <input
              type="number"
              className={inputClassName}
              placeholder="100000"
              value={formValues.minValue}
              onChange={(e) => handleInputChange('minValue', e.target.value)}
              style={{ borderColor: 'rgb(236, 240, 241)' }}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Max Value:</label>
            <input
              type="number"
              className={inputClassName}
              placeholder="500000"
              value={formValues.maxValue}
              onChange={(e) => handleInputChange('maxValue', e.target.value)}
              style={{ borderColor: 'rgb(236, 240, 241)' }}
            />
          </div>
        </div>

        {/* Square Footage Filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Min Square Feet:</label>
            <input
              type="number"
              className={inputClassName}
              placeholder="1500"
              value={formValues.minSqft}
              onChange={(e) => handleInputChange('minSqft', e.target.value)}
              style={{ borderColor: 'rgb(236, 240, 241)' }}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Max Square Feet:</label>
            <input
              type="number"
              className={inputClassName}
              placeholder="3000"
              value={formValues.maxSqft}
              onChange={(e) => handleInputChange('maxSqft', e.target.value)}
              style={{ borderColor: 'rgb(236, 240, 241)' }}
            />
          </div>
        </div>

        {/* Land Size Filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Min Land Square Feet:</label>
            <input
              type="number"
              className={inputClassName}
              placeholder="5000"
              value={formValues.minLandSqft}
              onChange={(e) => handleInputChange('minLandSqft', e.target.value)}
              style={{ borderColor: 'rgb(236, 240, 241)' }}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Max Land Square Feet:</label>
            <input
              type="number"
              className={inputClassName}
              placeholder="20000"
              value={formValues.maxLandSqft}
              onChange={(e) => handleInputChange('maxLandSqft', e.target.value)}
              style={{ borderColor: 'rgb(236, 240, 241)' }}
            />
          </div>
        </div>

        {/* Year Built Filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Min Year Built:</label>
            <input
              type="number"
              className={inputClassName}
              placeholder="1990"
              value={formValues.minYearBuilt}
              onChange={(e) => handleInputChange('minYearBuilt', e.target.value)}
              style={{ borderColor: 'rgb(236, 240, 241)' }}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Max Year Built:</label>
            <input
              type="number"
              className={inputClassName}
              placeholder="2024"
              value={formValues.maxYearBuilt}
              onChange={(e) => handleInputChange('maxYearBuilt', e.target.value)}
              style={{ borderColor: 'rgb(236, 240, 241)' }}
            />
          </div>
        </div>

        {/* Location Filters */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">County:</label>
            <select
              className={inputClassName}
              value={formValues.county}
              onChange={(e) => handleInputChange('county', e.target.value)}
              style={{ borderColor: 'rgb(236, 240, 241)' }}
            >
              <option value="">All Counties</option>
              <option value="BROWARD">Broward</option>
              <option value="MIAMI-DADE">Miami-Dade</option>
              <option value="PALM BEACH">Palm Beach</option>
              <option value="MONROE">Monroe</option>
              <option value="COLLIER">Collier</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">City:</label>
            <input
              type="text"
              className={inputClassName}
              placeholder="e.g., Miami"
              value={formValues.city}
              onChange={(e) => handleInputChange('city', e.target.value)}
              style={{ borderColor: 'rgb(236, 240, 241)' }}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">ZIP Code:</label>
            <input
              type="text"
              className={inputClassName}
              placeholder="33101"
              value={formValues.zipCode}
              onChange={(e) => handleInputChange('zipCode', e.target.value)}
              style={{ borderColor: 'rgb(236, 240, 241)' }}
            />
          </div>
        </div>

        {/* Property Type Filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Property Use Code:</label>
            <select
              className={inputClassName}
              value={formValues.propertyUseCode}
              onChange={(e) => handleInputChange('propertyUseCode', e.target.value)}
              style={{ borderColor: 'rgb(236, 240, 241)' }}
            >
              <option value="">All Property Types</option>
              {Object.entries(propertyUseCodes).map(([code, description]) => (
                <option key={code} value={code}>
                  {code} - {description}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Sub-Usage Code:</label>
            <input
              className={inputClassName}
              placeholder="e.g., 00 for standard"
              value={formValues.subUsageCode}
              onChange={(e) => handleInputChange('subUsageCode', e.target.value)}
              style={{ borderColor: 'rgb(236, 240, 241)' }}
            />
          </div>
        </div>

        {/* Assessment Filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Min Assessed Value:</label>
            <input
              type="number"
              className={inputClassName}
              placeholder="150000"
              value={formValues.minAssessedValue}
              onChange={(e) => handleInputChange('minAssessedValue', e.target.value)}
              style={{ borderColor: 'rgb(236, 240, 241)' }}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Max Assessed Value:</label>
            <input
              type="number"
              className={inputClassName}
              placeholder="750000"
              value={formValues.maxAssessedValue}
              onChange={(e) => handleInputChange('maxAssessedValue', e.target.value)}
              style={{ borderColor: 'rgb(236, 240, 241)' }}
            />
          </div>
        </div>

        {/* Boolean Filters */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Tax Exempt:</label>
            <select
              className={inputClassName}
              value={formValues.taxExempt}
              onChange={(e) => handleInputChange('taxExempt', e.target.value === 'true')}
              style={{ borderColor: 'rgb(236, 240, 241)' }}
            >
              <option value="">Any</option>
              <option value="true">Yes</option>
              <option value="false">No</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Has Pool:</label>
            <select
              className={inputClassName}
              value={formValues.hasPool}
              onChange={(e) => handleInputChange('hasPool', e.target.value === 'true')}
              style={{ borderColor: 'rgb(236, 240, 241)' }}
            >
              <option value="">Any</option>
              <option value="true">Yes</option>
              <option value="false">No</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Waterfront:</label>
            <select
              className={inputClassName}
              value={formValues.waterfront}
              onChange={(e) => handleInputChange('waterfront', e.target.value === 'true')}
              style={{ borderColor: 'rgb(236, 240, 241)' }}
            >
              <option value="">Any</option>
              <option value="true">Yes</option>
              <option value="false">No</option>
            </select>
          </div>
        </div>

        {/* Sales History Filter */}
        <div>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={formValues.recentlySold === 'true'}
              onChange={(e) => handleInputChange('recentlySold', e.target.checked)}
              className="rounded border-gray-300"
            />
            <span className="text-sm font-medium">Recently Sold (within 1 year)</span>
          </label>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4">
          <button
            type="submit"
            disabled={isLoading}
            className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-medium py-3 px-6 rounded-lg transition-colors"
          >
            {isLoading ? 'Searching...' : 'Search Properties'}
          </button>
          <button
            type="button"
            onClick={handleReset}
            className="px-6 py-3 border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium rounded-lg transition-colors"
          >
            Reset Filters
          </button>
        </div>
      </form>

      {/* Results Summary */}
      {metadata && (
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <span className="text-sm text-gray-600">
                Found {metadata.totalCount.toLocaleString()} properties
              </span>
              {metadata.executionTimeSeconds && (
                <span className="text-sm text-gray-500 ml-2">
                  ({metadata.executionTimeSeconds.toFixed(3)}s)
                </span>
              )}
            </div>
            {Object.keys(metadata.filtersApplied || {}).length > 0 && (
              <div className="text-sm text-gray-600">
                {Object.keys(metadata.filtersApplied).length} filters applied
              </div>
            )}
          </div>
        </div>
      )}

      {/* Error Display */}
      {isError && error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg">
          <strong>Search Error:</strong> {error}
        </div>
      )}

      {/* Results Preview */}
      {results.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-lg font-semibold">Search Results Preview</h3>
          <div className="grid gap-4">
            {results.slice(0, 3).map((property, index) => (
              <div key={property.parcelId || index} className="border border-gray-200 p-4 rounded-lg">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-medium">{property.fullAddress}</h4>
                    <p className="text-sm text-gray-600">{property.ownerName}</p>
                    <p className="text-sm text-gray-500">
                      {property.propertyUseDescription} • {property.yearBuilt} • {property.buildingSqft?.toLocaleString()} sq ft
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-semibold text-green-600">
                      ${property.justValue?.toLocaleString()}
                    </div>
                    {property.pricePerSqft && (
                      <div className="text-sm text-gray-500">
                        ${property.pricePerSqft}/sq ft
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
            {results.length > 3 && (
              <div className="text-center py-2">
                <span className="text-sm text-gray-500">
                  + {results.length - 3} more properties
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AdvancedPropertyFilters;