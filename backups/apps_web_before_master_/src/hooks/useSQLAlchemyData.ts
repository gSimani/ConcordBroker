/**
 * Hook for SQLAlchemy Data Service Integration
 * Connects React frontend to our FastAPI SQLAlchemy data service
 */

import { useState, useEffect } from 'react';

export interface PropertyData {
  parcel_id: string;
  address: string;
  city: string;
  county: string;
  state: string;
  zip_code: string;
  property_type: string;
  year_built?: number;
  bedrooms?: number;
  bathrooms?: number;
  square_feet?: number;
  lot_size?: number;
  just_value?: number;
  land_value?: number;
  building_value?: number;
  assessed_value?: number;
  market_value?: number;
  ownership_type?: string;
  deed_type?: string;
  use_code?: string;
  zoning?: string;
  flood_zone?: string;
}

export interface SalesRecord {
  sale_date?: string;
  sale_price?: number;
  sale_type?: string;
  deed_type?: string;
  buyer_name?: string;
  seller_name?: string;
  financing_type?: string;
  verified?: boolean;
}

export interface TaxRecord {
  tax_year: number;
  assessed_value?: number;
  millage_rate?: number;
  total_taxes?: number;
  homestead_exemption?: number;
  tax_status?: string;
  due_date?: string;
  paid_date?: string;
}

export interface OwnerInfo {
  owner_name?: string;
  owner_address?: string;
  owner_city?: string;
  owner_state?: string;
  owner_zip?: string;
  mailing_address?: string;
  ownership_type?: string;
  percentage_owned?: number;
}

export interface PermitRecord {
  permit_number?: string;
  permit_type?: string;
  permit_description?: string;
  issue_date?: string;
  completion_date?: string;
  permit_value?: number;
  contractor_name?: string;
  permit_status?: string;
}

export interface PropertyAnalytics {
  price_per_sqft?: number;
  land_value_per_acre?: number;
  appreciation_rate?: number;
  total_sales?: number;
  average_sale_price?: number;
  annual_taxes?: number;
  tax_rate_percentage?: number;
  estimated_monthly_rent?: number;
  estimated_annual_rent?: number;
  estimated_net_income?: number;
  cap_rate?: number;
  gross_yield?: number;
  market_position?: string;
  investment_grade?: string;
  risk_factors?: string[];
  risk_score?: number;
  property_age?: number;
}

export interface CompletePropertyData {
  property: PropertyData;
  sales_history: SalesRecord[];
  tax_data: TaxRecord[];
  owner_info: OwnerInfo | null;
  permits: PermitRecord[];
  analytics: PropertyAnalytics;
  timestamp: string;
}

const DATA_SERVICE_BASE_URL = 'http://localhost:8004';

export function useSQLAlchemyPropertyData(parcelId: string) {
  const [data, setData] = useState<CompletePropertyData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!parcelId) {
      setData(null);
      setLoading(false);
      return;
    }

    const fetchPropertyData = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(`${DATA_SERVICE_BASE_URL}/api/property/${parcelId}`);

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const propertyData: CompletePropertyData = await response.json();
        setData(propertyData);
      } catch (err) {
        console.error('Error fetching property data:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch property data');
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchPropertyData();
  }, [parcelId]);

  return { data, loading, error, refetch: () => setLoading(true) };
}

export function useSQLAlchemyAnalytics(parcelId: string) {
  const [analytics, setAnalytics] = useState<PropertyAnalytics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!parcelId) {
      setAnalytics(null);
      setLoading(false);
      return;
    }

    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(`${DATA_SERVICE_BASE_URL}/api/property/${parcelId}/analytics`);

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const analyticsData = await response.json();
        setAnalytics(analyticsData.analytics);
      } catch (err) {
        console.error('Error fetching analytics:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch analytics');
        setAnalytics(null);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, [parcelId]);

  return { analytics, loading, error };
}

export function useDataServiceHealth() {
  const [healthy, setHealthy] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${DATA_SERVICE_BASE_URL}/health`);
        setHealthy(response.ok);
      } catch (err) {
        setHealthy(false);
      } finally {
        setLoading(false);
      }
    };

    checkHealth();

    // Check health every 30 seconds
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return { healthy, loading };
}

// Helper function to format currency
export function formatCurrency(amount?: number): string {
  if (amount === undefined || amount === null) return 'N/A';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

// Helper function to format date
export function formatDate(date?: string): string {
  if (!date) return 'N/A';
  try {
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return date;
  }
}

// Helper function to calculate NumPy-style statistics
export function calculateStatistics(values: number[]): {
  mean: number;
  median: number;
  std: number;
  min: number;
  max: number;
  percentile_25: number;
  percentile_75: number;
} {
  if (values.length === 0) {
    return { mean: 0, median: 0, std: 0, min: 0, max: 0, percentile_25: 0, percentile_75: 0 };
  }

  const sorted = [...values].sort((a, b) => a - b);
  const n = values.length;

  // Mean
  const mean = values.reduce((sum, val) => sum + val, 0) / n;

  // Median
  const median = n % 2 === 0
    ? (sorted[n / 2 - 1] + sorted[n / 2]) / 2
    : sorted[Math.floor(n / 2)];

  // Standard deviation
  const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / n;
  const std = Math.sqrt(variance);

  // Min/Max
  const min = Math.min(...values);
  const max = Math.max(...values);

  // Percentiles
  const percentile_25 = sorted[Math.floor(n * 0.25)];
  const percentile_75 = sorted[Math.floor(n * 0.75)];

  return { mean, median, std, min, max, percentile_25, percentile_75 };
}