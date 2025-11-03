import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
// Note: Persistence packages may not be available in this version
// import { persistQueryClient } from '@tanstack/react-query-persist-client-core';
// import { createSyncStoragePersister } from '@tanstack/query-sync-storage-persister';

// Advanced performance configuration for ConcordBroker
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Aggressive caching for property data that doesn't change often
      staleTime: 10 * 60 * 1000, // 10 minutes (property data is relatively stable)
      gcTime: 2 * 60 * 60 * 1000, // 2 hours (keep longer for offline support)

      // Network optimization
      retry: (failureCount, error: any) => {
        // Smart retry logic based on error type
        if (error?.status === 404) return false; // Don't retry not found
        if (error?.status >= 400 && error?.status < 500) return false; // Don't retry client errors
        return failureCount < 3; // Retry server errors up to 3 times
      },
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff

      // Performance optimizations
      refetchOnWindowFocus: false, // Prevent unnecessary refetches
      refetchOnReconnect: 'always', // Always refresh on reconnect for fresh data
      refetchOnMount: false, // Simplified: don't refetch on mount (rely on staleTime)

      // Background updates for better UX
      refetchInterval: false, // We'll handle this per query as needed
      refetchIntervalInBackground: false,

      // Error handling
      throwOnError: false, // Handle errors gracefully in components

      // Network mode optimization
      networkMode: 'online', // Only fetch when online by default
    },
    mutations: {
      // Optimistic updates and error handling
      retry: (failureCount, error: any) => {
        if (error?.status >= 400 && error?.status < 500) return false;
        return failureCount < 2;
      },
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
      networkMode: 'online',
      throwOnError: false,
    },
  },
});

// Enhanced persister for offline support (disabled for now)
// const persister = createSyncStoragePersister({
//   storage: window.localStorage,
//   key: 'concordbroker-query-cache',
//   serialize: JSON.stringify,
//   deserialize: JSON.parse,
//   throttleTime: 1000, // Only persist every second to avoid performance issues
// });

// Persist query client for offline functionality (disabled for now)
// persistQueryClient({
//   queryClient,
//   persister,
//   maxAge: 24 * 60 * 60 * 1000, // 24 hours
//   buster: 'v1.2', // Increment this to invalidate old cache
// });

// Performance monitoring
if (process.env.NODE_ENV === 'development') {
  queryClient.getQueryCache().subscribe((event) => {
    if (event?.type === 'updated' && event?.query?.meta?.trackPerformance) {
      const query = event.query;
      // Calculate load time using dataUpdatedAt and fetchedAt timestamps
      const loadTime = query.state.dataUpdatedAt - (query.state.dataUpdatedAt || 0);
      console.log(`Query ${query.queryHash} completed in ${loadTime}ms`);
    }
  });
}

interface QueryProviderProps {
  children: React.ReactNode;
}

export function QueryProvider({ children }: QueryProviderProps) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {/* Only show devtools in development */}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools
          initialIsOpen={false}
          position={"bottom-right" as any}
        />
      )}
    </QueryClientProvider>
  );
}

// Export the client for manual usage if needed
export { queryClient };