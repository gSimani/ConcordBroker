// Test file to verify sales data flow logic
import React from 'react';
import { MiniPropertyCard } from './components/property/MiniPropertyCard';

// Mock property data with sales information
const mockPropertyWithSales = {
  parcel_id: 'TEST-PARCEL-001',
  phy_addr1: '123 Test Street',
  phy_city: 'Miami',
  phy_zipcd: '33101',
  owner_name: 'John Doe',
  jv: 450000,
  county: 'Miami-Dade',
  last_qualified_sale: {
    sale_date: '2023-06-15T00:00:00',
    sale_price: 425000,
    instrument_type: 'Warranty Deed',
    book_page: '12345/678'
  },
  has_qualified_sale: true
};

const mockPropertyWithoutSales = {
  parcel_id: 'TEST-PARCEL-002',
  phy_addr1: '456 Test Avenue',
  phy_city: 'Tampa',
  phy_zipcd: '33602',
  owner_name: 'Jane Smith',
  jv: 320000,
  county: 'Hillsborough',
  last_qualified_sale: null,
  has_qualified_sale: false
};

// Test Component
export function TestSalesDataFlow() {
  console.log('Testing sales data flow with mock data...');

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-2xl font-bold">Sales Data Flow Test</h1>

      <div>
        <h2 className="text-lg font-semibold mb-2">Property WITH Sales Data</h2>
        <div className="max-w-md">
          <MiniPropertyCard
            parcelId={mockPropertyWithSales.parcel_id}
            data={mockPropertyWithSales}
          />
        </div>
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-2">Property WITHOUT Sales Data</h2>
        <div className="max-w-md">
          <MiniPropertyCard
            parcelId={mockPropertyWithoutSales.parcel_id}
            data={mockPropertyWithoutSales}
          />
        </div>
      </div>
    </div>
  );
}

export default TestSalesDataFlow;