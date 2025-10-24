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

// Track service availability to avoid repeated failed requests
let serviceAvailable = true;
let lastServiceCheck = 0;
const SERVICE_CHECK_INTERVAL = 60000; // Check every 60 seconds

export function useSunbizMatching(parcelId: string, ownerName?: string) {
  const [matchData, setMatchData] = useState<SunbizMatchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!parcelId || !ownerName) return;

    // Skip if service is known to be unavailable (avoid console spam)
    const now = Date.now();
    if (!serviceAvailable && (now - lastServiceCheck) < SERVICE_CHECK_INTERVAL) {
      setError('Sunbiz service unavailable');
      return;
    }

    const fetchSunbizMatches = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `http://localhost:8003/api/sunbiz/match?owner_name=${encodeURIComponent(ownerName)}`,
          {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
            },
            signal: AbortSignal.timeout(5000), // 5 second timeout
          }
        );

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Adapt the API response to our expected format
        if (data.success && data.match) {
          const adaptedData: SunbizMatchResponse = {
            success: true,
            parcel_id: parcelId,
            owner_name: ownerName,
            parsed_names: [ownerName],
            is_company: true,
            matches: [data.match],
            total_matches: 1,
            best_match: data.match
          };
          setMatchData(adaptedData);
          serviceAvailable = true; // Service is working
        } else {
          // No match found, but service is working
          setMatchData({
            success: true,
            parcel_id: parcelId,
            owner_name: ownerName,
            parsed_names: [ownerName],
            is_company: false,
            matches: [],
            total_matches: 0,
            best_match: null
          });
          serviceAvailable = true;
        }
      } catch (err) {
        // Check if it's a connection error (service not running)
        // Covers: TypeError (Failed to fetch), ERR_CONNECTION_REFUSED, TimeoutError
        const isConnectionError =
          (err instanceof TypeError && err.message.includes('fetch')) ||
          (err instanceof Error && (
            err.message.includes('ERR_CONNECTION_REFUSED') ||
            err.message.includes('ECONNREFUSED') ||
            err.message.includes('timed out') ||
            err.name === 'TimeoutError' ||
            err.message.includes('NetworkError')
          ));

        if (isConnectionError) {
          // Only log warning once when service first goes down
          if (serviceAvailable) {
            console.warn('⚠️ Sunbiz matching service unavailable (port 8003). Features will be limited.');
          }
          serviceAvailable = false;
          lastServiceCheck = Date.now();
          setError('Service unavailable');
        } else {
          // Log other errors normally (not connection issues)
          console.error('Error fetching Sunbiz matches:', err);
          setError(err instanceof Error ? err.message : 'Unknown error');
        }
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