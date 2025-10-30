import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';

interface OwnerProperty {
  parcel_id: string;
  property_address_street: string;
  property_address_city: string;
  property_address_zip: string;
  owner_name: string;
  market_value: number;
  property_use_code: string;
  land_value: number;
  building_value: number;
  just_value: number;
  assessed_value: number;
  taxable_value: number;
  living_area: number;
  lot_size_sqft: number;
  year_built: number;
  sale_price: number;
  sale_date: string;
}

export function useOwnerProperties(ownerName: string, currentParcelId?: string, county: string = 'BROWARD') {
  const [ownerProperties, setOwnerProperties] = useState<OwnerProperty[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOwnerProperties = async () => {
      if (!ownerName || ownerName.trim() === '') {
        setOwnerProperties([]);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        console.log('Fetching properties for owner:', ownerName, 'in county:', county);

        // Clean and uppercase the search query for prefix matching
        const cleanOwnerName = ownerName.trim().toUpperCase();

        // Search for properties by owner name with prefix matching (uses idx_fp_owner_county_value)
        const { data: properties, error: propertiesError } = await supabase
          .from('florida_parcels')
          .select(`
            parcel_id,
            phy_addr1,
            phy_city,
            phy_zipcd,
            owner_name,
            just_value,
            property_use,
            land_value,
            total_living_area,
            land_sqft,
            year_built,
            sale_price,
            sale_date,
            assessed_value,
            taxable_value
          `)
          .eq('county', county.toUpperCase()) // Filter by county first for index usage
          .ilike('owner_name', `${cleanOwnerName}%`) // Prefix match instead of wildcard
          .not('parcel_id', 'eq', currentParcelId || '') // Exclude current property
          .order('just_value', { ascending: false }) // Order by market value descending
          .limit(20); // Limit to 20 properties to avoid overwhelming UI

        if (propertiesError) {
          console.error('Error fetching owner properties:', propertiesError);
          setError('Failed to fetch owner properties');
          return;
        }

        console.log('Found properties for owner:', properties?.length || 0);

        if (properties && properties.length > 0) {
          // Transform the data to match our interface
          const transformedProperties: OwnerProperty[] = properties.map(prop => ({
            parcel_id: prop.parcel_id || '',
            property_address_street: prop.phy_addr1 || '',
            property_address_city: prop.phy_city || '',
            property_address_zip: prop.phy_zipcd || '',
            owner_name: prop.owner_name || '',
            market_value: prop.just_value || 0,
            property_use_code: prop.property_use || '',
            land_value: prop.land_value || 0,
            building_value: (prop.just_value || 0) - (prop.land_value || 0),
            just_value: prop.just_value || 0,
            assessed_value: prop.assessed_value || 0,
            taxable_value: prop.taxable_value || 0,
            living_area: prop.total_living_area || 0,
            lot_size_sqft: prop.land_sqft || 0,
            year_built: prop.year_built || 0,
            sale_price: prop.sale_price || 0,
            sale_date: prop.sale_date || ''
          }));

          setOwnerProperties(transformedProperties);
        } else {
          setOwnerProperties([]);
        }

      } catch (err) {
        console.error('Error in fetchOwnerProperties:', err);
        setError('An unexpected error occurred');
        setOwnerProperties([]);
      } finally {
        setLoading(false);
      }
    };

    fetchOwnerProperties();
  }, [ownerName, currentParcelId, county]);

  return {
    ownerProperties,
    loading,
    error,
    hasMultipleProperties: ownerProperties.length > 0
  };
}
