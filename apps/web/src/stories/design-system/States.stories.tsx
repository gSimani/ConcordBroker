import type { Meta, StoryObj } from '@storybook/react';
import {
  SkeletonCard,
  SkeletonTable,
  SkeletonList,
  LoadingSpinner,
  EmptyState,
  NoPropertiesFound,
  NoSearchResults,
  NoDataAvailable,
  ErrorState,
  LoadError,
  NetworkError,
  ServerError,
  NoPermissionState,
  AccessDenied,
  LoginRequired,
  SubscriptionRequired,
  DataState,
} from '../../components/ui/states';
import { Search, FileQuestion, AlertCircle } from 'lucide-react';

const meta: Meta = {
  title: 'Design System/States',
  parameters: {
    docs: {
      description: {
        component: 'States-first design pattern components for handling loading, empty, error, and permission states.',
      },
    },
  },
};

export default meta;

// Loading States
export const LoadingCard: StoryObj = {
  name: 'Skeleton Card',
  render: () => (
    <div className="max-w-md">
      <SkeletonCard lines={3} showImage />
    </div>
  ),
};

export const LoadingTable: StoryObj = {
  name: 'Skeleton Table',
  render: () => (
    <SkeletonTable rows={5} columns={4} />
  ),
};

export const LoadingList: StoryObj = {
  name: 'Skeleton List',
  render: () => (
    <div className="max-w-md">
      <SkeletonList items={5} />
    </div>
  ),
};

export const Spinner: StoryObj = {
  name: 'Loading Spinner',
  render: () => (
    <div className="flex gap-8 items-center">
      <div className="text-center">
        <LoadingSpinner size="sm" />
        <p className="text-xs text-neutral-500 mt-2">Small</p>
      </div>
      <div className="text-center">
        <LoadingSpinner size="md" />
        <p className="text-xs text-neutral-500 mt-2">Medium</p>
      </div>
      <div className="text-center">
        <LoadingSpinner size="lg" />
        <p className="text-xs text-neutral-500 mt-2">Large</p>
      </div>
    </div>
  ),
};

// Empty States
export const GenericEmptyState: StoryObj = {
  name: 'Empty State - Generic',
  render: () => (
    <EmptyState
      icon={<Search className="h-12 w-12 text-neutral-400" />}
      title="No results found"
      description="Try adjusting your search or filter to find what you're looking for."
      action={<button className="px-4 py-2 bg-[#0ABAB5] text-white rounded-lg hover:bg-[#099A96]">Clear Filters</button>}
    />
  ),
};

export const EmptyProperties: StoryObj = {
  name: 'Empty State - No Properties',
  render: () => (
    <NoPropertiesFound onClearFilters={() => alert('Clear filters clicked')} />
  ),
};

export const EmptySearch: StoryObj = {
  name: 'Empty State - No Search Results',
  render: () => (
    <NoSearchResults query="oceanfront property under 100k" onClear={() => alert('Clear search clicked')} />
  ),
};

export const EmptyData: StoryObj = {
  name: 'Empty State - No Data',
  render: () => (
    <NoDataAvailable dataType="sales history" />
  ),
};

// Error States
export const GenericError: StoryObj = {
  name: 'Error State - Generic',
  render: () => (
    <ErrorState
      title="Something went wrong"
      description="We encountered an unexpected error. Please try again."
      error={new Error("Failed to fetch data: Network timeout")}
      onRetry={() => alert('Retry clicked')}
    />
  ),
};

export const DataLoadError: StoryObj = {
  name: 'Error State - Load Error',
  render: () => (
    <LoadError
      error={new Error("Unable to load property data")}
      onRetry={() => alert('Retry clicked')}
    />
  ),
};

export const ConnectionError: StoryObj = {
  name: 'Error State - Network Error',
  render: () => (
    <NetworkError onRetry={() => alert('Retry clicked')} />
  ),
};

export const BackendError: StoryObj = {
  name: 'Error State - Server Error',
  render: () => (
    <ServerError
      error={new Error("500 Internal Server Error")}
      onRetry={() => alert('Retry clicked')}
    />
  ),
};

// Permission States
export const PermissionDenied: StoryObj = {
  name: 'Permission State - Access Denied',
  render: () => (
    <AccessDenied onRequestAccess={() => alert('Request access clicked')} />
  ),
};

export const NeedsLogin: StoryObj = {
  name: 'Permission State - Login Required',
  render: () => (
    <LoginRequired onLogin={() => alert('Login clicked')} />
  ),
};

export const NeedsSubscription: StoryObj = {
  name: 'Permission State - Subscription Required',
  render: () => (
    <SubscriptionRequired onUpgrade={() => alert('Upgrade clicked')} />
  ),
};

// DataState Wrapper Examples
export const DataStateLoading: StoryObj = {
  name: 'DataState Wrapper - Loading',
  render: () => (
    <DataState
      data={null}
      isLoading={true}
      loadingComponent={<SkeletonCard lines={3} />}
    >
      {(data) => <div>Data: {JSON.stringify(data)}</div>}
    </DataState>
  ),
};

export const DataStateError: StoryObj = {
  name: 'DataState Wrapper - Error',
  render: () => (
    <DataState
      data={null}
      error={new Error("Failed to load properties")}
      onRetry={() => alert('Retry clicked')}
    >
      {(data) => <div>Data: {JSON.stringify(data)}</div>}
    </DataState>
  ),
};

export const DataStateEmpty: StoryObj = {
  name: 'DataState Wrapper - Empty',
  render: () => (
    <DataState
      data={[]}
      emptyComponent={<NoPropertiesFound />}
    >
      {(data) => <div>Properties: {data.length}</div>}
    </DataState>
  ),
};

export const DataStateWithData: StoryObj = {
  name: 'DataState Wrapper - With Data',
  render: () => (
    <DataState
      data={[
        { id: 1, address: '123 Main St', value: 450000 },
        { id: 2, address: '456 Oak Ave', value: 325000 },
      ]}
    >
      {(properties) => (
        <div className="space-y-2">
          {properties.map((p: any) => (
            <div key={p.id} className="p-4 bg-white rounded-lg border">
              <p className="font-medium">{p.address}</p>
              <p className="text-sm text-neutral-500">${p.value.toLocaleString()}</p>
            </div>
          ))}
        </div>
      )}
    </DataState>
  ),
};

// All States Overview
export const AllStates: StoryObj = {
  name: 'All States Overview',
  render: () => (
    <div className="space-y-12">
      <section>
        <h2 className="text-xl font-semibold mb-4">Loading States</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <h3 className="text-sm font-medium text-neutral-500 mb-2">Card</h3>
            <SkeletonCard lines={2} />
          </div>
          <div>
            <h3 className="text-sm font-medium text-neutral-500 mb-2">List</h3>
            <SkeletonList items={3} />
          </div>
          <div>
            <h3 className="text-sm font-medium text-neutral-500 mb-2">Spinner</h3>
            <div className="flex justify-center py-8">
              <LoadingSpinner size="lg" />
            </div>
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-4">Empty States</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="border rounded-lg">
            <NoPropertiesFound />
          </div>
          <div className="border rounded-lg">
            <NoSearchResults query="test query" />
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-4">Error States</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="border rounded-lg">
            <LoadError error={new Error("Connection failed")} />
          </div>
          <div className="border rounded-lg">
            <NetworkError />
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-4">Permission States</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="border rounded-lg">
            <AccessDenied />
          </div>
          <div className="border rounded-lg">
            <LoginRequired />
          </div>
          <div className="border rounded-lg">
            <SubscriptionRequired />
          </div>
        </div>
      </section>
    </div>
  ),
};
