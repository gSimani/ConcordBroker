/**
 * ConcordBroker Design System - State Components
 * ===============================================
 *
 * States-first design pattern components for handling:
 * - Loading states
 * - Empty states
 * - Error states
 * - No permission states
 *
 * Every data component should use these for consistent UX.
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { AlertCircle, Ban, FileQuestion, RefreshCw, Search, ShieldX, XCircle } from 'lucide-react';
import { Button } from './button';
import { Skeleton } from './skeleton';

/* ==========================================================================
   Loading States
   ========================================================================== */

interface SkeletonCardProps {
  className?: string;
  lines?: number;
  showImage?: boolean;
}

export function SkeletonCard({
  className,
  lines = 3,
  showImage = false
}: SkeletonCardProps) {
  return (
    <div className={cn('rounded-lg border bg-card p-4 space-y-4', className)}>
      {showImage && (
        <Skeleton className="h-40 w-full rounded-md" />
      )}
      <div className="space-y-2">
        <Skeleton className="h-4 w-3/4" />
        {Array.from({ length: lines - 1 }).map((_, i) => (
          <Skeleton key={i} className="h-4 w-1/2" />
        ))}
      </div>
    </div>
  );
}

interface SkeletonTableProps {
  className?: string;
  rows?: number;
  columns?: number;
}

export function SkeletonTable({
  className,
  rows = 5,
  columns = 4
}: SkeletonTableProps) {
  return (
    <div className={cn('rounded-lg border', className)}>
      {/* Header */}
      <div className="border-b bg-muted/50 p-4">
        <div className="flex gap-4">
          {Array.from({ length: columns }).map((_, i) => (
            <Skeleton key={i} className="h-4 flex-1" />
          ))}
        </div>
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="border-b last:border-b-0 p-4">
          <div className="flex gap-4">
            {Array.from({ length: columns }).map((_, colIndex) => (
              <Skeleton
                key={colIndex}
                className={cn(
                  'h-4 flex-1',
                  colIndex === 0 && 'w-1/4',
                  colIndex === columns - 1 && 'w-1/6'
                )}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

interface SkeletonListProps {
  className?: string;
  items?: number;
}

export function SkeletonList({
  className,
  items = 5
}: SkeletonListProps) {
  return (
    <div className={cn('space-y-3', className)}>
      {Array.from({ length: items }).map((_, i) => (
        <div key={i} className="flex items-center gap-3">
          <Skeleton className="h-10 w-10 rounded-full" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-1/3" />
            <Skeleton className="h-3 w-1/2" />
          </div>
        </div>
      ))}
    </div>
  );
}

interface LoadingSpinnerProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  label?: string;
}

export function LoadingSpinner({
  className,
  size = 'md',
  label = 'Loading...'
}: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8'
  };

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <RefreshCw className={cn('animate-spin text-brand-500', sizeClasses[size])} />
      <span className="text-sm text-muted-foreground sr-only">{label}</span>
    </div>
  );
}

/* ==========================================================================
   Empty States
   ========================================================================== */

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  icon = <Search className="h-12 w-12 text-muted-foreground/50" />,
  title,
  description,
  action,
  className
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-12 px-4 text-center',
        className
      )}
      role="status"
      aria-label={title}
    >
      <div className="mb-4">{icon}</div>
      <h3 className="text-lg font-semibold text-foreground mb-2">{title}</h3>
      {description && (
        <p className="text-sm text-muted-foreground max-w-md mb-4">
          {description}
        </p>
      )}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

/* Pre-built empty states for common use cases */
export function NoPropertiesFound({
  onClearFilters
}: {
  onClearFilters?: () => void;
}) {
  return (
    <EmptyState
      icon={<FileQuestion className="h-12 w-12 text-muted-foreground/50" />}
      title="No properties found"
      description="Try adjusting your search filters or search criteria to find more properties."
      action={
        onClearFilters && (
          <Button variant="outline" onClick={onClearFilters}>
            Clear Filters
          </Button>
        )
      }
    />
  );
}

export function NoSearchResults({
  query,
  onClear
}: {
  query?: string;
  onClear?: () => void;
}) {
  return (
    <EmptyState
      icon={<Search className="h-12 w-12 text-muted-foreground/50" />}
      title="No results found"
      description={
        query
          ? `No results found for "${query}". Try a different search term.`
          : "Your search didn't match any records."
      }
      action={
        onClear && (
          <Button variant="outline" onClick={onClear}>
            Clear Search
          </Button>
        )
      }
    />
  );
}

export function NoDataAvailable({
  dataType = 'data'
}: {
  dataType?: string;
}) {
  return (
    <EmptyState
      icon={<FileQuestion className="h-12 w-12 text-muted-foreground/50" />}
      title={`No ${dataType} available`}
      description={`There is no ${dataType} to display at this time.`}
    />
  );
}

/* ==========================================================================
   Error States
   ========================================================================== */

interface ErrorStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  error?: Error | string | null;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  icon = <AlertCircle className="h-12 w-12 text-error-500" />,
  title,
  description,
  error,
  onRetry,
  className
}: ErrorStateProps) {
  const errorMessage = error instanceof Error ? error.message : error;

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-12 px-4 text-center',
        className
      )}
      role="alert"
      aria-label={title}
    >
      <div className="mb-4">{icon}</div>
      <h3 className="text-lg font-semibold text-foreground mb-2">{title}</h3>
      {description && (
        <p className="text-sm text-muted-foreground max-w-md mb-2">
          {description}
        </p>
      )}
      {errorMessage && (
        <p className="text-xs text-error-600 font-mono bg-error-50 px-3 py-1 rounded mb-4 max-w-md truncate">
          {errorMessage}
        </p>
      )}
      {onRetry && (
        <Button variant="outline" onClick={onRetry} className="gap-2">
          <RefreshCw className="h-4 w-4" />
          Try Again
        </Button>
      )}
    </div>
  );
}

/* Pre-built error states for common use cases */
export function LoadError({
  error,
  onRetry
}: {
  error?: Error | string | null;
  onRetry?: () => void;
}) {
  return (
    <ErrorState
      title="Failed to load data"
      description="There was a problem loading the data. Please try again."
      error={error}
      onRetry={onRetry}
    />
  );
}

export function NetworkError({
  onRetry
}: {
  onRetry?: () => void;
}) {
  return (
    <ErrorState
      icon={<XCircle className="h-12 w-12 text-error-500" />}
      title="Connection error"
      description="Unable to connect to the server. Please check your internet connection and try again."
      onRetry={onRetry}
    />
  );
}

export function ServerError({
  error,
  onRetry
}: {
  error?: Error | string | null;
  onRetry?: () => void;
}) {
  return (
    <ErrorState
      title="Server error"
      description="Something went wrong on our end. Our team has been notified."
      error={error}
      onRetry={onRetry}
    />
  );
}

/* ==========================================================================
   Permission States
   ========================================================================== */

interface NoPermissionStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function NoPermissionState({
  icon = <ShieldX className="h-12 w-12 text-warning-500" />,
  title,
  description,
  action,
  className
}: NoPermissionStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-12 px-4 text-center',
        className
      )}
      role="alert"
      aria-label={title}
    >
      <div className="mb-4">{icon}</div>
      <h3 className="text-lg font-semibold text-foreground mb-2">{title}</h3>
      {description && (
        <p className="text-sm text-muted-foreground max-w-md mb-4">
          {description}
        </p>
      )}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

/* Pre-built permission states */
export function AccessDenied({
  onRequestAccess
}: {
  onRequestAccess?: () => void;
}) {
  return (
    <NoPermissionState
      title="Access Denied"
      description="You don't have permission to view this content. Please contact an administrator if you believe this is an error."
      action={
        onRequestAccess && (
          <Button variant="outline" onClick={onRequestAccess}>
            Request Access
          </Button>
        )
      }
    />
  );
}

export function LoginRequired({
  onLogin
}: {
  onLogin?: () => void;
}) {
  return (
    <NoPermissionState
      icon={<Ban className="h-12 w-12 text-warning-500" />}
      title="Login Required"
      description="Please sign in to view this content."
      action={
        onLogin && (
          <Button onClick={onLogin}>
            Sign In
          </Button>
        )
      }
    />
  );
}

export function SubscriptionRequired({
  onUpgrade
}: {
  onUpgrade?: () => void;
}) {
  return (
    <NoPermissionState
      title="Subscription Required"
      description="This feature requires an active subscription. Upgrade your plan to access this content."
      action={
        onUpgrade && (
          <Button onClick={onUpgrade}>
            Upgrade Plan
          </Button>
        )
      }
    />
  );
}

/* ==========================================================================
   Data State Wrapper Component
   ========================================================================== */

interface DataStateProps<T> {
  data: T | null | undefined;
  isLoading?: boolean;
  error?: Error | string | null;
  isEmpty?: boolean;
  hasPermission?: boolean;
  loadingComponent?: React.ReactNode;
  emptyComponent?: React.ReactNode;
  errorComponent?: React.ReactNode;
  noPermissionComponent?: React.ReactNode;
  children: (data: T) => React.ReactNode;
  onRetry?: () => void;
}

/**
 * Wrapper component that handles all data states in priority order:
 * 1. Loading
 * 2. Error
 * 3. No Permission
 * 4. Empty
 * 5. Data (children)
 */
export function DataState<T>({
  data,
  isLoading = false,
  error = null,
  isEmpty,
  hasPermission = true,
  loadingComponent,
  emptyComponent,
  errorComponent,
  noPermissionComponent,
  children,
  onRetry
}: DataStateProps<T>) {
  // Priority 1: Loading
  if (isLoading) {
    return <>{loadingComponent ?? <SkeletonCard />}</>;
  }

  // Priority 2: Error
  if (error) {
    return <>{errorComponent ?? <LoadError error={error} onRetry={onRetry} />}</>;
  }

  // Priority 3: No Permission
  if (!hasPermission) {
    return <>{noPermissionComponent ?? <AccessDenied />}</>;
  }

  // Priority 4: Empty (check isEmpty prop or if data is null/undefined/empty array)
  const isDataEmpty = isEmpty ?? (
    data === null ||
    data === undefined ||
    (Array.isArray(data) && data.length === 0)
  );

  if (isDataEmpty) {
    return <>{emptyComponent ?? <NoDataAvailable />}</>;
  }

  // Priority 5: Render children with data
  return <>{children(data as T)}</>;
}

export default DataState;
