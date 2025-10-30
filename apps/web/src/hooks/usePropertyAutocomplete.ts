import { useState, useCallback } from 'react';
import { supabase } from '@/lib/supabase';
import { getDorCodeFromPropertyUse, getPropertyUseDescription } from '@/lib/propertyUseToDorCode';
import { searchCounties, getCountyDisplayName } from '@/lib/floridaCounties';

/**
 * Property Autocomplete Hook
 * Provides real-time Supabase-powered autocomplete with:
 * - Property addresses with icons based on property type (DOR codes)
 * - Owner names
 * - City, zip code, and property metadata
 * - USE and SUBUSE descriptions
 */

interface Suggestion {
  type: 'address' | 'owner' | 'city' | 'county';
  display: string;
  value: string;
  property_type?: string;  // DOR code (converted from property_use)
  metadata?: {
    city?: string;
    zip_code?: string;
    owner_name?: string;
    just_value?: number;
    parcel_id?: string;
    property_use?: string;      // Original property_use text code
    property_use_desc?: string; // Human-readable description
  };
}

export function usePropertyAutocomplete(county?: string) {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [loading, setLoading] = useState(false);

  const searchProperties = useCallback(async (query: string) => {
    if (!query || query.length < 2) {
      setSuggestions([]);
      return;
    }

    setLoading(true);
    try {
      const cleanQuery = query.trim().toUpperCase();

      // FIXED: Only apply county filter if one is actually selected
      // If no county selected, search across ALL counties for better autocomplete
      const hasCountyFilter = county && county.trim() !== '';
      const targetCounty = hasCountyFilter ? county.toUpperCase().replace(/\s+/g, '_') : null;

      // Build query builders with conditional county filter
      const buildAddressQuery = () => {
        let q = supabase
          .from('florida_parcels')
          .select('phy_addr1, phy_city, phy_zipcd, owner_name, property_use, just_value, parcel_id, county')
          .ilike('phy_addr1', `${cleanQuery}%`)
          .not('phy_addr1', 'is', null)
          .limit(5)
          .order('phy_addr1');

        if (targetCounty) q = q.eq('county', targetCounty);
        return q;
      };

      const buildOwnerQuery = () => {
        let q = supabase
          .from('florida_parcels')
          .select('owner_name, phy_addr1, phy_city, phy_zipcd, property_use, just_value, parcel_id, county')
          .ilike('owner_name', `${cleanQuery}%`)
          .not('owner_name', 'is', null)
          .limit(5)
          .order('owner_name');

        if (targetCounty) q = q.eq('county', targetCounty);
        return q;
      };

      const buildCityQuery = () => {
        if (cleanQuery.length < 3 || /^\d/.test(cleanQuery)) {
          return Promise.resolve({ data: [], error: null });
        }

        let q = supabase
          .from('florida_parcels')
          .select('phy_city, county')
          .ilike('phy_city', `${cleanQuery}%`)
          .not('phy_city', 'is', null)
          .limit(3);

        if (targetCounty) q = q.eq('county', targetCounty);
        return q;
      };

      // RUN QUERIES IN PARALLEL for maximum speed
      // Counties use static list for instant results (no database query needed)
      const [addressResult, ownerResult, cityResult] = await Promise.allSettled([
        buildAddressQuery(),
        buildOwnerQuery(),
        buildCityQuery()
      ]);

      // Query 4: Counties (instant static search - ALWAYS search all counties)
      const matchingCounties = cleanQuery.length >= 2 && !/^\d/.test(cleanQuery)
        ? searchCounties(cleanQuery, 5)
        : [];

      const allSuggestions: Suggestion[] = [];

      // PRIORITY 1: Process county results FIRST (instant static search)
      // Counties appear at the top when user types county names
      matchingCounties.forEach(county => {
        allSuggestions.push({
          type: 'county',
          display: getCountyDisplayName(county),
          value: county,
          metadata: {}
        });
      });

      // PRIORITY 2: Process city results (location filter)
      // Cities appear high in suggestions for location-based searches
      if (cityResult.status === 'fulfilled' && cityResult.value.data) {
        const uniqueCities = [...new Set(cityResult.value.data.map(p => p.phy_city))];
        uniqueCities.forEach(city => {
          if (city) {
            allSuggestions.push({
              type: 'city',
              display: city,
              value: city,
              metadata: {
                city: city
              }
            });
          }
        });
      }

      // PRIORITY 3: Process address results
      if (addressResult.status === 'fulfilled' && addressResult.value.data) {
        addressResult.value.data.forEach((prop) => {
          // Convert property_use text code (e.g., "SFR") to DOR code (e.g., "0100") for icon mapping
          const dorCode = getDorCodeFromPropertyUse(prop.property_use);
          const useDescription = getPropertyUseDescription(prop.property_use);

          allSuggestions.push({
            type: 'address',
            display: prop.phy_addr1 || '',
            value: prop.phy_addr1 || '',
            property_type: dorCode,  // DOR code for icon mapping (e.g., "0100")
            metadata: {
              city: prop.phy_city || '',
              zip_code: prop.phy_zipcd || '',
              owner_name: prop.owner_name || '',
              just_value: prop.just_value,
              parcel_id: prop.parcel_id,
              property_use: prop.property_use,        // Original text code (e.g., "SFR")
              property_use_desc: useDescription        // Human-readable (e.g., "Single Family")
            }
          });
        });
      }

      // PRIORITY 4: Process owner results (with deduplication)
      if (ownerResult.status === 'fulfilled' && ownerResult.value.data) {
        const uniqueOwners = new Map<string, typeof ownerResult.value.data[0]>();
        ownerResult.value.data.forEach(prop => {
          if (prop.owner_name && !uniqueOwners.has(prop.owner_name)) {
            uniqueOwners.set(prop.owner_name, prop);
          }
        });

        uniqueOwners.forEach((prop, ownerName) => {
          // Convert property_use text code to DOR code for icon mapping
          const dorCode = getDorCodeFromPropertyUse(prop.property_use);
          const useDescription = getPropertyUseDescription(prop.property_use);

          allSuggestions.push({
            type: 'owner',
            display: ownerName,
            value: ownerName,
            property_type: dorCode,  // DOR code for icon mapping
            metadata: {
              city: prop.phy_city || '',
              zip_code: prop.phy_zipcd || '',
              owner_name: ownerName,
              just_value: prop.just_value,
              parcel_id: prop.parcel_id,
              property_use: prop.property_use,        // Original text code
              property_use_desc: useDescription        // Human-readable
            }
          });
        });
      }

      setSuggestions(allSuggestions);
    } catch (error) {
      console.error('Autocomplete error:', error);
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  }, [county]);

  return {
    suggestions,
    loading,
    searchProperties
  };
}
