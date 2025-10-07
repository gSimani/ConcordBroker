import { useState, useEffect } from 'react';

export interface NAVAssessment {
  levy_description_code: string;
  function_code: string;
  assessment_description: string;
  assessment_amount: number;
  county_code: number;
  county_name: string;
}

export interface NAVSummary {
  parcel_id: string;
  county_code: number;
  county_name: string;
  assessment_count: number;
  total_assessments: number;
  tax_year: number;
  assessments: NAVAssessment[];
}

interface UseNAVAssessmentsReturn {
  navData: NAVSummary | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

const API_BASE_URL = 'http://localhost:8005';

export function useNAVAssessments(parcelId: string): UseNAVAssessmentsReturn {
  const [navData, setNavData] = useState<NAVSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    if (!parcelId || parcelId === 'TEST-NO-VALUE') {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/nav-assessments/${encodeURIComponent(parcelId)}`);

      if (response.ok) {
        const result = await response.json();
        setNavData(result);
      } else if (response.status === 404) {
        // No NAV data found - this is normal for many properties
        setNavData(null);
      } else {
        setError(`Failed to fetch NAV data: ${response.status}`);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      console.error('Error fetching NAV assessments:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [parcelId]);

  return {
    navData,
    isLoading,
    error,
    refetch: fetchData
  };
}

// Hook for getting available counties
interface UseNAVCountiesReturn {
  counties: Array<{
    county_code: number;
    county_name: string;
    parcel_count: number;
  }>;
  isLoading: boolean;
  error: string | null;
}

export function useNAVAvailableCounties(): UseNAVCountiesReturn {
  const [counties, setCounties] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCounties = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(`${API_BASE_URL}/api/nav-available-counties`);

        if (response.ok) {
          const result = await response.json();
          setCounties(result);
        } else {
          setError(`Failed to fetch counties: ${response.status}`);
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMessage);
        console.error('Error fetching NAV counties:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCounties();
  }, []);

  return { counties, isLoading, error };
}

// Utility functions for formatting NAV data
export const formatNAVAmount = (amount: number): string => {
  if (amount >= 1000) {
    return `$${(amount / 1000).toFixed(1)}K`;
  }
  return `$${amount.toFixed(2)}`;
};

export const getNAVAssessmentIcon = (assessmentType: string): string => {
  const type = assessmentType.toUpperCase();

  if (type.includes('STORMWATER') || type.includes('DRAINAGE')) return '🌊';
  if (type.includes('FIRE')) return '🚒';
  if (type.includes('WASTE') || type.includes('GARBAGE')) return '🗑️';
  if (type.includes('STREET') || type.includes('LIGHT')) return '💡';
  if (type.includes('ROAD') || type.includes('TRANSPORTATION')) return '🛣️';
  if (type.includes('LIBRARY')) return '📚';
  if (type.includes('PARK') || type.includes('RECREATION')) return '🌳';
  if (type.includes('SECURITY')) return '🔒';

  return '🏛️'; // Generic government service
};

export const getNAVAssessmentColor = (assessmentType: string): string => {
  const type = assessmentType.toUpperCase();

  if (type.includes('STORMWATER') || type.includes('DRAINAGE')) return 'text-blue-600';
  if (type.includes('FIRE')) return 'text-red-600';
  if (type.includes('WASTE') || type.includes('GARBAGE')) return 'text-gray-600';
  if (type.includes('STREET') || type.includes('LIGHT')) return 'text-yellow-600';
  if (type.includes('ROAD') || type.includes('TRANSPORTATION')) return 'text-stone-600';
  if (type.includes('LIBRARY')) return 'text-purple-600';
  if (type.includes('PARK') || type.includes('RECREATION')) return 'text-green-600';
  if (type.includes('SECURITY')) return 'text-indigo-600';

  return 'text-slate-600'; // Default
};