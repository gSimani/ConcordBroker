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
      // Dynamic county filter - defaults to BROWARD for backward compatibility and performance
      const targetCounty = (county || 'BROWARD').toUpperCase().replace(/\s+/g, '_');

      // RUN QUERIES IN PARALLEL for maximum speed
      // Counties use static list for instant results (no database query needed)
      const [addressResult, ownerResult, cityResult] = await Promise.allSettled([
        // Query 1: Search addresses (prefix match for performance)
        supabase
          .from('florida_parcels')
          .select('phy_addr1, phy_city, phy_zipcd, owner_name, property_use, just_value, parcel_id')
          .eq('county', targetCounty)
          .ilike('phy_addr1', `${cleanQuery}%`)
          .not('phy_addr1', 'is', null)
          .limit(5)
          .order('phy_addr1'),

        // Query 2: Search owner names (prefix match for performance)
        supabase
          .from('florida_parcels')
          .select('owner_name, phy_addr1, phy_city, phy_zipcd, property_use, just_value, parcel_id')
          .eq('county', targetCounty)
          .ilike('owner_name', `${cleanQuery}%`)
          .not('owner_name', 'is', null)
          .limit(5)
          .order('owner_name'),

        // Query 3: Search cities (if query looks like a city name)
        cleanQuery.length >= 3 && !/^\d/.test(cleanQuery)
          ? supabase
              .from('florida_parcels')
              .select('phy_city')
              .eq('county', targetCounty)
              .ilike('phy_city', `${cleanQuery}%`)
              .not('phy_city', 'is', null)
              .limit(3)
          : Promise.resolve({ data: [], error: null })
      ]);

      // Query 4: Counties (instant static search - no database query)
      const matchingCounties = cleanQuery.length >= 3 && !/^\d/.test(cleanQuery)
        ? searchCounties(cleanQuery, 5)
        : [];

      const allSuggestions: Suggestion[] = [];

      // Process address results
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

      // Process owner results (with deduplication)
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

      // Process city results
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

      // Process county results (instant static search)
      matchingCounties.forEach(county => {
        allSuggestions.push({
          type: 'county',
          display: getCountyDisplayName(county),
          value: county,
          metadata: {}
        });
      });

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
