import { useState, useCallback } from 'react';
import { supabase } from '@/lib/supabase';
import { debounce } from 'lodash';

export interface PropertySuggestion {
  id: string;
  address: string;
  city: string;
  county: string;
  zipCode: string;
  type: 'property' | 'owner' | 'city';
  parcelId?: string;
  owner?: string;
  value?: number;
  matchScore: number;
}

export function usePropertyAutocomplete() {
  const [suggestions, setSuggestions] = useState<PropertySuggestion[]>([]);
  const [loading, setLoading] = useState(false);

  const searchProperties = useCallback(
    debounce(async (searchTerm: string) => {
      if (!searchTerm || searchTerm.length < 3) {
        setSuggestions([]);
        return;
      }

      setLoading(true);
      try {
        const term = searchTerm.toLowerCase().trim();

        // Search across multiple fields in florida_parcels
        const { data, error } = await supabase
          .from('florida_parcels')
          .select('parcel_id,phy_addr1,phy_city,phy_zipcd,county,owner_name,just_value')
          .or(`phy_addr1.ilike.%${term}%,phy_city.ilike.%${term}%,owner_name.ilike.%${term}%`)
          .eq('is_redacted', false)
          .gt('just_value', 0)
          .limit(15);

        if (error) throw error;

        // Transform results into suggestions
        const suggestions: PropertySuggestion[] = (data || []).map((prop, index) => {
          // Determine match type and score
          let type: 'property' | 'owner' | 'city' = 'property';
          let matchScore = 0.5;

          const addr = prop.phy_addr1?.toLowerCase() || '';
          const city = prop.phy_city?.toLowerCase() || '';
          const owner = prop.owner_name?.toLowerCase() || '';

          if (addr.startsWith(term)) {
            type = 'property';
            matchScore = 0.95;
          } else if (addr.includes(term)) {
            type = 'property';
            matchScore = 0.85;
          } else if (owner.includes(term)) {
            type = 'owner';
            matchScore = 0.75;
          } else if (city.startsWith(term)) {
            type = 'city';
            matchScore = 0.65;
          } else if (city.includes(term)) {
            type = 'city';
            matchScore = 0.55;
          }

          // Boost score for exact matches
          if (addr === term) matchScore = 1.0;
          if (owner === term) matchScore = 0.95;
          if (city === term) matchScore = 0.90;

          return {
            id: `${prop.parcel_id}-${index}`,
            address: prop.phy_addr1 || 'Address not available',
            city: prop.phy_city || '',
            county: prop.county || '',
            zipCode: prop.phy_zipcd || '',
            type,
            parcelId: prop.parcel_id,
            owner: prop.owner_name || undefined,
            value: prop.just_value || undefined,
            matchScore
          };
        });

        // Sort by match score (highest first)
        suggestions.sort((a, b) => b.matchScore - a.matchScore);

        setSuggestions(suggestions);
      } catch (error) {
        console.error('Error fetching autocomplete suggestions:', error);
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    }, 300),
    []
  );

  return {
    suggestions,
    loading,
    searchProperties
  };
}
