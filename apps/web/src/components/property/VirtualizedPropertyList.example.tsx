/**
 * VirtualizedPropertyList - Usage Examples
 *
 * This file demonstrates how to use the VirtualizedPropertyList component
 * with @tanstack/react-virtual for high-performance property rendering.
 */

import React, { useState } from 'react';
import { VirtualizedPropertyList } from './VirtualizedPropertyList';

// Example 1: Basic Grid View
export function BasicGridExample() {
  const [properties] = useState([
    {
      parcel_id: '12-34-56-78',
      phy_addr1: '123 Main St',
      phy_city: 'Miami',
      phy_zipcd: '33101',
      owner_name: 'John Doe',
      jv: 350000,
      tot_lvg_area: 2000,
      lnd_sqfoot: 5000,
      act_yr_blt: 2010,
    },
    // ... more properties
  ]);

  const handlePropertyClick = (property: any) => {
    console.log('Property clicked:', property);
  };

  return (
    <VirtualizedPropertyList
      properties={properties}
      onPropertyClick={handlePropertyClick}
      viewMode="grid"
      height={600}
    />
  );
}

// Example 2: List View with Selection
export function ListViewWithSelectionExample() {
  const [properties] = useState([
    // ... your properties
  ]);
  const [selectedProperties, setSelectedProperties] = useState<Set<string>>(new Set());

  const handlePropertyClick = (property: any) => {
    console.log('Property clicked:', property);
  };

  const handleToggleSelection = (parcelId: string) => {
    setSelectedProperties(prev => {
      const newSet = new Set(prev);
      if (newSet.has(parcelId)) {
        newSet.delete(parcelId);
      } else {
        newSet.add(parcelId);
      }
      return newSet;
    });
  };

  return (
    <VirtualizedPropertyList
      properties={properties}
      onPropertyClick={handlePropertyClick}
      viewMode="list"
      height={800}
      selectedProperties={selectedProperties}
      onToggleSelection={handleToggleSelection}
    />
  );
}

// Example 3: Infinite Loading
export function InfiniteLoadingExample() {
  const [properties, setProperties] = useState([
    // Initial properties
  ]);
  const [hasNextPage, setHasNextPage] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  const loadNextPage = async () => {
    if (isLoading) return;

    setIsLoading(true);
    try {
      // Fetch more properties from API
      const response = await fetch('/api/properties?page=2');
      const newProperties = await response.json();

      setProperties(prev => [...prev, ...newProperties]);
      setHasNextPage(newProperties.length > 0);
    } catch (error) {
      console.error('Failed to load more properties:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <VirtualizedPropertyList
      properties={properties}
      hasNextPage={hasNextPage}
      isNextPageLoading={isLoading}
      loadNextPage={loadNextPage}
      onPropertyClick={(property) => console.log(property)}
      viewMode="grid"
      height={600}
    />
  );
}

// Example 4: Full-Featured Implementation
export function FullFeaturedExample() {
  const [properties, setProperties] = useState([]);
  const [selectedProperties, setSelectedProperties] = useState<Set<string>>(new Set());
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [hasNextPage, setHasNextPage] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  const handlePropertyClick = (property: any) => {
    // Open property detail modal or navigate to detail page
    console.log('Opening property:', property.parcel_id);
  };

  const handleToggleSelection = (parcelId: string) => {
    setSelectedProperties(prev => {
      const newSet = new Set(prev);
      if (newSet.has(parcelId)) {
        newSet.delete(parcelId);
      } else {
        newSet.add(parcelId);
      }
      return newSet;
    });
  };

  const loadNextPage = async () => {
    if (isLoading) return;
    setIsLoading(true);

    try {
      // Implement your pagination logic
      const newProperties = await fetchMoreProperties();
      setProperties(prev => [...prev, ...newProperties]);
      setHasNextPage(newProperties.length > 0);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      {/* View Mode Toggle */}
      <div className="mb-4 flex gap-2">
        <button
          onClick={() => setViewMode('grid')}
          className={viewMode === 'grid' ? 'active' : ''}
        >
          Grid View
        </button>
        <button
          onClick={() => setViewMode('list')}
          className={viewMode === 'list' ? 'active' : ''}
        >
          List View
        </button>
      </div>

      {/* Selected Count */}
      {selectedProperties.size > 0 && (
        <div className="mb-4">
          {selectedProperties.size} properties selected
        </div>
      )}

      {/* Virtualized List */}
      <VirtualizedPropertyList
        properties={properties}
        hasNextPage={hasNextPage}
        isNextPageLoading={isLoading}
        loadNextPage={loadNextPage}
        onPropertyClick={handlePropertyClick}
        viewMode={viewMode}
        height={800}
        selectedProperties={selectedProperties}
        onToggleSelection={handleToggleSelection}
      />
    </div>
  );
}

// Helper function (mock)
async function fetchMoreProperties() {
  // Replace with actual API call
  return [];
}
