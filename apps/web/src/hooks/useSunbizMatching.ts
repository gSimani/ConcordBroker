import { useState, useEffect } from 'react';

interface SunbizMatch {
  entity_id: string;
  company_name: string;
  entity_type: string;
  status: string;
  match_type: string;
  confidence: number;
  authorized_persons: Array<{
    name: string;
    title: string;
  }>;
  principal_address?: string;
  filing_date?: string;
  registered_agent?: string;
}

interface SunbizMatchResponse {
  success: boolean;
  parcel_id: string;
  owner_name: string;
  parsed_names: string[];
  is_company: boolean;
  matches: SunbizMatch[];
  total_matches: number;
  best_match: SunbizMatch | null;
}

export function useSunbizMatching(parcelId: string, ownerName?: string) {
  const [matchData, setMatchData] = useState<SunbizMatchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!parcelId || !ownerName) return;

    const fetchSunbizMatches = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `http://localhost:8002/api/sunbiz/match/${encodeURIComponent(parcelId)}`,
          {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
            },
          }
        );

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data: SunbizMatchResponse = await response.json();

        if (data.success) {
          setMatchData(data);
        } else {
          throw new Error('Failed to fetch Sunbiz matches');
        }
      } catch (err) {
        console.error('Error fetching Sunbiz matches:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
        setMatchData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchSunbizMatches();
  }, [parcelId, ownerName]);

  return {
    matchData,
    bestMatch: matchData?.best_match || null,
    allMatches: matchData?.matches || [],
    totalMatches: matchData?.total_matches || 0,
    loading,
    error,
    hasMatches: (matchData?.total_matches || 0) > 0,
    isCompany: matchData?.is_company || false,
  };
}

export function getSunbizSearchUrl(ownerName: string, bestMatch?: SunbizMatch | null): string {
  if (bestMatch) {
    // Use the matched company name for more accurate search
    const searchName = bestMatch.company_name
      .replace(/LLC$|INC$|CORP$|LP$|LLP$/i, '')
      .trim();
    return `https://search.sunbiz.org/Inquiry/CorporationSearch/SearchResults?inquiryType=EntityName&searchNameOrder=&searchTerm=${encodeURIComponent(searchName)}`;
  }

  // Fallback to original owner name
  const searchName = ownerName
    .replace(/LLC$|INC$|CORP$|LP$|LLP$/i, '')
    .trim();
  return `https://search.sunbiz.org/Inquiry/CorporationSearch/SearchResults?inquiryType=EntityName&searchNameOrder=&searchTerm=${encodeURIComponent(searchName)}`;
}