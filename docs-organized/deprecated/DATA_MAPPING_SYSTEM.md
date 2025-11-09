# ConcordBroker Data Mapping & Tracking System

## Overview
This document defines the comprehensive data mapping system that tracks every piece of data from database to UI, enabling precise communication about data flow and location.

## 1. Data Attribute System

### Every Data-Displaying Element MUST Have:

```jsx
// Required data attributes for ALL elements displaying database data
<div 
  id="property-price-display"
  data-source-table="parcels"
  data-source-field="assessed_value"
  data-field-type="currency"
  data-transform="formatCurrency"
  data-update-frequency="realtime"
  data-fallback="N/A"
>
  ${250,000}
</div>
```

### Data Attribute Definitions:

| Attribute | Purpose | Example |
|-----------|---------|---------|
| `data-source-table` | Database table name | `parcels`, `sales_history`, `florida_parcels` |
| `data-source-field` | Exact database column | `assessed_value`, `owner_name`, `site_address` |
| `data-field-type` | Data type for validation | `string`, `number`, `currency`, `date`, `boolean` |
| `data-transform` | Transformation function applied | `formatCurrency`, `toUpperCase`, `dateFormat` |
| `data-update-frequency` | How often data refreshes | `realtime`, `hourly`, `daily`, `static` |
| `data-fallback` | Value when data is null/undefined | `"N/A"`, `"Loading..."`, `"--"` |
| `data-validation` | Validation rules | `required`, `min:0`, `max:1000000` |
| `data-api-endpoint` | API endpoint fetching this data | `/api/properties/{id}` |

## 2. Database to UI Mapping Configuration

Create a centralized mapping configuration:

```typescript
// data-mapping.config.ts
export const DATA_MAPPING = {
  parcels: {
    tableName: 'parcels',
    displayName: 'Property Information',
    fields: {
      parcel_id: {
        dbField: 'parcel_id',
        displayName: 'Parcel ID',
        type: 'string',
        uiLocations: [
          'property-header-parcel-id',
          'property-detail-parcel-number',
          'search-result-card-id'
        ],
        format: 'uppercase',
        searchable: true,
        sortable: true
      },
      assessed_value: {
        dbField: 'assessed_value',
        displayName: 'Assessed Value',
        type: 'currency',
        uiLocations: [
          'property-price-display',
          'property-card-price',
          'dashboard-total-value'
        ],
        format: 'currency',
        transform: (value) => `$${value.toLocaleString()}`,
        aggregations: ['sum', 'avg', 'min', 'max'],
        validation: {
          min: 0,
          max: 999999999
        }
      },
      site_address: {
        dbField: 'site_address',
        displayName: 'Property Address',
        type: 'string',
        uiLocations: [
          'property-header-address',
          'search-result-address',
          'map-popup-address'
        ],
        searchable: true,
        required: true,
        components: {
          full: 'site_address',
          street: 'site_addr',
          city: 'site_city',
          state: 'site_state',
          zip: 'site_zip'
        }
      },
      owner_name: {
        dbField: 'owner_name',
        displayName: 'Owner Name',
        type: 'string',
        uiLocations: [
          'property-owner-section',
          'owner-details-card',
          'search-result-owner'
        ],
        searchable: true,
        sensitive: true,
        permissions: ['admin', 'authenticated']
      }
    }
  },
  sales_history: {
    tableName: 'sales_history',
    displayName: 'Sales History',
    fields: {
      sale_date: {
        dbField: 'sale_date',
        displayName: 'Sale Date',
        type: 'date',
        uiLocations: [
          'sales-history-table-date',
          'property-last-sale-date',
          'timeline-sale-event'
        ],
        format: 'MM/DD/YYYY',
        sortable: true
      },
      sale_price: {
        dbField: 'sale_price',
        displayName: 'Sale Price',
        type: 'currency',
        uiLocations: [
          'sales-history-table-price',
          'property-last-sale-price',
          'price-history-chart'
        ],
        format: 'currency',
        validation: {
          min: 0
        }
      }
    }
  }
};
```

## 3. Component Data Annotation System

### Example: Property Card Component

```tsx
// PropertyCard.tsx with full data mapping
interface PropertyCardProps {
  property: Property;
}

export const PropertyCard: React.FC<PropertyCardProps> = ({ property }) => {
  return (
    <div 
      id={`property-card-${property.parcel_id}`}
      data-component="PropertyCard"
      data-source-entity="property"
      data-record-id={property.parcel_id}
    >
      {/* Property Address */}
      <div 
        id={`property-address-${property.parcel_id}`}
        data-source-table="parcels"
        data-source-field="site_address"
        data-field-type="string"
        className="text-lg font-semibold"
      >
        {property.site_address}
      </div>

      {/* Property Price */}
      <div 
        id={`property-price-${property.parcel_id}`}
        data-source-table="parcels"
        data-source-field="assessed_value"
        data-field-type="currency"
        data-transform="formatCurrency"
        data-calculation="none"
        className="text-2xl font-bold text-blue-600"
      >
        ${property.assessed_value?.toLocaleString() || 'N/A'}
      </div>

      {/* Owner Information */}
      <div 
        id={`property-owner-${property.parcel_id}`}
        data-source-table="parcels"
        data-source-field="owner_name"
        data-field-type="string"
        data-sensitive="true"
        data-permission-required="authenticated"
        className="text-sm text-gray-600"
      >
        Owner: {property.owner_name}
      </div>

      {/* Calculated Field */}
      <div 
        id={`property-tax-estimate-${property.parcel_id}`}
        data-source-table="parcels"
        data-source-fields="assessed_value,tax_rate"
        data-calculation="assessed_value * tax_rate"
        data-field-type="currency"
        data-derived="true"
        className="text-sm"
      >
        Est. Tax: ${calculateTax(property.assessed_value, property.tax_rate)}
      </div>

      {/* Related Data */}
      <div 
        id={`property-last-sale-${property.parcel_id}`}
        data-source-table="sales_history"
        data-source-field="sale_price"
        data-join="parcels.parcel_id = sales_history.parcel_id"
        data-filter="ORDER BY sale_date DESC LIMIT 1"
        data-field-type="currency"
        className="text-sm"
      >
        Last Sale: ${property.last_sale_price?.toLocaleString() || 'N/A'}
      </div>
    </div>
  );
};
```

## 4. Data Flow Tracking System

### Create a Data Flow Map

```typescript
// data-flow.config.ts
export const DATA_FLOW = {
  pages: {
    '/properties': {
      pageName: 'Properties Search',
      dataSources: [
        {
          table: 'parcels',
          fields: ['parcel_id', 'site_address', 'assessed_value', 'owner_name'],
          filters: 'dynamic',
          pagination: true,
          caching: '5min'
        }
      ],
      components: [
        {
          name: 'PropertySearchBar',
          receives: [],
          sends: ['search_query'],
          updates: ['search_results']
        },
        {
          name: 'PropertyList',
          receives: ['search_results'],
          sends: ['selected_property'],
          displays: ['parcel_id', 'site_address', 'assessed_value']
        }
      ]
    },
    '/property/:id': {
      pageName: 'Property Detail',
      dataSources: [
        {
          table: 'parcels',
          fields: '*',
          filters: 'parcel_id = :id',
          joins: [
            {
              table: 'sales_history',
              on: 'parcels.parcel_id = sales_history.parcel_id',
              fields: ['sale_date', 'sale_price']
            },
            {
              table: 'tax_assessments',
              on: 'parcels.parcel_id = tax_assessments.parcel_id',
              fields: ['tax_year', 'tax_amount']
            }
          ]
        }
      ]
    }
  }
};
```

## 5. Data Dictionary with UI Locations

```typescript
// data-dictionary.ts
export const DATA_DICTIONARY = {
  // Financial Fields
  assessed_value: {
    definition: "Current assessed value of the property",
    source: "parcels.assessed_value",
    type: "number",
    format: "currency",
    uiLocations: {
      pages: ['/property/:id', '/properties', '/dashboard'],
      components: ['PropertyCard', 'PropertyDetail', 'DashboardStats'],
      elementIds: [
        'property-price-display',
        'property-card-price',
        'dashboard-total-value'
      ]
    },
    relatedFields: ['taxable_value', 'market_value'],
    calculations: {
      'estimated_tax': 'assessed_value * 0.02',
      'price_per_sqft': 'assessed_value / total_square_feet'
    }
  },
  
  // Location Fields
  site_address: {
    definition: "Physical street address of the property",
    source: "parcels.site_address",
    type: "string",
    format: "address",
    uiLocations: {
      pages: ['/property/:id', '/properties', '/map'],
      components: ['PropertyCard', 'PropertyHeader', 'MapMarker'],
      elementIds: [
        'property-header-address',
        'search-result-address',
        'map-popup-address'
      ]
    },
    validation: {
      required: true,
      pattern: /^\d+\s+[\w\s]+$/
    },
    searchable: true,
    geocoded: true
  },
  
  // Ownership Fields
  owner_name: {
    definition: "Current owner(s) of the property",
    source: "parcels.owner_name",
    type: "string",
    format: "name",
    sensitive: true,
    uiLocations: {
      pages: ['/property/:id', '/ownership'],
      components: ['OwnershipCard', 'PropertyDetail'],
      elementIds: [
        'property-owner-section',
        'owner-details-card'
      ]
    },
    permissions: ['authenticated', 'admin'],
    relatedData: {
      'owner_history': 'ownership_history.previous_owners',
      'owner_properties': 'parcels WHERE owner_name = :owner_name'
    }
  }
};
```

## 6. Data Hooks with Tracking

```typescript
// hooks/useTrackedData.ts
export function useTrackedData(
  table: string, 
  field: string, 
  recordId?: string
) {
  const [data, setData] = useState(null);
  const [metadata, setMetadata] = useState({});

  useEffect(() => {
    // Track data access
    console.log(`[DATA ACCESS] Table: ${table}, Field: ${field}, ID: ${recordId}`);
    
    // Log to analytics
    trackDataAccess({
      table,
      field,
      recordId,
      component: getCurrentComponent(),
      timestamp: new Date().toISOString()
    });

    // Fetch data
    fetchData(table, field, recordId).then(result => {
      setData(result.data);
      setMetadata({
        source: `${table}.${field}`,
        fetchedAt: new Date().toISOString(),
        cacheStatus: result.fromCache ? 'hit' : 'miss'
      });
    });
  }, [table, field, recordId]);

  return { data, metadata };
}

// Usage in component
const PropertyPrice = ({ propertyId }) => {
  const { data: price, metadata } = useTrackedData(
    'parcels', 
    'assessed_value', 
    propertyId
  );

  return (
    <div
      data-source-table="parcels"
      data-source-field="assessed_value"
      data-fetch-time={metadata.fetchedAt}
      data-cache-status={metadata.cacheStatus}
    >
      ${price?.toLocaleString()}
    </div>
  );
};
```

## 7. Data Validation & Type Safety

```typescript
// types/data-mapping.types.ts
export interface DataFieldMapping {
  dbField: string;
  dbTable: string;
  uiField: string;
  uiComponent: string;
  transform?: (value: any) => any;
  validate?: (value: any) => boolean;
  required?: boolean;
  sensitive?: boolean;
}

// Zod schema for validation
import { z } from 'zod';

export const PropertyDataSchema = z.object({
  parcel_id: z.string().regex(/^\d{10}$/),
  assessed_value: z.number().min(0).max(999999999),
  site_address: z.string().min(1),
  owner_name: z.string().optional(),
  // ... other fields
});

// Type-safe data access
export function getPropertyField<T extends keyof Property>(
  property: Property,
  field: T
): Property[T] {
  // This will be type-safe and tracked
  console.log(`Accessing ${field} from property ${property.parcel_id}`);
  return property[field];
}
```

## 8. Debug Mode for Data Tracking

```typescript
// utils/data-debug.ts
export function enableDataDebugMode() {
  if (process.env.NODE_ENV === 'development') {
    // Add visual indicators to all data elements
    document.querySelectorAll('[data-source-table]').forEach(element => {
      element.addEventListener('mouseenter', (e) => {
        const target = e.target as HTMLElement;
        const tooltip = document.createElement('div');
        tooltip.className = 'data-debug-tooltip';
        tooltip.innerHTML = `
          <strong>Data Source:</strong><br/>
          Table: ${target.dataset.sourceTable}<br/>
          Field: ${target.dataset.sourceField}<br/>
          Type: ${target.dataset.fieldType}<br/>
          Transform: ${target.dataset.transform || 'none'}<br/>
          Last Updated: ${target.dataset.lastUpdated || 'unknown'}
        `;
        target.appendChild(tooltip);
      });
    });
  }
}
```

## 9. SQL Query Mapping

```sql
-- Create a view that shows UI mapping
CREATE VIEW ui_data_mapping AS
SELECT 
  'parcels' as table_name,
  column_name,
  data_type,
  CASE 
    WHEN column_name = 'parcel_id' THEN 'property-header-parcel-id, property-card-id'
    WHEN column_name = 'assessed_value' THEN 'property-price-display, dashboard-total-value'
    WHEN column_name = 'site_address' THEN 'property-header-address, search-result-address'
    -- ... more mappings
  END as ui_element_ids,
  CASE
    WHEN column_name LIKE '%_value' THEN 'currency'
    WHEN column_name LIKE '%_date' THEN 'date'
    ELSE 'string'
  END as display_format
FROM information_schema.columns
WHERE table_name IN ('parcels', 'sales_history', 'tax_assessments');
```

## 10. Implementation Checklist

### For Every New Component:
- [ ] Add unique ID to every div
- [ ] Add data-source-table attribute
- [ ] Add data-source-field attribute
- [ ] Add data-field-type attribute
- [ ] Document in DATA_MAPPING config
- [ ] Update DATA_DICTIONARY
- [ ] Add to DATA_FLOW map
- [ ] Implement validation
- [ ] Add error handling
- [ ] Include fallback values

### For Database Changes:
- [ ] Update DATA_MAPPING config
- [ ] Update affected component attributes
- [ ] Update validation schemas
- [ ] Test data flow
- [ ] Update documentation

## Benefits of This System:

1. **Precise Communication**: "The assessed_value from parcels table displays in property-price-display div"
2. **Easy Debugging**: Every element shows its data source
3. **Impact Analysis**: Know exactly what UI elements are affected by database changes
4. **Data Lineage**: Track data from source to display
5. **Type Safety**: Strongly typed data access
6. **Performance Monitoring**: Track which data is accessed most
7. **Security**: Clear permission requirements for sensitive data

## Example Communication:

"Update the property-price-display element that shows parcels.assessed_value to format as currency with 0 decimal places"

"The owner-details-card component needs to join parcels.owner_name with ownership_history.transfer_date"

"Add validation to all elements displaying parcels.assessed_value to ensure the value is between 0 and 10 million"