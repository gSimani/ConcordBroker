import { useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL || '',
  import.meta.env.VITE_SUPABASE_ANON_KEY || ''
);

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

export function useOwnerProperties(ownerName: string, currentParcelId?: string) {
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
        console.log('Fetching properties for owner:', ownerName);

        // Search for properties by owner name with fuzzy matching
        const { data: properties, error: propertiesError } = await supabase
          .from('florida_parcels')
          .select(`
            parcel_id,
            phy_addr1,
            phy_city,
            phy_zipcd,
            own_name,
            jv,
            dor_uc,
            lnd_val,
            tot_lvg_area,
            lnd_sqfoot,
            act_yr_blt,
            sale_prc1,
            sale_yr1,
            sale_mo1,
            av_sd,
            tv_sd
          `)
          .ilike('own_name', `%${ownerName.trim()}%`)
          .not('parcel_id', 'eq', currentParcelId || '') // Exclude current property
          .order('jv', { ascending: false }) // Order by market value descending
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
            owner_name: prop.own_name || '',
            market_value: prop.jv || 0,
            property_use_code: prop.dor_uc || '',
            land_value: prop.lnd_val || 0,
            building_value: (prop.jv || 0) - (prop.lnd_val || 0),
            just_value: prop.jv || 0,
            assessed_value: prop.av_sd || 0,
            taxable_value: prop.tv_sd || 0,
            living_area: prop.tot_lvg_area || 0,
            lot_size_sqft: prop.lnd_sqfoot || 0,
            year_built: prop.act_yr_blt || 0,
            sale_price: prop.sale_prc1 || 0,
            sale_date: prop.sale_yr1 && prop.sale_mo1
              ? `${prop.sale_yr1}-${String(prop.sale_mo1).padStart(2, '0')}-01`
              : ''
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
  }, [ownerName, currentParcelId]);

  return {
    ownerProperties,
    loading,
    error,
    hasMultipleProperties: ownerProperties.length > 0
  };
}