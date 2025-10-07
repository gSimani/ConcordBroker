import React from 'react';
import { MiniPropertyCard } from '@/components/property/MiniPropertyCard';
import { mockProperties } from '@/data/mockPropertyData';

export function TestPropertyCards() {
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Test Property Cards - Appraised Values</h1>

      <div className="mb-8 p-4 bg-blue-50 rounded-lg">
        <h2 className="text-lg font-semibold mb-2">Data Field Mapping</h2>
        <p className="text-sm text-gray-700">
          The MiniPropertyCard component checks for appraised values in the following fields:
        </p>
        <ul className="list-disc list-inside mt-2 text-sm">
          <li><code>jv</code> - Primary field name in database</li>
          <li><code>just_value</code> - Alternative field name</li>
          <li><code>appraised_value</code> - Another alternative</li>
          <li><code>market_value</code> - Market value field</li>
        </ul>
        <p className="mt-2 text-sm text-gray-700">
          The component will display "N/A" only if ALL these fields are missing or null.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {mockProperties.map((property) => (
          <div key={property.parcel_id} className="space-y-2">
            <div className="bg-gray-100 p-2 rounded text-xs">
              <h3 className="font-semibold mb-1">Raw Data Values:</h3>
              <div className="grid grid-cols-2 gap-1">
                <span>jv:</span>
                <span className="font-mono">${property.jv?.toLocaleString() || 'null'}</span>
                <span>just_value:</span>
                <span className="font-mono">${property.just_value?.toLocaleString() || 'null'}</span>
                <span>market_value:</span>
                <span className="font-mono">${property.market_value?.toLocaleString() || 'null'}</span>
              </div>
            </div>

            <MiniPropertyCard
              parcelId={property.parcel_id}
              data={property}
              variant="grid"
            />
          </div>
        ))}
      </div>

      <div className="mt-8 p-4 bg-yellow-50 rounded-lg">
        <h2 className="text-lg font-semibold mb-2">Test Case: Missing Values</h2>
        <p className="text-sm text-gray-700 mb-4">
          This card has no appraised value fields to test the N/A display:
        </p>

        <div className="max-w-md">
          <MiniPropertyCard
            parcelId="TEST-NO-VALUE"
            data={{
              phy_addr1: "999 Test Street",
              phy_city: "Test City",
              phy_zipcd: "99999",
              owner_name: "Test Owner",
              // No value fields provided - should show N/A
            }}
            variant="grid"
          />
        </div>
      </div>

      <div className="mt-8 p-4 bg-green-50 rounded-lg">
        <h2 className="text-lg font-semibold mb-2">Success Criteria</h2>
        <ul className="list-disc list-inside text-sm">
          <li>✅ Properties with value data show the appraised value in currency format</li>
          <li>✅ Properties without value data show "N/A"</li>
          <li>✅ Condo units show unit numbers in the address</li>
          <li>✅ All value fields are properly mapped from the database</li>
        </ul>
      </div>
    </div>
  );
}