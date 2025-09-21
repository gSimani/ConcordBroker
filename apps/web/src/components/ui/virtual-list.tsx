/**
 * High-Performance Virtual List Component
 * Optimized for large datasets with smooth scrolling and minimal re-renders
 */

import React, { useState, useEffect, useRef, useCallback, useMemo, memo } from 'react';
import { debounce } from 'lodash';

interface VirtualListProps<T> {
  items: T[];
  itemHeight: number | ((index: number, item: T) => number);
  containerHeight: number;
  renderItem: (item: T, index: number, style: React.CSSProperties) => React.ReactNode;
  overscan?: number; // Number of items to render outside visible area
  className?: string;
  onScroll?: (scrollTop: number) => void;
  scrollToIndex?: number;
  estimatedItemSize?: number; // For dynamic height lists
  getItemKey?: (item: T, index: number) => string | number;
}

interface VirtualizedRange {
  startIndex: number;
  endIndex: number;
  totalHeight: number;
  offsetY: number;
}

interface ItemMetrics {
  offset: number;
  size: number;
}

function useVirtualization<T>({
  items,
  itemHeight,
  containerHeight,
  overscan = 5,
  scrollToIndex,
  estimatedItemSize = 50,
}: {
  items: T[];
  itemHeight: number | ((index: number, item: T) => number);
  containerHeight: number;
  overscan?: number;
  scrollToIndex?: number;
  estimatedItemSize?: number;
}) {
  const [scrollTop, setScrollTop] = useState(0);
  const [isScrolling, setIsScrolling] = useState(false);

  // Cache for measured item sizes (for dynamic heights)
  const itemMetrics = useRef<Map<number, ItemMetrics>>(new Map());
  const measuredCache = useRef<Map<number, number>>(new Map());

  // Calculate item size
  const getItemSize = useCallback((index: number): number => {
    if (typeof itemHeight === 'number') {
      return itemHeight;
    }

    // Check cache first
    const cached = measuredCache.current.get(index);
    if (cached !== undefined) {
      return cached;
    }

    // Use estimated size if not measured
    if (index < items.length) {
      const estimated = itemHeight(index, items[index]);
      measuredCache.current.set(index, estimated);
      return estimated;
    }

    return estimatedItemSize;
  }, [itemHeight, items, estimatedItemSize]);

  // Calculate total height and item offsets
  const { totalHeight, itemOffsets } = useMemo(() => {
    let offset = 0;
    const offsets: number[] = [];

    for (let i = 0; i < items.length; i++) {
      offsets[i] = offset;
      offset += getItemSize(i);
    }

    return {
      totalHeight: offset,
      itemOffsets: offsets,
    };
  }, [items.length, getItemSize]);

  // Binary search to find start index
  const getStartIndex = useCallback((scrollTop: number): number => {
    let low = 0;
    let high = itemOffsets.length - 1;

    while (low <= high) {
      const mid = Math.floor((low + high) / 2);
      const offset = itemOffsets[mid];

      if (offset === scrollTop) {
        return mid;
      } else if (offset < scrollTop) {
        low = mid + 1;
      } else {
        high = mid - 1;
      }
    }

    return Math.max(0, high);
  }, [itemOffsets]);

  // Calculate visible range
  const range = useMemo((): VirtualizedRange => {
    const startIndex = getStartIndex(scrollTop);
    let endIndex = startIndex;
    let height = 0;

    // Find end index
    for (let i = startIndex; i < items.length && height < containerHeight; i++) {
      height += getItemSize(i);
      endIndex = i;
    }

    // Apply overscan
    const overscanStart = Math.max(0, startIndex - overscan);
    const overscanEnd = Math.min(items.length - 1, endIndex + overscan);

    return {
      startIndex: overscanStart,
      endIndex: overscanEnd,
      totalHeight,
      offsetY: itemOffsets[overscanStart] || 0,
    };
  }, [scrollTop, containerHeight, getStartIndex, getItemSize, items.length, overscan, totalHeight, itemOffsets]);

  // Handle scroll to index
  useEffect(() => {
    if (scrollToIndex !== undefined && scrollToIndex >= 0 && scrollToIndex < items.length) {
      const targetOffset = itemOffsets[scrollToIndex];
      setScrollTop(targetOffset);
    }
  }, [scrollToIndex, itemOffsets, items.length]);

  // Debounced scroll end detection
  const scrollEndTimer = useRef<NodeJS.Timeout>();
  const handleScrollEnd = useCallback(() => {
    setIsScrolling(false);
  }, []);

  const debouncedScrollEnd = useMemo(
    () => debounce(handleScrollEnd, 150),
    [handleScrollEnd]
  );

  const handleScroll = useCallback((newScrollTop: number) => {
    setScrollTop(newScrollTop);
    setIsScrolling(true);

    // Clear previous timer
    if (scrollEndTimer.current) {
      clearTimeout(scrollEndTimer.current);
    }

    // Set new timer
    scrollEndTimer.current = setTimeout(() => {
      setIsScrolling(false);
    }, 150);

    debouncedScrollEnd();
  }, [debouncedScrollEnd]);

  // Update item size cache
  const measureItem = useCallback((index: number, size: number) => {
    const currentSize = measuredCache.current.get(index);
    if (currentSize !== size) {
      measuredCache.current.set(index, size);
      // Trigger re-calculation on next render
      setScrollTop(prev => prev);
    }
  }, []);

  return {
    range,
    totalHeight,
    isScrolling,
    handleScroll,
    measureItem,
  };
}

// Individual list item component with size measurement
const VirtualListItem = memo(function VirtualListItem<T>({
  item,
  index,
  style,
  renderItem,
  measureItem,
}: {
  item: T;
  index: number;
  style: React.CSSProperties;
  renderItem: (item: T, index: number, style: React.CSSProperties) => React.ReactNode;
  measureItem: (index: number, size: number) => void;
}) {
  const itemRef = useRef<HTMLDivElement>(null);

  // Measure item size after render
  useEffect(() => {
    if (itemRef.current) {
      const height = itemRef.current.offsetHeight;
      measureItem(index, height);
    }
  }, [index, measureItem]);

  return (
    <div ref={itemRef} style={style}>
      {renderItem(item, index, style)}
    </div>
  );
});

export const VirtualList = memo(function VirtualList<T>({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  overscan = 5,
  className = '',
  onScroll,
  scrollToIndex,
  estimatedItemSize = 50,
  getItemKey,
}: VirtualListProps<T>) {
  const containerRef = useRef<HTMLDivElement>(null);
  const scrollElementRef = useRef<HTMLDivElement>(null);

  const {
    range,
    totalHeight,
    isScrolling,
    handleScroll,
    measureItem,
  } = useVirtualization({
    items,
    itemHeight,
    containerHeight,
    overscan,
    scrollToIndex,
    estimatedItemSize,
  });

  // Handle scroll events
  const onScrollHandler = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const scrollTop = e.currentTarget.scrollTop;
    handleScroll(scrollTop);
    onScroll?.(scrollTop);
  }, [handleScroll, onScroll]);

  // Generate visible items
  const visibleItems = useMemo(() => {
    const items_to_render = [];

    for (let i = range.startIndex; i <= range.endIndex; i++) {
      if (i >= items.length) break;

      const item = items[i];
      const key = getItemKey ? getItemKey(item, i) : i;

      // Calculate item offset from start of visible area
      const itemOffset = (typeof itemHeight === 'number')
        ? i * itemHeight
        : range.offsetY + (i - range.startIndex) * estimatedItemSize;

      const style: React.CSSProperties = {
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        transform: `translateY(${itemOffset}px)`,
      };

      items_to_render.push(
        <VirtualListItem
          key={key}
          item={item}
          index={i}
          style={style}
          renderItem={renderItem}
          measureItem={measureItem}
        />
      );
    }

    return items_to_render;
  }, [range, items, itemHeight, estimatedItemSize, renderItem, getItemKey, measureItem]);

  // Scroll to index programmatically
  const scrollToItem = useCallback((index: number, align: 'start' | 'center' | 'end' = 'start') => {
    if (!scrollElementRef.current || index < 0 || index >= items.length) return;

    const itemOffset = (typeof itemHeight === 'number')
      ? index * itemHeight
      : estimatedItemSize * index;

    let scrollTop = itemOffset;

    if (align === 'center') {
      scrollTop = itemOffset - containerHeight / 2;
    } else if (align === 'end') {
      const itemSize = typeof itemHeight === 'number' ? itemHeight : estimatedItemSize;
      scrollTop = itemOffset - containerHeight + itemSize;
    }

    scrollTop = Math.max(0, Math.min(scrollTop, totalHeight - containerHeight));

    scrollElementRef.current.scrollTop = scrollTop;
  }, [items.length, itemHeight, estimatedItemSize, containerHeight, totalHeight]);

  // Performance optimization: Use transform instead of top for better performance
  const scrollContainerStyle: React.CSSProperties = {
    height: containerHeight,
    overflow: 'auto',
    position: 'relative',
    ...(!isScrolling && { scrollBehavior: 'smooth' }),
  };

  const innerStyle: React.CSSProperties = {
    height: totalHeight,
    position: 'relative',
  };

  return (
    <div
      ref={containerRef}
      className={`virtual-list ${className}`}
      style={scrollContainerStyle}
    >
      <div
        ref={scrollElementRef}
        style={{
          height: '100%',
          overflow: 'auto',
          willChange: 'scroll-position',
        }}
        onScroll={onScrollHandler}
      >
        <div style={innerStyle}>
          {visibleItems}
        </div>
      </div>
    </div>
  );
});

// Hook for managing virtual list state
export function useVirtualList<T>(items: T[], options: {
  itemHeight: number;
  containerHeight: number;
  overscan?: number;
}) {
  const [scrollToIndex, setScrollToIndex] = useState<number>();

  const scrollToItem = useCallback((index: number) => {
    setScrollToIndex(index);
    // Reset after scroll
    setTimeout(() => setScrollToIndex(undefined), 100);
  }, []);

  return {
    scrollToIndex,
    scrollToItem,
  };
}

// Infinite loading virtual list
export const InfiniteVirtualList = memo(function InfiniteVirtualList<T>({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  hasNextPage = false,
  isFetchingNextPage = false,
  fetchNextPage,
  ...props
}: VirtualListProps<T> & {
  hasNextPage?: boolean;
  isFetchingNextPage?: boolean;
  fetchNextPage?: () => void;
}) {
  const [scrollTop, setScrollTop] = useState(0);

  // Load more when near bottom
  useEffect(() => {
    const threshold = 200; // Load more when 200px from bottom
    const totalHeight = typeof itemHeight === 'number'
      ? items.length * itemHeight
      : items.length * (props.estimatedItemSize || 50);

    const bottomDistance = totalHeight - (scrollTop + containerHeight);

    if (bottomDistance < threshold && hasNextPage && !isFetchingNextPage && fetchNextPage) {
      fetchNextPage();
    }
  }, [scrollTop, containerHeight, items.length, itemHeight, hasNextPage, isFetchingNextPage, fetchNextPage, props.estimatedItemSize]);

  const handleScroll = useCallback((newScrollTop: number) => {
    setScrollTop(newScrollTop);
    props.onScroll?.(newScrollTop);
  }, [props]);

  return (
    <VirtualList
      {...props}
      items={items}
      itemHeight={itemHeight}
      containerHeight={containerHeight}
      renderItem={renderItem}
      onScroll={handleScroll}
    />
  );
});

export default VirtualList;