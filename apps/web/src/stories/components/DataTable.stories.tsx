import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';
import { DataTable, Column } from '../../components/ui/data-table';

interface Property {
  id: string;
  address: string;
  city: string;
  county: string;
  justValue: number;
  owner: string;
  propertyType: string;
}

const sampleData: Property[] = [
  { id: '1', address: '123 Ocean Drive', city: 'Fort Lauderdale', county: 'Broward', justValue: 485000, owner: 'SMITH JOHN', propertyType: 'Residential' },
  { id: '2', address: '456 Palm Ave', city: 'Miami', county: 'Miami-Dade', justValue: 625000, owner: 'JOHNSON MARY', propertyType: 'Residential' },
  { id: '3', address: '789 Sunset Blvd', city: 'Tampa', county: 'Hillsborough', justValue: 320000, owner: 'WILLIAMS LLC', propertyType: 'Commercial' },
  { id: '4', address: '321 Beach Rd', city: 'Jacksonville', county: 'Duval', justValue: 275000, owner: 'BROWN ROBERT', propertyType: 'Residential' },
  { id: '5', address: '654 Marina Way', city: 'Orlando', county: 'Orange', justValue: 890000, owner: 'DAVIS HOLDINGS', propertyType: 'Commercial' },
  { id: '6', address: '987 Coral Ln', city: 'Naples', county: 'Collier', justValue: 1250000, owner: 'MILLER TRUST', propertyType: 'Residential' },
  { id: '7', address: '147 Gulf Shore', city: 'Sarasota', county: 'Sarasota', justValue: 975000, owner: 'WILSON ESTATE', propertyType: 'Residential' },
  { id: '8', address: '258 Harbor Dr', city: 'Clearwater', county: 'Pinellas', justValue: 445000, owner: 'TAYLOR JAMES', propertyType: 'Residential' },
  { id: '9', address: '369 Bay View', city: 'St. Petersburg', county: 'Pinellas', justValue: 520000, owner: 'ANDERSON LLC', propertyType: 'Commercial' },
  { id: '10', address: '741 Island Way', city: 'Key West', county: 'Monroe', justValue: 1850000, owner: 'THOMAS CORP', propertyType: 'Commercial' },
];

const columns: Column<Property>[] = [
  { id: 'address', header: 'Address', accessorKey: 'address' },
  { id: 'city', header: 'City', accessorKey: 'city' },
  { id: 'county', header: 'County', accessorKey: 'county' },
  {
    id: 'justValue',
    header: 'Just Value',
    accessorFn: (row) => `$${row.justValue.toLocaleString()}`,
    align: 'right',
  },
  { id: 'owner', header: 'Owner', accessorKey: 'owner' },
  {
    id: 'propertyType',
    header: 'Type',
    accessorFn: (row) => (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
        row.propertyType === 'Residential'
          ? 'bg-blue-100 text-blue-700'
          : 'bg-purple-100 text-purple-700'
      }`}>
        {row.propertyType}
      </span>
    ),
  },
];

const meta: Meta<typeof DataTable> = {
  title: 'Components/DataTable',
  component: DataTable,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: 'A reusable data table with sorting, pagination, and selection.',
      },
    },
  },
};

export default meta;
type Story = StoryObj<typeof DataTable<Property>>;

export const Default: Story = {
  render: () => (
    <DataTable
      data={sampleData}
      columns={columns}
      getRowId={(row) => row.id}
    />
  ),
};

export const WithPagination: Story = {
  render: () => {
    const [page, setPage] = useState(0);
    return (
      <DataTable
        data={sampleData}
        columns={columns}
        getRowId={(row) => row.id}
        paginated
        pageSize={5}
        currentPage={page}
        onPageChange={setPage}
      />
    );
  },
};

export const WithSelection: Story = {
  render: () => {
    const [selected, setSelected] = useState<string[]>([]);
    return (
      <div className="space-y-4">
        <div className="text-sm text-neutral-600">
          Selected: {selected.length > 0 ? selected.join(', ') : 'None'}
        </div>
        <DataTable
          data={sampleData}
          columns={columns}
          getRowId={(row) => row.id}
          selectable
          selectedIds={selected}
          onSelectionChange={setSelected}
        />
      </div>
    );
  },
};

export const WithRowClick: Story = {
  render: () => (
    <DataTable
      data={sampleData}
      columns={columns}
      getRowId={(row) => row.id}
      onRowClick={(row) => alert(`Clicked: ${row.address}`)}
    />
  ),
};

export const Loading: Story = {
  render: () => (
    <DataTable
      data={[]}
      columns={columns}
      getRowId={(row) => row.id}
      isLoading
    />
  ),
};

export const Empty: Story = {
  render: () => (
    <DataTable
      data={[]}
      columns={columns}
      getRowId={(row) => row.id}
      emptyMessage="No properties found matching your criteria."
    />
  ),
};

export const FullFeatured: Story = {
  name: 'Full Featured Table',
  render: () => {
    const [page, setPage] = useState(0);
    const [selected, setSelected] = useState<string[]>([]);

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="text-sm text-neutral-600">
            {selected.length} of {sampleData.length} selected
          </div>
          {selected.length > 0 && (
            <button className="px-4 py-2 text-sm font-medium text-white bg-[#0ABAB5] rounded-lg hover:bg-[#099A96]">
              Export Selected
            </button>
          )}
        </div>
        <DataTable
          data={sampleData}
          columns={columns}
          getRowId={(row) => row.id}
          selectable
          selectedIds={selected}
          onSelectionChange={setSelected}
          paginated
          pageSize={5}
          currentPage={page}
          onPageChange={setPage}
          onRowClick={(row) => console.log('Row clicked:', row)}
        />
      </div>
    );
  },
};
