/**
 * Infinite Scroll Hook for Property Search
 * Phase 3: Auto-loads more results as user scrolls
 */

import { useEffect, useRef, useCallback } from 'react';

export interface UseInfiniteScrollOptions {
  onLoadMore: () => void;
  hasMore: boolean;
  isLoading: boolean;
  threshold?: number; // Distance from bottom (in pixels) to trigger load
  rootMargin?: string; // Intersection Observer root margin
}

/**
 * Custom hook for infinite scrolling
 * Automatically triggers onLoadMore when user scrolls near the bottom
 *
 * @param options Configuration options for infinite scroll
 * @returns Object with trigger element ref
 *
 * @example
 * ```tsx
 * const { triggerRef } = useInfiniteScroll({
 *   onLoadMore: () => loadNextPage(),
 *   hasMore: hasMoreResults,
 *   isLoading: loading
 * });
 *
 * return (
 *   <>
 *     {items.map(item => <Item key={item.id} {...item} />)}
 *     <div ref={triggerRef} />
 *   </>
 * );
 * ```
 */
export function useInfiniteScroll({
  onLoadMore,
  hasMore,
  isLoading,
  threshold = 300,
  rootMargin = '300px'
}: UseInfiniteScrollOptions) {
  const triggerRef = useRef<HTMLDivElement>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);

  const handleIntersection = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      const [entry] = entries;

      if (entry.isIntersecting && hasMore && !isLoading) {
        onLoadMore();
      }
    },
    [hasMore, isLoading, onLoadMore]
  );

  useEffect(() => {
    // Create Intersection Observer
    const options = {
      root: null, // viewport
      rootMargin,
      threshold: 0.1
    };

    observerRef.current = new IntersectionObserver(handleIntersection, options);

    // Observe the trigger element
    const currentTrigger = triggerRef.current;
    if (currentTrigger) {
      observerRef.current.observe(currentTrigger);
    }

    // Cleanup
    return () => {
      if (observerRef.current && currentTrigger) {
        observerRef.current.unobserve(currentTrigger);
      }
    };
  }, [handleIntersection, rootMargin]);

  return { triggerRef };
}

/**
 * Alternative: Distance-based infinite scroll
 * Triggers when user scrolls within threshold pixels of bottom
 */
export function useScrollDistance({
  onLoadMore,
  hasMore,
  isLoading,
  threshold = 300
}: Omit<UseInfiniteScrollOptions, 'rootMargin'>) {
  const loadingRef = useRef(false);

  const handleScroll = useCallback(() => {
    if (loadingRef.current || isLoading || !hasMore) return;

    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const scrollHeight = document.documentElement.scrollHeight;
    const clientHeight = document.documentElement.clientHeight;
    const distanceFromBottom = scrollHeight - (scrollTop + clientHeight);

    if (distanceFromBottom < threshold) {
      loadingRef.current = true;
      onLoadMore();

      // Reset after a delay to prevent rapid firing
      setTimeout(() => {
        loadingRef.current = false;
      }, 1000);
    }
  }, [onLoadMore, hasMore, isLoading, threshold]);

  useEffect(() => {
    window.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, [handleScroll]);
}

/**
 * Hook for property-specific infinite scroll
 * Combines infinite scroll with property search logic
 */
export function useInfinitePropertyScroll(
  currentCount: number,
  totalCount: number,
  isLoading: boolean,
  onLoadMore: () => void
) {
  const hasMore = currentCount < totalCount;

  const { triggerRef } = useInfiniteScroll({
    onLoadMore,
    hasMore,
    isLoading,
    threshold: 500, // Trigger earlier for smoother UX
    rootMargin: '500px' // Start loading before user reaches bottom
  });

  return {
    triggerRef,
    hasMore,
    percentLoaded: totalCount > 0 ? Math.round((currentCount / totalCount) * 100) : 0,
    remainingCount: totalCount - currentCount
  };
}
