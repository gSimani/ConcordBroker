import { useState, useEffect } from 'react';

interface SalesData {
  has_sales: boolean;
  last_sale_price?: number;
  last_sale_date?: string;
  total_sales: number;
  price_trend?: string;
  appreciation?: number;
  quick_insight?: string;
}

interface AIAnalysis {
  investment_score?: number;
  investment_grade?: string;
  price_trend?: {
    trend?: string;
    trend_emoji?: string;
    total_appreciation?: number;
    annual_appreciation?: number;
  };
  market_activity?: {
    activity_level?: string;
    activity_emoji?: string;
    total_transactions?: number;
  };
  investment_insights?: {
    insights?: string[];
    recommendations?: string[];
    risk_factors?: string[];
    ai_summary?: string;
  };
}

interface UseAISalesHistoryReturn {
  salesData: SalesData | null;
  aiAnalysis: AIAnalysis | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

const API_BASE_URL = 'http://localhost:8004';

export function useAISalesHistory(parcelId: string, enableAI: boolean = true): UseAISalesHistoryReturn {
  const [salesData, setSalesData] = useState<SalesData | null>(null);
  const [aiAnalysis, setAIAnalysis] = useState<AIAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    if (!parcelId || parcelId === 'TEST-NO-VALUE') {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Fetch mini card sales data
      const salesResponse = await fetch(`${API_BASE_URL}/api/mini-card-data/${parcelId}`);

      if (salesResponse.ok) {
        const salesResult = await salesResponse.json();
        if (salesResult.success) {
          setSalesData(salesResult.mini_card_data);
        } else {
          console.warn('Sales data fetch unsuccessful:', salesResult);
        }
      } else {
        console.warn('Sales data response not ok:', salesResponse.status);
      }

      // If AI analysis is enabled, fetch it
      if (enableAI) {
        const analysisResponse = await fetch(`${API_BASE_URL}/api/sales-analysis/${parcelId}`);

        if (analysisResponse.ok) {
          const analysisResult = await analysisResponse.json();
          if (analysisResult.success) {
            setAIAnalysis(analysisResult.analysis);
          } else {
            console.warn('AI analysis fetch unsuccessful:', analysisResult);
          }
        } else {
          console.warn('AI analysis response not ok:', analysisResponse.status);
        }
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      console.error('Error fetching sales history:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [parcelId, enableAI]);

  return {
    salesData,
    aiAnalysis,
    isLoading,
    error,
    refetch: fetchData
  };
}

// Hook for batch fetching multiple properties (for performance)
export function useBatchSalesHistory(parcelIds: string[]): {
  batchData: Record<string, SalesData>;
  isLoading: boolean;
  error: string | null;
} {
  const [batchData, setBatchData] = useState<Record<string, SalesData>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!parcelIds.length) return;

    const fetchBatchData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const idsString = parcelIds.filter(id => id && id !== 'TEST-NO-VALUE').join(',');
        if (!idsString) return;

        const response = await fetch(`${API_BASE_URL}/api/batch-mini-cards?parcel_ids=${encodeURIComponent(idsString)}`);

        if (response.ok) {
          const result = await response.json();
          if (result.success) {
            setBatchData(result.data);
          }
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMessage);
        console.error('Error fetching batch sales data:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchBatchData();
  }, [parcelIds.join(',')]);

  return { batchData, isLoading, error };
}

// Utility functions for formatting
export const formatCurrency = (value?: number): string => {
  if (!value) return 'N/A';
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(2)}M`;
  }
  if (value >= 1000) {
    return `$${Math.round(value / 1000)}K`;
  }
  return `$${value.toLocaleString()}`;
};

export const formatDate = (dateStr?: string): string => {
  if (!dateStr) return 'N/A';
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
  } catch {
    return dateStr;
  }
};

export const getAppreciationColor = (appreciation?: number): string => {
  if (!appreciation) return 'text-muted-foreground';
  if (appreciation > 0) return 'text-green-600';
  return 'text-red-600';
};

export const getInvestmentGradeColor = (grade?: string): string => {
  if (!grade) return 'bg-gray-500';
  const letter = grade.charAt(0);
  switch (letter) {
    case 'A': return 'bg-green-600';
    case 'B': return 'bg-blue-600';
    case 'C': return 'bg-yellow-600';
    case 'D': return 'bg-orange-600';
    case 'F': return 'bg-red-600';
    default: return 'bg-gray-500';
  }
};