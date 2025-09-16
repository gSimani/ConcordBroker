/**
 * ConcordBroker Data Mapping Configuration
 * This file maps all database fields to their UI locations
 */

export interface FieldMapping {
  dbField: string;
  displayName: string;
  type: 'string' | 'number' | 'currency' | 'date' | 'boolean' | 'array' | 'object';
  uiLocations: string[];
  format?: string;
  transform?: (value: any) => any;
  validation?: {
    required?: boolean;
    min?: number;
    max?: number;
    pattern?: RegExp;
  };
  searchable?: boolean;
  sortable?: boolean;
  sensitive?: boolean;
  permissions?: string[];
  aggregations?: string[];
}

export interface TableMapping {
  tableName: string;
  displayName: string;
  primaryKey: string;
  fields: Record<string, FieldMapping>;
}

export const DATA_MAPPING: Record<string, TableMapping> = {
  parcels: {
    tableName: 'parcels',
    displayName: 'Property Information',
    primaryKey: 'parcel_id',
    fields: {
      parcel_id: {
        dbField: 'parcel_id',
        displayName: 'Parcel ID',
        type: 'string',
        uiLocations: [
          'property-header-parcel-id',
          'property-detail-parcel-number',
          'search-result-card-id',
          'property-card-parcel-${id}'
        ],
        format: 'uppercase',
        searchable: true,
        sortable: true,
        validation: {
          required: true,
          pattern: /^\d{10,}$/
        }
      },
      site_address: {
        dbField: 'site_address',
        displayName: 'Property Address',
        type: 'string',
        uiLocations: [
          'property-header-address',
          'search-result-address',
          'map-popup-address',
          'property-card-address-${id}'
        ],
        searchable: true,
        validation: {
          required: true
        }
      },
      site_city: {
        dbField: 'site_city',
        displayName: 'City',
        type: 'string',
        uiLocations: [
          'property-location-city',
          'search-filter-city',
          'property-card-city-${id}'
        ],
        searchable: true,
        sortable: true
      },
      site_zip: {
        dbField: 'site_zip',
        displayName: 'ZIP Code',
        type: 'string',
        uiLocations: [
          'property-location-zip',
          'search-filter-zip',
          'property-card-zip-${id}'
        ],
        searchable: true,
        validation: {
          pattern: /^\d{5}(-\d{4})?$/
        }
      },
      owner_name: {
        dbField: 'owner_name',
        displayName: 'Owner Name',
        type: 'string',
        uiLocations: [
          'property-owner-section',
          'owner-details-card',
          'search-result-owner',
          'property-card-owner-${id}'
        ],
        searchable: true,
        sensitive: true,
        permissions: ['authenticated', 'admin']
      },
      assessed_value: {
        dbField: 'assessed_value',
        displayName: 'Assessed Value',
        type: 'currency',
        uiLocations: [
          'property-price-display',
          'property-card-price',
          'dashboard-total-value',
          'property-value-assessed-${id}'
        ],
        format: 'currency',
        transform: (value: number) => `$${(value || 0).toLocaleString()}`,
        sortable: true,
        aggregations: ['sum', 'avg', 'min', 'max'],
        validation: {
          min: 0,
          max: 999999999
        }
      },
      taxable_value: {
        dbField: 'taxable_value',
        displayName: 'Taxable Value',
        type: 'currency',
        uiLocations: [
          'property-tax-value',
          'tax-calculation-base',
          'property-value-taxable-${id}'
        ],
        format: 'currency',
        transform: (value: number) => `$${(value || 0).toLocaleString()}`,
        validation: {
          min: 0
        }
      },
      just_value: {
        dbField: 'just_value',
        displayName: 'Market Value',
        type: 'currency',
        uiLocations: [
          'property-market-value',
          'property-value-market-${id}',
          'valuation-comparison-market'
        ],
        format: 'currency',
        transform: (value: number) => `$${(value || 0).toLocaleString()}`
      },
      total_square_feet: {
        dbField: 'total_square_feet',
        displayName: 'Square Footage',
        type: 'number',
        uiLocations: [
          'property-size-sqft',
          'property-card-sqft-${id}',
          'search-filter-sqft'
        ],
        format: 'number',
        transform: (value: number) => `${(value || 0).toLocaleString()} sq ft`,
        sortable: true,
        validation: {
          min: 0
        }
      },
      year_built: {
        dbField: 'year_built',
        displayName: 'Year Built',
        type: 'number',
        uiLocations: [
          'property-year-built',
          'property-age-display',
          'property-card-year-${id}'
        ],
        sortable: true,
        validation: {
          min: 1800,
          max: new Date().getFullYear()
        }
      },
      bedrooms: {
        dbField: 'bedrooms',
        displayName: 'Bedrooms',
        type: 'number',
        uiLocations: [
          'property-bedrooms-count',
          'property-card-beds-${id}',
          'search-filter-bedrooms'
        ],
        sortable: true,
        searchable: true,
        validation: {
          min: 0,
          max: 20
        }
      },
      bathrooms: {
        dbField: 'bathrooms',
        displayName: 'Bathrooms',
        type: 'number',
        uiLocations: [
          'property-bathrooms-count',
          'property-card-baths-${id}',
          'search-filter-bathrooms'
        ],
        sortable: true,
        searchable: true,
        validation: {
          min: 0,
          max: 20
        }
      },
      property_use_code: {
        dbField: 'property_use_code',
        displayName: 'Property Type',
        type: 'string',
        uiLocations: [
          'property-type-display',
          'property-use-category',
          'search-filter-type'
        ],
        transform: (code: string) => {
          const types: Record<string, string> = {
            '001': 'Single Family',
            '002': 'Condominium',
            '003': 'Multi-Family',
            '004': 'Vacant Land',
            '100': 'Commercial'
          };
          return types[code] || code;
        },
        searchable: true,
        sortable: true
      },
      last_sale_date: {
        dbField: 'last_sale_date',
        displayName: 'Last Sale Date',
        type: 'date',
        uiLocations: [
          'property-last-sale-date',
          'sales-history-recent',
          'property-card-sale-date-${id}'
        ],
        format: 'MM/DD/YYYY',
        transform: (value: string) => {
          if (!value) return 'N/A';
          return new Date(value).toLocaleDateString();
        },
        sortable: true
      },
      last_sale_price: {
        dbField: 'last_sale_price',
        displayName: 'Last Sale Price',
        type: 'currency',
        uiLocations: [
          'property-last-sale-price',
          'sales-history-price',
          'property-card-sale-price-${id}'
        ],
        format: 'currency',
        transform: (value: number) => value ? `$${value.toLocaleString()}` : 'N/A'
      }
    }
  },
  
  sales_history: {
    tableName: 'sales_history',
    displayName: 'Sales History',
    primaryKey: 'sale_id',
    fields: {
      sale_id: {
        dbField: 'sale_id',
        displayName: 'Sale ID',
        type: 'string',
        uiLocations: [
          'sales-history-row-id-${id}',
          'transaction-detail-id'
        ]
      },
      parcel_id: {
        dbField: 'parcel_id',
        displayName: 'Parcel ID',
        type: 'string',
        uiLocations: [
          'sales-history-parcel-ref',
          'transaction-property-link'
        ]
      },
      sale_date: {
        dbField: 'sale_date',
        displayName: 'Sale Date',
        type: 'date',
        uiLocations: [
          'sales-history-date-${id}',
          'timeline-sale-event-${id}',
          'transaction-date-display'
        ],
        format: 'MM/DD/YYYY',
        sortable: true
      },
      sale_price: {
        dbField: 'sale_price',
        displayName: 'Sale Price',
        type: 'currency',
        uiLocations: [
          'sales-history-price-${id}',
          'price-trend-point-${id}',
          'transaction-amount-display'
        ],
        format: 'currency',
        transform: (value: number) => `$${(value || 0).toLocaleString()}`,
        sortable: true,
        aggregations: ['sum', 'avg', 'min', 'max']
      },
      buyer_name: {
        dbField: 'buyer_name',
        displayName: 'Buyer',
        type: 'string',
        uiLocations: [
          'sales-history-buyer-${id}',
          'transaction-buyer-name'
        ],
        sensitive: true,
        permissions: ['admin', 'authenticated']
      },
      seller_name: {
        dbField: 'seller_name',
        displayName: 'Seller',
        type: 'string',
        uiLocations: [
          'sales-history-seller-${id}',
          'transaction-seller-name'
        ],
        sensitive: true,
        permissions: ['admin', 'authenticated']
      }
    }
  },
  
  tax_assessments: {
    tableName: 'tax_assessments',
    displayName: 'Tax Assessments',
    primaryKey: 'assessment_id',
    fields: {
      tax_year: {
        dbField: 'tax_year',
        displayName: 'Tax Year',
        type: 'number',
        uiLocations: [
          'tax-assessment-year-${year}',
          'tax-history-year-${year}',
          'annual-tax-display-${year}'
        ],
        sortable: true
      },
      tax_amount: {
        dbField: 'tax_amount',
        displayName: 'Tax Amount',
        type: 'currency',
        uiLocations: [
          'tax-amount-${year}',
          'tax-bill-total-${year}',
          'property-tax-display'
        ],
        format: 'currency',
        transform: (value: number) => `$${(value || 0).toLocaleString()}`,
        aggregations: ['sum', 'avg']
      },
      millage_rate: {
        dbField: 'millage_rate',
        displayName: 'Millage Rate',
        type: 'number',
        uiLocations: [
          'tax-millage-rate',
          'tax-calculation-rate',
          'millage-display-${year}'
        ],
        format: 'percentage',
        transform: (value: number) => `${(value * 100).toFixed(3)}%`
      }
    }
  },
  
  building_permits: {
    tableName: 'building_permits',
    displayName: 'Building Permits',
    primaryKey: 'permit_id',
    fields: {
      permit_number: {
        dbField: 'permit_number',
        displayName: 'Permit Number',
        type: 'string',
        uiLocations: [
          'permit-number-${id}',
          'permit-list-item-${id}',
          'permit-detail-number'
        ],
        searchable: true
      },
      permit_type: {
        dbField: 'permit_type',
        displayName: 'Permit Type',
        type: 'string',
        uiLocations: [
          'permit-type-${id}',
          'permit-category-badge-${id}'
        ],
        searchable: true,
        sortable: true
      },
      issue_date: {
        dbField: 'issue_date',
        displayName: 'Issue Date',
        type: 'date',
        uiLocations: [
          'permit-issue-date-${id}',
          'permit-timeline-date-${id}'
        ],
        format: 'MM/DD/YYYY',
        sortable: true
      },
      estimated_value: {
        dbField: 'estimated_value',
        displayName: 'Estimated Value',
        type: 'currency',
        uiLocations: [
          'permit-value-${id}',
          'permit-cost-estimate-${id}'
        ],
        format: 'currency',
        transform: (value: number) => value ? `$${value.toLocaleString()}` : 'N/A'
      }
    }
  }
};

// Helper function to get field mapping
export function getFieldMapping(table: string, field: string): FieldMapping | undefined {
  return DATA_MAPPING[table]?.fields[field];
}

// Helper function to get all UI locations for a field
export function getUILocations(table: string, field: string): string[] {
  const mapping = getFieldMapping(table, field);
  return mapping?.uiLocations || [];
}

// Helper function to validate field value
export function validateField(table: string, field: string, value: any): boolean {
  const mapping = getFieldMapping(table, field);
  if (!mapping?.validation) return true;
  
  const { required, min, max, pattern } = mapping.validation;
  
  if (required && !value) return false;
  if (min !== undefined && value < min) return false;
  if (max !== undefined && value > max) return false;
  if (pattern && !pattern.test(String(value))) return false;
  
  return true;
}

// Helper function to transform field value for display
export function transformFieldValue(table: string, field: string, value: any): any {
  const mapping = getFieldMapping(table, field);
  if (!mapping?.transform) return value;
  
  return mapping.transform(value);
}

// Export types for use in components
export type TableName = keyof typeof DATA_MAPPING;
export type ParcelFields = keyof typeof DATA_MAPPING.parcels.fields;
export type SalesHistoryFields = keyof typeof DATA_MAPPING.sales_history.fields;