import React, { useCallback, useEffect, useRef, useState } from 'react';
import { VariableSizeGrid as Grid } from 'react-window';
import InfiniteLoader from 'react-window-infinite-loader';
import AutoSizer from 'react-virtualized-auto-sizer';
import { useInfiniteQuery } from '@tanstack/react-query';
import { EnhancedMiniPropertyCard } from './EnhancedMiniPropertyCard';
import { Loader2 } from 'lucide-react';

interface VirtualPropertyGridProps {
  filters?: any;
  onPropertyClick?: (property: any) => void;
  onCompare?: (properties: any[]) => void;
}

/**
 * Virtual scrolling grid for 7.31M properties
 * Renders only visible properties for optimal performance
 */
export const VirtualPropertyGrid: React.FC<VirtualPropertyGridProps> = ({
  filters = {},
  onPropertyClick,
  onCompare
}) => {
  const [selectedForCompare, setSelectedForCompare] = useState<Set<string>>(new Set());
  const gridRef = useRef<any>(null);
  const [columnCount, setColumnCount] = useState(4);

  // Constants for grid layout
  const CARD_WIDTH = 320;
  const CARD_HEIGHT = 420;
  const GAP = 16;
  const BATCH_SIZE = 100; // Fetch 100 properties at a time

  // Fetch properties with infinite scroll
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    status,
    error
  } = useInfiniteQuery({
    queryKey: ['properties-infinite', filters],
    queryFn: async ({ pageParam = 0 }) => {
      const response = await fetch(
        `http://localhost:8000/api/properties/search?` +
        new URLSearchParams({
          ...filters,
          limit: String(BATCH_SIZE),
          offset: String(pageParam * BATCH_SIZE)
        })
      );

      if (!response.ok) throw new Error('Failed to fetch properties');
      const result = await response.json();

      return {
        properties: result.properties || result.data || [],
        total: result.total || 7312041,
        nextOffset: (pageParam + 1) * BATCH_SIZE
      };
    },
    getNextPageParam: (lastPage, pages) => {
      const loadedCount = pages.reduce((acc, page) => acc + page.properties.length, 0);
      if (loadedCount < lastPage.total) {
        return pages.length;
      }
      return undefined;
    },
    staleTime: 1000 * 60 * 5, // Cache for 5 minutes
    cacheTime: 1000 * 60 * 10, // Keep in cache for 10 minutes
  });

  // Flatten all pages into single array
  const allProperties = data?.pages.flatMap(page => page.properties) || [];
  const totalProperties = data?.pages[0]?.total || 7312041;

  // Calculate total rows needed
  const rowCount = Math.ceil(totalProperties / columnCount);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth - 32; // Account for padding
      const newColumnCount = Math.max(1, Math.floor(width / (CARD_WIDTH + GAP)));
      setColumnCount(newColumnCount);
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Get item data for specific position
  const getItemData = useCallback((rowIndex: number, columnIndex: number) => {
    const index = rowIndex * columnCount + columnIndex;
    if (index >= totalProperties) return null;

    // Check if we need to load more
    if (index >= allProperties.length - 20 && hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }

    return allProperties[index] || null;
  }, [allProperties, columnCount, totalProperties, hasNextPage, fetchNextPage, isFetchingNextPage]);

  // Check if item is loaded
  const isItemLoaded = useCallback((index: number) => {
    return index < allProperties.length;
  }, [allProperties.length]);

  // Load more items
  const loadMoreItems = useCallback(() => {
    if (!isFetchingNextPage && hasNextPage) {
      return fetchNextPage();
    }
    return Promise.resolve();
  }, [fetchNextPage, hasNextPage, isFetchingNextPage]);

  // Cell renderer
  const Cell = ({ columnIndex, rowIndex, style }: any) => {
    const property = getItemData(rowIndex, columnIndex);

    if (!property) {
      // Show loading placeholder
      if (rowIndex * columnCount + columnIndex < totalProperties) {
        return (
          <div style={style} className="p-2">
            <div className="bg-gray-100 rounded-lg h-full animate-pulse flex items-center justify-center">
              <Loader2 className="w-8 h-8 text-gray-400 animate-spin" />
            </div>
          </div>
        );
      }
      return null;
    }

    return (
      <div style={style} className="p-2">
        <EnhancedMiniPropertyCard
          property={property}
          variant="grid"
          onClick={onPropertyClick}
          onCompare={(prop) => {
            const newSelected = new Set(selectedForCompare);
            if (newSelected.has(prop.parcel_id)) {
              newSelected.delete(prop.parcel_id);
            } else {
              newSelected.add(prop.parcel_id);
            }
            setSelectedForCompare(newSelected);

            // Trigger comparison when 2+ properties selected
            if (newSelected.size >= 2) {
              const compareProperties = allProperties.filter(p =>
                newSelected.has(p.parcel_id)
              );
              onCompare?.(compareProperties);
            }
          }}
        />
      </div>
    );
  };

  // Handle scroll to load more
  const handleScroll = useCallback(({ scrollTop, scrollHeight, clientHeight }: any) => {
    // Load more when scrolled near bottom
    if (scrollHeight - scrollTop - clientHeight < 1000) {
      loadMoreItems();
    }
  }, [loadMoreItems]);

  if (status === 'loading') {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading properties...</p>
        </div>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center text-red-500">
          <p className="text-xl font-semibold mb-2">Error loading properties</p>
          <p className="text-gray-600">{(error as Error)?.message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full">
      {/* Header with count and controls */}
      <div className="sticky top-0 z-10 bg-white border-b px-4 py-3 flex justify-between items-center">
        <div>
          <h2 className="text-lg font-semibold">
            {totalProperties.toLocaleString()} Properties Found
          </h2>
          <p className="text-sm text-gray-500">
            Showing {allProperties.length.toLocaleString()} of {totalProperties.toLocaleString()}
          </p>
        </div>

        {selectedForCompare.size > 0 && (
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">
              {selectedForCompare.size} selected for comparison
            </span>
            <button
              onClick={() => setSelectedForCompare(new Set())}
              className="text-sm text-blue-500 hover:text-blue-700"
            >
              Clear selection
            </button>
          </div>
        )}
      </div>

      {/* Virtual grid */}
      <div style={{ height: 'calc(100vh - 200px)' }}>
        <AutoSizer>
          {({ height, width }) => (
            <InfiniteLoader
              isItemLoaded={isItemLoaded}
              itemCount={totalProperties}
              loadMoreItems={loadMoreItems}
              minimumBatchSize={BATCH_SIZE}
              threshold={10}
            >
              {({ onItemsRendered, ref }) => (
                <Grid
                  ref={(grid) => {
                    ref(grid);
                    gridRef.current = grid;
                  }}
                  columnCount={columnCount}
                  columnWidth={() => CARD_WIDTH + GAP}
                  height={height}
                  rowCount={rowCount}
                  rowHeight={() => CARD_HEIGHT + GAP}
                  width={width}
                  onScroll={handleScroll}
                  overscanRowCount={2}
                  overscanColumnCount={1}
                >
                  {Cell}
                </Grid>
              )}
            </InfiniteLoader>
          )}
        </AutoSizer>
      </div>

      {/* Loading indicator */}
      {isFetchingNextPage && (
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-white rounded-full shadow-lg px-4 py-2 flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
          <span className="text-sm">Loading more properties...</span>
        </div>
      )}

      {/* Performance stats (development only) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="fixed bottom-4 right-4 bg-black/80 text-white text-xs rounded p-2">
          <div>Loaded: {allProperties.length.toLocaleString()}</div>
          <div>Total: {totalProperties.toLocaleString()}</div>
          <div>Grid: {columnCount} cols × {rowCount} rows</div>
        </div>
      )}
    </div>
  );
};

export default VirtualPropertyGrid;