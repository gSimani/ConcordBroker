import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';
import { SearchFilters, FilterConfig, FilterValues } from '../../components/ui/search-filters';

const meta: Meta<typeof SearchFilters> = {
  title: 'Components/SearchFilters',
  component: SearchFilters,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: 'Comprehensive search and filter component for property search.',
      },
    },
  },
};

export default meta;
type Story = StoryObj<typeof SearchFilters>;

const countyOptions = [
  { value: 'broward', label: 'Broward', count: 1250000 },
  { value: 'miami-dade', label: 'Miami-Dade', count: 2100000 },
  { value: 'palm-beach', label: 'Palm Beach', count: 980000 },
  { value: 'hillsborough', label: 'Hillsborough', count: 750000 },
  { value: 'orange', label: 'Orange', count: 620000 },
  { value: 'duval', label: 'Duval', count: 540000 },
];

const propertyTypeOptions = [
  { value: 'residential', label: 'Residential', count: 6500000 },
  { value: 'commercial', label: 'Commercial', count: 1200000 },
  { value: 'vacant-land', label: 'Vacant Land', count: 850000 },
  { value: 'industrial', label: 'Industrial', count: 320000 },
];

const statusOptions = [
  { value: 'active', label: 'Active', count: 7200000 },
  { value: 'pending', label: 'Pending', count: 450000 },
  { value: 'sold', label: 'Sold', count: 1463150 },
];

const filterConfigs: FilterConfig[] = [
  {
    id: 'county',
    label: 'County',
    type: 'select',
    options: countyOptions,
    placeholder: 'All Counties',
  },
  {
    id: 'propertyType',
    label: 'Property Type',
    type: 'select',
    options: propertyTypeOptions,
    placeholder: 'All Types',
  },
  {
    id: 'status',
    label: 'Status',
    type: 'select',
    options: statusOptions,
    placeholder: 'All Statuses',
  },
  {
    id: 'priceRange',
    label: 'Price Range',
    type: 'range',
    min: 0,
    max: 10000000,
  },
  {
    id: 'yearBuilt',
    label: 'Year Built',
    type: 'range',
    min: 1900,
    max: 2024,
  },
  {
    id: 'bedrooms',
    label: 'Bedrooms',
    type: 'select',
    options: [
      { value: '1', label: '1+' },
      { value: '2', label: '2+' },
      { value: '3', label: '3+' },
      { value: '4', label: '4+' },
      { value: '5', label: '5+' },
    ],
  },
];

const SearchFiltersWithState = (props: Partial<React.ComponentProps<typeof SearchFilters>>) => {
  const [values, setValues] = useState<FilterValues>({});

  return (
    <div className="space-y-4">
      <SearchFilters
        filters={filterConfigs}
        values={values}
        onChange={setValues}
        {...props}
      />
      <div className="p-4 bg-neutral-50 rounded-lg">
        <h3 className="text-sm font-medium text-neutral-700 mb-2">Current Filter Values:</h3>
        <pre className="text-xs text-neutral-600 overflow-auto">
          {JSON.stringify(values, null, 2)}
        </pre>
      </div>
    </div>
  );
};

export const Default: Story = {
  render: () => <SearchFiltersWithState />,
};

export const WithInitialValues: Story = {
  render: () => {
    const [values, setValues] = useState<FilterValues>({
      county: 'broward',
      propertyType: 'residential',
    });

    return (
      <SearchFilters
        filters={filterConfigs}
        values={values}
        onChange={setValues}
      />
    );
  },
};

export const CustomPlaceholder: Story = {
  render: () => (
    <SearchFiltersWithState
      searchPlaceholder="Search by address, parcel ID, or owner name..."
    />
  ),
};

export const LimitedVisibleFilters: Story = {
  render: () => (
    <SearchFiltersWithState visibleFilters={2} />
  ),
};

export const NoAdvancedFilters: Story = {
  render: () => (
    <SearchFiltersWithState showAdvanced={false} visibleFilters={6} />
  ),
};

export const PropertySearchExample: Story = {
  name: 'Property Search Use Case',
  render: () => {
    const [values, setValues] = useState<FilterValues>({});
    const [results, setResults] = useState<number | null>(null);

    const handleChange = (newValues: FilterValues) => {
      setValues(newValues);
      // Simulate search results
      setTimeout(() => {
        setResults(Math.floor(Math.random() * 100000) + 1000);
      }, 500);
    };

    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg border border-neutral-200 p-4">
          <h2 className="text-lg font-semibold mb-4">Search Florida Properties</h2>
          <SearchFilters
            filters={filterConfigs}
            values={values}
            onChange={handleChange}
            searchPlaceholder="Search by address, parcel ID, or owner..."
          />
        </div>

        {results !== null && (
          <div className="text-sm text-neutral-600">
            Found <span className="font-semibold text-[#0ABAB5]">{results.toLocaleString()}</span> properties matching your criteria
          </div>
        )}
      </div>
    );
  },
};
