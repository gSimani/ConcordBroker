import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { usePropertyBatch } from '@/hooks/usePropertyBatch';
import { debounce } from '@/lib/utils';

export function PropertySearchOptimized() {
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    city: '',
    minPrice: null,
    maxPrice: null,
    propertyType: ''
  });

  // Debounced filters to reduce API calls
  const debouncedFilters = useMemo(() => {
    const handler = debounce((newFilters: any) => {
      setFilters(newFilters);
    }, 300);
    
    return handler;
  }, []);

  const {
    properties,
    loading,
    hasMore,
    totalCount,
    loadMore,
    reset
  } = usePropertyBatch({
    filters: {
      ...filters,
      ...(searchTerm ? { owner_name: \`%\${searchTerm}%\` } : {})
    },
    pageSize: 50,
    orderBy: 'assessed_value',
    ascending: false
  });

  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchTerm(value);
    
    debouncedFilters({
      ...filters,
      owner_name: value ? \`%\${value}%\` : null
    });
  }, [filters, debouncedFilters]);

  const handleFilterChange = useCallback((key: string, value: any) => {
    const newFilters = { ...filters, [key]: value };
    debouncedFilters(newFilters);
  }, [filters, debouncedFilters]);

  // Virtual scrolling for better performance with large lists
  const visibleProperties = useMemo(() => {
    // Implement virtual scrolling logic here
    return properties;
  }, [properties]);

  return (
    <div className="property-search-optimized">
      <div className="search-header">
        <input
          type="text"
          placeholder="Search by owner name, address, or parcel ID..."
          value={searchTerm}
          onChange={handleSearchChange}
          className="search-input"
        />
        
        <div className="filters">
          <select 
            onChange={(e) => handleFilterChange('city', e.target.value)}
            value={filters.city}
          >
            <option value="">All Cities</option>
            <option value="Fort Lauderdale">Fort Lauderdale</option>
            <option value="Hollywood">Hollywood</option>
            <option value="Pembroke Pines">Pembroke Pines</option>
          </select>
          
          <input
            type="number"
            placeholder="Min Price"
            onChange={(e) => handleFilterChange('minPrice', e.target.value ? parseInt(e.target.value) : null)}
          />
          
          <input
            type="number"
            placeholder="Max Price"
            onChange={(e) => handleFilterChange('maxPrice', e.target.value ? parseInt(e.target.value) : null)}
          />
        </div>
      </div>

      <div className="results-summary">
        Found {totalCount.toLocaleString()} properties
      </div>

      <div className="property-list">
        {visibleProperties.map((property) => (
          <PropertyCard key={property.parcel_id} property={property} />
        ))}
      </div>

      {hasMore && (
        <button 
          onClick={loadMore} 
          disabled={loading}
          className="load-more-btn"
        >
          {loading ? 'Loading...' : 'Load More'}
        </button>
      )}
    </div>
  );
}

function PropertyCard({ property }: { property: any }) {
  return (
    <div className="property-card">
      <h3>{property.owner_name}</h3>
      <p>{property.address}, {property.city}, {property.state} {property.zip_code}</p>
      <p>Value: ${property.assessed_value?.toLocaleString()}</p>
    </div>
  );
}