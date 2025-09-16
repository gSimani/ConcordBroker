/**
 * Property Card Component with Full Data Tracking
 * Every data point is mapped to its database source
 */

import React from 'react';
import { Card } from '../ui/card';
import { MapPin, Home, DollarSign, Calendar, User, Square } from 'lucide-react';
import { useTrackedData } from '../../hooks/useTrackedData';

interface TrackedPropertyCardProps {
  propertyId: string;
  index: number;
  onSelect?: (propertyId: string) => void;
}

export const TrackedPropertyCard: React.FC<TrackedPropertyCardProps> = ({
  propertyId,
  index,
  onSelect
}) => {
  // Track each data field separately for granular tracking
  const { data: address } = useTrackedData(
    'parcels', 
    'site_address', 
    propertyId,
    `property-card-address-${propertyId}`
  );
  
  const { data: city } = useTrackedData(
    'parcels',
    'site_city',
    propertyId,
    `property-card-city-${propertyId}`
  );
  
  const { data: assessedValue } = useTrackedData(
    'parcels',
    'assessed_value',
    propertyId,
    `property-card-price-${propertyId}`
  );
  
  const { data: owner } = useTrackedData(
    'parcels',
    'owner_name',
    propertyId,
    `property-card-owner-${propertyId}`
  );
  
  const { data: sqft } = useTrackedData(
    'parcels',
    'total_square_feet',
    propertyId,
    `property-card-sqft-${propertyId}`
  );
  
  const { data: yearBuilt } = useTrackedData(
    'parcels',
    'year_built',
    propertyId,
    `property-card-year-${propertyId}`
  );
  
  const { data: lastSaleDate } = useTrackedData(
    'parcels',
    'last_sale_date',
    propertyId,
    `property-card-sale-date-${propertyId}`
  );
  
  const { data: lastSalePrice } = useTrackedData(
    'parcels',
    'last_sale_price',
    propertyId,
    `property-card-sale-price-${propertyId}`
  );

  const cardId = `property-card-${propertyId}`;

  return (
    <Card 
      id={cardId}
      data-component="TrackedPropertyCard"
      data-record-id={propertyId}
      data-index={index}
      className="p-4 hover:shadow-lg transition-shadow cursor-pointer"
      onClick={() => onSelect?.(propertyId)}
    >
      {/* Card Header */}
      <div 
        id={`${cardId}-header`}
        className="mb-3"
      >
        {/* Address Section */}
        <div 
          id={`property-card-address-${propertyId}`}
          data-source-table="parcels"
          data-source-field="site_address"
          data-field-type="string"
          data-searchable="true"
          className="flex items-start gap-2 mb-2"
        >
          <MapPin className="w-4 h-4 text-gray-500 mt-1" />
          <div id={`${cardId}-address-content`}>
            <div 
              id={`${cardId}-street-address`}
              className="font-semibold text-lg"
            >
              {address || 'Loading...'}
            </div>
            <div 
              id={`property-card-city-${propertyId}`}
              data-source-table="parcels"
              data-source-field="site_city"
              data-field-type="string"
              className="text-sm text-gray-600"
            >
              {city || 'Loading...'}
            </div>
          </div>
        </div>

        {/* Price Display */}
        <div 
          id={`property-card-price-${propertyId}`}
          data-source-table="parcels"
          data-source-field="assessed_value"
          data-field-type="currency"
          data-transform="formatCurrency"
          data-aggregation="sum,avg"
          data-sortable="true"
          className="flex items-center gap-2 mb-2"
        >
          <DollarSign className="w-5 h-5 text-green-600" />
          <span className="text-2xl font-bold text-blue-600">
            {assessedValue ? `$${assessedValue.toLocaleString()}` : 'N/A'}
          </span>
        </div>
      </div>

      {/* Property Details */}
      <div 
        id={`${cardId}-details`}
        className="space-y-2 border-t pt-3"
      >
        {/* Owner Information */}
        <div 
          id={`property-card-owner-${propertyId}`}
          data-source-table="parcels"
          data-source-field="owner_name"
          data-field-type="string"
          data-sensitive="true"
          data-permission="authenticated"
          className="flex items-center gap-2 text-sm"
        >
          <User className="w-4 h-4 text-gray-500" />
          <span className="text-gray-700">
            {owner || 'Owner information restricted'}
          </span>
        </div>

        {/* Property Size */}
        <div 
          id={`property-card-sqft-${propertyId}`}
          data-source-table="parcels"
          data-source-field="total_square_feet"
          data-field-type="number"
          data-format="number"
          data-sortable="true"
          className="flex items-center gap-2 text-sm"
        >
          <Square className="w-4 h-4 text-gray-500" />
          <span className="text-gray-700">
            {sqft ? `${sqft.toLocaleString()} sq ft` : 'N/A'}
          </span>
        </div>

        {/* Year Built */}
        <div 
          id={`property-card-year-${propertyId}`}
          data-source-table="parcels"
          data-source-field="year_built"
          data-field-type="number"
          data-validation="min:1800,max:2025"
          className="flex items-center gap-2 text-sm"
        >
          <Home className="w-4 h-4 text-gray-500" />
          <span className="text-gray-700">
            Built: {yearBuilt || 'N/A'}
          </span>
        </div>

        {/* Last Sale Information */}
        <div 
          id={`${cardId}-last-sale`}
          className="flex items-center gap-2 text-sm"
        >
          <Calendar className="w-4 h-4 text-gray-500" />
          <div id={`${cardId}-sale-info`}>
            <span 
              id={`property-card-sale-date-${propertyId}`}
              data-source-table="parcels"
              data-source-field="last_sale_date"
              data-field-type="date"
              data-format="MM/DD/YYYY"
              className="text-gray-700"
            >
              Last Sale: {lastSaleDate || 'N/A'}
            </span>
            {lastSalePrice && (
              <span 
                id={`property-card-sale-price-${propertyId}`}
                data-source-table="parcels"
                data-source-field="last_sale_price"
                data-field-type="currency"
                data-transform="formatCurrency"
                className="text-gray-700 ml-2"
              >
                (${lastSalePrice.toLocaleString()})
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Calculated Fields */}
      <div 
        id={`${cardId}-calculations`}
        className="mt-3 pt-3 border-t"
      >
        {/* Price per Square Foot (Calculated) */}
        {assessedValue && sqft && (
          <div 
            id={`property-card-price-per-sqft-${propertyId}`}
            data-source-table="parcels"
            data-source-fields="assessed_value,total_square_feet"
            data-calculation="assessed_value / total_square_feet"
            data-field-type="currency"
            data-derived="true"
            className="text-sm text-gray-600"
          >
            ${Math.round(assessedValue / sqft)}/sq ft
          </div>
        )}

        {/* Property Age (Calculated) */}
        {yearBuilt && (
          <div 
            id={`property-card-age-${propertyId}`}
            data-source-table="parcels"
            data-source-field="year_built"
            data-calculation="current_year - year_built"
            data-field-type="number"
            data-derived="true"
            className="text-sm text-gray-600"
          >
            {new Date().getFullYear() - yearBuilt} years old
          </div>
        )}
      </div>

      {/* Metadata Footer */}
      <div 
        id={`${cardId}-metadata`}
        data-last-updated={new Date().toISOString()}
        data-cache-status="fresh"
        className="mt-3 pt-2 border-t text-xs text-gray-400"
      >
        <div id={`${cardId}-parcel-id`}>
          Parcel: {propertyId}
        </div>
        <div id={`${cardId}-data-source`}>
          Source: Broward County Records
        </div>
      </div>
    </Card>
  );
};

// Example of how to use the component
export const PropertyCardExample: React.FC = () => {
  const handlePropertySelect = (propertyId: string) => {
    console.log(`Selected property: ${propertyId}`);
    // Navigate to property detail page
    window.location.href = `/property/${propertyId}`;
  };

  return (
    <div id="property-grid-container" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <TrackedPropertyCard 
        propertyId="123456789"
        index={0}
        onSelect={handlePropertySelect}
      />
      <TrackedPropertyCard 
        propertyId="987654321"
        index={1}
        onSelect={handlePropertySelect}
      />
    </div>
  );
};