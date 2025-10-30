import { memo, useMemo, useRef } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { MiniPropertyCard } from './MiniPropertyCard';

interface PropertyData {
  parcel_id: string;
  [key: string]: any;
}

interface VirtualizedPropertyListProps {
  properties: PropertyData[];
  hasNextPage?: boolean;
  isNextPageLoading?: boolean;
  loadNextPage?: () => Promise<void>;
  onPropertyClick: (property: PropertyData) => void;
  viewMode?: 'grid' | 'list';
  height?: number;
  selectedProperties?: Set<string>;
  onToggleSelection?: (parcelId: string) => void;
  batchSalesData?: Record<string, any>;
  isBatchLoading?: boolean;
}

/**
 * VirtualizedPropertyList - High-performance property list using @tanstack/react-virtual
 *
 * Features:
 * - Virtual scrolling for thousands of properties
 * - Grid and list view modes
 * - Infinite loading support
 * - Overscan for smooth scrolling
 * - Dynamic row heights
 */
export const VirtualizedPropertyList = memo<VirtualizedPropertyListProps>(({
  properties,
  hasNextPage = false,
  isNextPageLoading = false,
  loadNextPage,
  onPropertyClick,
  viewMode = 'grid',
  height = 600,
  selectedProperties,
  onToggleSelection,
  batchSalesData,
  isBatchLoading = false
}) => {
  const parentRef = useRef<HTMLDivElement>(null);

  // Calculate items per row for grid view
  const itemsPerRow = useMemo(() => {
    if (viewMode === 'list') return 1;

    // Grid view: calculate based on container width
    // Assuming ~350px per card + 16px gap
    const containerWidth = parentRef.current?.clientWidth || 1200;
    const cardWidth = 350;
    const gap = 16;
    const padding = 32;

    return Math.max(1, Math.floor((containerWidth - padding) / (cardWidth + gap)));
  }, [viewMode]);

  // Calculate total number of rows for virtualization
  const rowCount = useMemo(() => {
    if (viewMode === 'list') {
      // List view: one item per row
      return hasNextPage ? properties.length + 1 : properties.length;
    }

    // Grid view: multiple items per row
    const rows = Math.ceil(properties.length / itemsPerRow);
    return hasNextPage ? rows + 1 : rows;
  }, [properties.length, hasNextPage, viewMode, itemsPerRow]);

  // Initialize virtualizer with proper configuration
  const rowVirtualizer = useVirtualizer({
    count: rowCount,
    getScrollElement: () => parentRef.current,
    estimateSize: () => (viewMode === 'grid' ? 350 : 150), // Estimated row height
    overscan: 5, // Render 5 extra items outside viewport for smooth scrolling
    // Enable infinite loading
    onChange: (instance) => {
      if (!loadNextPage || isNextPageLoading || !hasNextPage) return;

      const lastItem = instance.getVirtualItems().slice(-1)[0];
      if (!lastItem) return;

      // Load more when user scrolls near the end
      if (lastItem.index >= rowCount - 1 - 3) {
        loadNextPage();
      }
    },
  });

  const virtualItems = rowVirtualizer.getVirtualItems();
  const totalSize = rowVirtualizer.getTotalSize();

  // Render grid row with multiple items
  const renderGridRow = (virtualRow: typeof virtualItems[0]) => {
    const rowStartIndex = virtualRow.index * itemsPerRow;
    const rowItems = properties.slice(rowStartIndex, rowStartIndex + itemsPerRow);

    if (rowItems.length === 0) {
      // Loading row
      return (
        <div
          key={virtualRow.key}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: `${virtualRow.size}px`,
            transform: `translateY(${virtualRow.start}px)`,
          }}
          className="flex gap-4 px-4"
        >
          <div className="flex-1 animate-pulse bg-gray-200 rounded-lg h-[320px]" />
          <div className="flex-1 animate-pulse bg-gray-200 rounded-lg h-[320px]" />
          <div className="flex-1 animate-pulse bg-gray-200 rounded-lg h-[320px]" />
        </div>
      );
    }

    return (
      <div
        key={virtualRow.key}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: `${virtualRow.size}px`,
          transform: `translateY(${virtualRow.start}px)`,
        }}
        className="flex gap-4 px-4"
      >
        {rowItems.map((property) => (
          <div key={property.parcel_id} className="flex-1">
            <MiniPropertyCard
              parcelId={property.parcel_id}
              data={property}
              onClick={() => onPropertyClick(property)}
              variant="grid"
              isSelected={selectedProperties?.has(property.parcel_id)}
              onToggleSelection={onToggleSelection ? () => onToggleSelection(property.parcel_id) : undefined}
              salesData={batchSalesData?.[property.parcel_id]}
              isBatchLoading={isBatchLoading}
            />
          </div>
        ))}
        {/* Fill empty slots in the last row */}
        {Array.from({ length: itemsPerRow - rowItems.length }).map((_, emptyIndex) => (
          <div key={`empty-${emptyIndex}`} className="flex-1" />
        ))}
      </div>
    );
  };

  // Render list row with single item
  const renderListRow = (virtualRow: typeof virtualItems[0]) => {
    const property = properties[virtualRow.index];

    if (!property) {
      // Loading row
      return (
        <div
          key={virtualRow.key}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: `${virtualRow.size}px`,
            transform: `translateY(${virtualRow.start}px)`,
          }}
          className="px-4 py-2"
        >
          <div className="animate-pulse bg-gray-200 h-[120px] rounded-lg" />
        </div>
      );
    }

    return (
      <div
        key={virtualRow.key}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: `${virtualRow.size}px`,
          transform: `translateY(${virtualRow.start}px)`,
        }}
        className="px-4 py-2"
      >
        <MiniPropertyCard
          parcelId={property.parcel_id}
          data={property}
          onClick={() => onPropertyClick(property)}
          variant="list"
          isSelected={selectedProperties?.has(property.parcel_id)}
          onToggleSelection={onToggleSelection ? () => onToggleSelection(property.parcel_id) : undefined}
          salesData={batchSalesData?.[property.parcel_id]}
          isBatchLoading={isBatchLoading}
        />
      </div>
    );
  };

  // Handle empty state
  if (properties.length === 0 && !isNextPageLoading) {
    return (
      <div
        className="flex items-center justify-center bg-gray-50 rounded-lg border-2 border-dashed border-gray-300"
        style={{ height }}
      >
        <div className="text-center">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No properties found</h3>
          <p className="mt-1 text-sm text-gray-500">Try adjusting your filters or search criteria.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div
        ref={parentRef}
        className="w-full overflow-auto"
        style={{ height }}
      >
        <div
          style={{
            height: `${totalSize}px`,
            width: '100%',
            position: 'relative',
          }}
        >
          {virtualItems.map((virtualRow) =>
            viewMode === 'grid'
              ? renderGridRow(virtualRow)
              : renderListRow(virtualRow)
          )}
        </div>
      </div>

      {/* Loading indicator */}
      {isNextPageLoading && (
        <div className="flex justify-center py-4">
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            <span className="text-sm text-gray-600">Loading more properties...</span>
          </div>
        </div>
      )}
    </div>
  );
});

VirtualizedPropertyList.displayName = 'VirtualizedPropertyList';
