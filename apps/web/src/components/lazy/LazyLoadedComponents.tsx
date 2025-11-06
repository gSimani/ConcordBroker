import { lazy, Suspense } from 'react';
import { Skeleton } from '@/components/ui/skeleton';

// Lazy-loaded heavy components
const PropertyMap = lazy(() =>
  import('@/components/property/PropertyMap').then(module => ({ default: module.PropertyMap }))
);

const TaxDeedSalesTab = lazy(() =>
  import('@/components/property/tabs/TaxDeedSalesTab').then(module => ({ default: module.TaxDeedSalesTab }))
);

const AISearchEnhanced = lazy(() =>
  import('@/components/ai/AISearchEnhanced').then(module => ({ default: module.AISearchEnhanced }))
);

const GraphVisualization = lazy(() =>
  import('@/components/graph/GraphVisualization').then(module => ({ default: module.GraphVisualization }))
);

// Advanced property tabs - these are heavy due to charts and calculations
const AnalysisTab = lazy(() =>
  import('@/components/property/tabs/AnalysisTab').then(module => ({ default: module.AnalysisTab }))
);

const SalesHistoryTab = lazy(() =>
  import('@/components/property/tabs/SalesHistoryTab').then(module => ({ default: module.SalesHistoryTabUpdated }))
);

// Loading skeleton components
const MapLoadingSkeleton = () => (
  <div className="w-full h-96 bg-gray-100 rounded-lg flex items-center justify-center">
    <div className="text-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
      <p className="text-sm text-gray-500">Loading map...</p>
    </div>
  </div>
);

const TabLoadingSkeleton = () => (
  <div className="space-y-4 p-6">
    <Skeleton className="h-4 w-3/4" />
    <Skeleton className="h-4 w-1/2" />
    <Skeleton className="h-32 w-full" />
    <div className="grid grid-cols-2 gap-4">
      <Skeleton className="h-20 w-full" />
      <Skeleton className="h-20 w-full" />
    </div>
  </div>
);

const AISearchLoadingSkeleton = () => (
  <div className="space-y-4 p-6">
    <Skeleton className="h-10 w-full" />
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <Skeleton className="h-24 w-full" />
      <Skeleton className="h-24 w-full" />
      <Skeleton className="h-24 w-full" />
    </div>
  </div>
);

const ChartLoadingSkeleton = () => (
  <div className="space-y-4">
    <Skeleton className="h-6 w-48" />
    <Skeleton className="h-64 w-full" />
    <div className="flex space-x-4">
      <Skeleton className="h-4 w-20" />
      <Skeleton className="h-4 w-20" />
      <Skeleton className="h-4 w-20" />
    </div>
  </div>
);

// Wrapped lazy components with loading states
export const LazyPropertyMap = (props: any) => (
  <Suspense fallback={<MapLoadingSkeleton />}>
    <PropertyMap {...props} />
  </Suspense>
);

export const LazyTaxDeedSalesTab = (props: any) => (
  <Suspense fallback={<TabLoadingSkeleton />}>
    <TaxDeedSalesTab {...props} />
  </Suspense>
);

export const LazyAISearchEnhanced = (props: any) => (
  <Suspense fallback={<AISearchLoadingSkeleton />}>
    <AISearchEnhanced {...props} />
  </Suspense>
);

export const LazyGraphVisualization = (props: any) => (
  <Suspense fallback={<ChartLoadingSkeleton />}>
    <GraphVisualization {...props} />
  </Suspense>
);

export const LazyAnalysisTab = (props: any) => (
  <Suspense fallback={<TabLoadingSkeleton />}>
    <AnalysisTab {...props} />
  </Suspense>
);

export const LazySalesHistoryTab = (props: any) => (
  <Suspense fallback={<TabLoadingSkeleton />}>
    <SalesHistoryTab {...props} />
  </Suspense>
);

// Export individual lazy components for more granular usage
export {
  PropertyMap as LazyPropertyMapComponent,
  TaxDeedSalesTab as LazyTaxDeedSalesTabComponent,
  AISearchEnhanced as LazyAISearchEnhancedComponent,
  GraphVisualization as LazyGraphVisualizationComponent,
  AnalysisTab as LazyAnalysisTabComponent,
  SalesHistoryTab as LazySalesHistoryTabComponent
};