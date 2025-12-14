/**
 * ConcordBroker UI Component Library
 * ===================================
 *
 * Central export for all UI components in the design system.
 * Import components from this file for consistent usage.
 *
 * Example:
 *   import { PropertyCard, MetricCard, DataTable } from '@/components/ui';
 */

// Core UI Components (shadcn/ui based)
export { Button, buttonVariants, type ButtonProps } from './button';

// Design System Components
export {
  PropertyCard,
  PropertyCardSkeleton,
  type PropertyCardProps,
  type PropertyType,
  type PropertyStatus,
} from './property-card';

export {
  MetricCard,
  MetricCardSkeleton,
  type MetricCardProps,
} from './metric-card';

export {
  CollapsibleSection,
  CollapsibleGroup,
  type CollapsibleSectionProps,
  type CollapsibleGroupProps,
} from './collapsible-section';

// States Components
export {
  // Loading states
  SkeletonCard,
  SkeletonTable,
  SkeletonList,
  LoadingSpinner,
  // Empty states
  EmptyState,
  NoPropertiesFound,
  NoSearchResults,
  NoDataAvailable,
  // Error states
  ErrorState,
  LoadError,
  NetworkError,
  ServerError,
  // Permission states
  NoPermissionState,
  AccessDenied,
  LoginRequired,
  SubscriptionRequired,
  // Universal wrapper
  DataState,
} from './states';

// Layout Components
export {
  AppShell,
  type AppShellProps,
  type NavItem,
} from './app-shell';

// Data Display Components
export {
  DataTable,
  type DataTableProps,
  type Column,
} from './data-table';

// Form & Filter Components
export {
  SearchFilters,
  type SearchFiltersProps,
  type FilterConfig,
  type FilterOption,
  type FilterValues,
} from './search-filters';
