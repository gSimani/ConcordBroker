import React, { memo, useCallback, useMemo } from 'react';
import { FixedSizeList as List } from 'react-window';
// @ts-ignore - ESM import issue
import * as InfiniteLoaderModule from 'react-window-infinite-loader';
const InfiniteLoader = InfiniteLoaderModule.default || InfiniteLoaderModule;
import { OptimizedMiniPropertyCard } from './OptimizedMiniPropertyCard';

interface PropertyData {
  parcel_id: string;
  [key: string]: any;
}

interface VirtualizedPropertyListProps {
  properties: PropertyData[];
  hasNextPage: boolean;
  isNextPageLoading: boolean;
  loadNextPage: () => Promise<void>;
  onPropertyClick: (property: PropertyData) => void;
  viewMode?: 'grid' | 'list';
  height?: number;
  width?: number;
  selectedProperties?: Set<string>;
  onToggleSelection?: (parcelId: string) => void;
}

// Grid item component for virtualization
const GridItem = memo<{
  index: number;
  style: React.CSSProperties;
  data: {
    properties: PropertyData[];
    onPropertyClick: (property: PropertyData) => void;
    itemsPerRow: number;
    selectedProperties?: Set<string>;
    onToggleSelection?: (parcelId: string) => void;
  };
}>(({ index, style, data }) => {
  const { properties, onPropertyClick, itemsPerRow, selectedProperties, onToggleSelection } = data;

  const rowStartIndex = index * itemsPerRow;
  const rowItems = properties.slice(rowStartIndex, rowStartIndex + itemsPerRow);

  return (
    <div style={style} className="flex gap-4 px-4">
      {rowItems.map((property, itemIndex) => {
        const actualIndex = rowStartIndex + itemIndex;
        if (actualIndex >= properties.length) return null;

        return (
          <div key={property.parcel_id} className="flex-1">
            <OptimizedMiniPropertyCard
              parcelId={property.parcel_id}
              data={property}
              onClick={() => onPropertyClick(property)}
              variant="grid"
              isSelected={selectedProperties?.has(property.parcel_id)}
              onToggleSelection={onToggleSelection ? () => onToggleSelection(property.parcel_id) : undefined}
            />
          </div>
        );
      })}
      {/* Fill empty slots in the last row */}
      {Array.from({ length: itemsPerRow - rowItems.length }).map((_, emptyIndex) => (
        <div key={`empty-${emptyIndex}`} className="flex-1" />
      ))}
    </div>
  );
});

GridItem.displayName = 'GridItem';

// List item component for virtualization
const ListItem = memo<{
  index: number;
  style: React.CSSProperties;
  data: {
    properties: PropertyData[];
    onPropertyClick: (property: PropertyData) => void;
    selectedProperties?: Set<string>;
    onToggleSelection?: (parcelId: string) => void;
  };
}>(({ index, style, data }) => {
  const { properties, onPropertyClick, selectedProperties, onToggleSelection } = data;
  const property = properties[index];

  if (!property) {
    return (
      <div style={style} className="px-4 py-2">
        <div className="animate-pulse bg-gray-200 h-16 rounded"></div>
      </div>
    );
  }

  return (
    <div style={style} className="px-4 py-1">
      <OptimizedMiniPropertyCard
        parcelId={property.parcel_id}
        data={property}
        onClick={() => onPropertyClick(property)}
        variant="list"
        isSelected={selectedProperties?.has(property.parcel_id)}
        onToggleSelection={onToggleSelection ? () => onToggleSelection(property.parcel_id) : undefined}
      />
    </div>
  );
});

ListItem.displayName = 'ListItem';

const VirtualizedPropertyList = memo<VirtualizedPropertyListProps>(({
  properties,
  hasNextPage,
  isNextPageLoading,
  loadNextPage,
  onPropertyClick,
  viewMode = 'grid',
  height = 600,
  width = '100%',
  selectedProperties,
  onToggleSelection
}) => {
  // Calculate items per row for grid view based on container width
  const itemsPerRow = useMemo(() => {
    if (viewMode === 'list') return 1;

    // Estimate based on card width (~300px) + gaps
    const containerWidth = typeof width === 'number' ? width : 1200; // Default assumption
    const cardWidth = 300;
    const gap = 16;
    const padding = 32;

    return Math.max(1, Math.floor((containerWidth - padding) / (cardWidth + gap)));
  }, [viewMode, width]);

  // Calculate total number of rows/items for virtualization
  const itemCount = useMemo(() => {
    if (viewMode === 'list') {
      return hasNextPage ? properties.length + 1 : properties.length;
    }

    // For grid, calculate number of rows
    const rows = Math.ceil(properties.length / itemsPerRow);
    return hasNextPage ? rows + 1 : rows;
  }, [properties.length, hasNextPage, viewMode, itemsPerRow]);

  // Item height calculation
  const itemHeight = useMemo(() => {
    return viewMode === 'grid' ? 280 : 100; // Approximate heights
  }, [viewMode]);

  // Check if item is loaded
  const isItemLoaded = useCallback((index: number) => {
    if (viewMode === 'list') {
      return !!properties[index];
    }

    // For grid, check if all items in the row are loaded
    const rowStartIndex = index * itemsPerRow;
    return rowStartIndex < properties.length;
  }, [properties.length, viewMode, itemsPerRow]);

  // Memoized item data for better performance
  const itemData = useMemo(() => ({
    properties,
    onPropertyClick,
    itemsPerRow,
    selectedProperties,
    onToggleSelection
  }), [properties, onPropertyClick, itemsPerRow, selectedProperties, onToggleSelection]);

  const ItemComponent = viewMode === 'grid' ? GridItem : ListItem;

  return (
    <div className="w-full">
      <InfiniteLoader
        isItemLoaded={isItemLoaded}
        itemCount={itemCount}
        loadMoreItems={loadNextPage}
      >
        {({ onItemsRendered, ref }) => (
          <List
            ref={ref}
            height={height}
            width={width}
            itemCount={itemCount}
            itemSize={itemHeight}
            itemData={itemData}
            onItemsRendered={onItemsRendered}
            overscanCount={5} // Render 5 extra items outside viewport
          >
            {ItemComponent}
          </List>
        )}
      </InfiniteLoader>

      {/* Loading indicator */}
      {isNextPageLoading && (
        <div className="flex justify-center py-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      )}
    </div>
  );
});

VirtualizedPropertyList.displayName = 'VirtualizedPropertyList';

export { VirtualizedPropertyList };