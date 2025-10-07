import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';

export interface TaxAssessmentData {
  parcel_id: string;
  year: number;
  just_value: number;
  assessed_value: number;
  taxable_value: number;
  land_value: number;
  building_value: number;
  homestead_exemption: number;
  other_exemptions: number;
  tax_amount: number;
  county: string;
}

export interface NavAssessment {
  parcel_id: string;
  authority_name: string;
  district_name: string;
  total_assessment: number;
  assessment_year: number;
  bond_debt: number;
  annual_payment: number;
  remaining_years: number;
  is_cdd: boolean;
}

export interface TaxCertificate {
  parcel_id: string;
  certificate_number: string;
  certificate_date: string;
  tax_year: number;
  amount_due: number;
  status: string;
  auction_date?: string;
  sold_to?: string;
}

export interface PropertyTaxInfo {
  parcel_id: string;
  current_assessment: TaxAssessmentData | null;
  historical_assessments: TaxAssessmentData[];
  nav_assessments: NavAssessment[];
  tax_certificates: TaxCertificate[];
  total_nav_assessment: number;
  is_in_cdd: boolean;
  estimated_annual_taxes: number;
  effective_tax_rate: number;
  tax_history_trend: 'increasing' | 'decreasing' | 'stable';
  payment_status: 'current' | 'delinquent' | 'certificate_sold';
  risk_factors: string[];
}

export function usePropertyTaxInfo(parcelId: string | null) {
  const [taxInfo, setTaxInfo] = useState<PropertyTaxInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!parcelId) {
      setTaxInfo(null);
      return;
    }

    fetchTaxInfo(parcelId);
  }, [parcelId]);

  const fetchTaxInfo = async (parcelId: string) => {
    setLoading(true);
    setError(null);

    try {
      console.log(`[usePropertyTaxInfo] Fetching tax data for parcel: ${parcelId}`);

      // Fetch data from multiple sources in parallel
      const [
        currentAssessmentResult,
        historicalAssessmentsResult,
        navAssessmentsResult,
        taxCertificatesResult
      ] = await Promise.all([
        fetchCurrentAssessment(parcelId),
        fetchHistoricalAssessments(parcelId),
        fetchNavAssessments(parcelId),
        fetchTaxCertificates(parcelId)
      ]);

      const currentAssessment = currentAssessmentResult;
      const historicalAssessments = historicalAssessmentsResult;
      const navAssessments = navAssessmentsResult;
      const taxCertificates = taxCertificatesResult;

      // Calculate derived metrics
      const totalNavAssessment = navAssessments.reduce(
        (sum, nav) => sum + nav.total_assessment, 0
      );

      const isInCdd = navAssessments.some(nav => nav.is_cdd);

      const estimatedAnnualTaxes = calculateEstimatedTaxes(
        currentAssessment, navAssessments
      );

      const effectiveTaxRate = currentAssessment?.taxable_value > 0
        ? (estimatedAnnualTaxes / currentAssessment.taxable_value) * 100
        : 0;

      const taxHistoryTrend = calculateTaxTrend(historicalAssessments);
      const paymentStatus = determinePaymentStatus(taxCertificates);
      const riskFactors = identifyTaxRiskFactors(
        currentAssessment, navAssessments, taxCertificates, taxHistoryTrend
      );

      const taxInfo: PropertyTaxInfo = {
        parcel_id: parcelId,
        current_assessment: currentAssessment,
        historical_assessments: historicalAssessments,
        nav_assessments: navAssessments,
        tax_certificates: taxCertificates,
        total_nav_assessment: totalNavAssessment,
        is_in_cdd: isInCdd,
        estimated_annual_taxes: estimatedAnnualTaxes,
        effective_tax_rate: effectiveTaxRate,
        tax_history_trend: taxHistoryTrend,
        payment_status: paymentStatus,
        risk_factors: riskFactors
      };

      console.log(`[usePropertyTaxInfo] Tax info compiled for ${parcelId}:`, {
        navAssessment: totalNavAssessment,
        isInCdd,
        estimatedTaxes: estimatedAnnualTaxes,
        effectiveRate: effectiveTaxRate,
        certificates: taxCertificates.length
      });

      setTaxInfo(taxInfo);
    } catch (err) {
      console.error('[usePropertyTaxInfo] Error fetching tax info:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch tax information');
      setTaxInfo(null);
    } finally {
      setLoading(false);
    }
  };

  // Helper function to fetch current assessment from florida_parcels
  const fetchCurrentAssessment = async (parcelId: string): Promise<TaxAssessmentData | null> => {
    try {
      console.log(`[usePropertyTaxInfo] Fetching current assessment for ${parcelId}`);

      const { data: floridaData, error } = await supabase
        .from('florida_parcels')
        .select('parcel_id, year, just_value, assessed_value, taxable_value, land_value, building_value, homestead_exemption, other_exemptions, county')
        .eq('parcel_id', parcelId)
        .order('year', { ascending: false })
        .limit(1)
        .single();

      if (error) {
        console.log(`[usePropertyTaxInfo] Current assessment error: ${error.message}`);
        return null;
      }

      if (!floridaData) return null;

      // Calculate estimated tax amount
      const taxableValue = parseFloat(floridaData.taxable_value) || 0;
      const estimatedTaxRate = 0.015; // 1.5% average Florida tax rate
      const taxAmount = taxableValue * estimatedTaxRate;

      return {
        parcel_id: floridaData.parcel_id,
        year: parseInt(floridaData.year) || new Date().getFullYear(),
        just_value: parseFloat(floridaData.just_value) || 0,
        assessed_value: parseFloat(floridaData.assessed_value) || 0,
        taxable_value: taxableValue,
        land_value: parseFloat(floridaData.land_value) || 0,
        building_value: parseFloat(floridaData.building_value) || 0,
        homestead_exemption: parseFloat(floridaData.homestead_exemption) || 0,
        other_exemptions: parseFloat(floridaData.other_exemptions) || 0,
        tax_amount: taxAmount,
        county: floridaData.county || ''
      };
    } catch (error) {
      console.log(`[usePropertyTaxInfo] Current assessment fetch error:`, error);
      return null;
    }
  };

  // Helper function to fetch historical assessments
  const fetchHistoricalAssessments = async (parcelId: string): Promise<TaxAssessmentData[]> => {
    try {
      console.log(`[usePropertyTaxInfo] Fetching historical assessments for ${parcelId}`);

      const { data: historicalData, error } = await supabase
        .from('florida_parcels')
        .select('parcel_id, year, just_value, assessed_value, taxable_value, land_value, building_value, homestead_exemption, other_exemptions, county')
        .eq('parcel_id', parcelId)
        .order('year', { ascending: false })
        .limit(10);

      if (error) {
        console.log(`[usePropertyTaxInfo] Historical assessments error: ${error.message}`);
        return [];
      }

      return (historicalData || []).map(data => ({
        parcel_id: data.parcel_id,
        year: parseInt(data.year) || 0,
        just_value: parseFloat(data.just_value) || 0,
        assessed_value: parseFloat(data.assessed_value) || 0,
        taxable_value: parseFloat(data.taxable_value) || 0,
        land_value: parseFloat(data.land_value) || 0,
        building_value: parseFloat(data.building_value) || 0,
        homestead_exemption: parseFloat(data.homestead_exemption) || 0,
        other_exemptions: parseFloat(data.other_exemptions) || 0,
        tax_amount: (parseFloat(data.taxable_value) || 0) * 0.015,
        county: data.county || ''
      }));
    } catch (error) {
      console.log(`[usePropertyTaxInfo] Historical assessments fetch error:`, error);
      return [];
    }
  };

  // Helper function to fetch NAV assessments
  const fetchNavAssessments = async (parcelId: string): Promise<NavAssessment[]> => {
    try {
      console.log(`[usePropertyTaxInfo] Fetching NAV assessments for ${parcelId}`);

      const { data: navData, error } = await supabase
        .from('nav_assessments')
        .select('*')
        .eq('parcel_id', parcelId)
        .order('assessment_year', { ascending: false });

      if (error) {
        console.log(`[usePropertyTaxInfo] NAV assessments error: ${error.message}`);
        return [];
      }

      return (navData || []).map(nav => ({
        parcel_id: nav.parcel_id,
        authority_name: nav.authority_name || '',
        district_name: nav.district_name || '',
        total_assessment: parseFloat(nav.total_assessment) || 0,
        assessment_year: parseInt(nav.assessment_year) || new Date().getFullYear(),
        bond_debt: parseFloat(nav.bond_debt) || 0,
        annual_payment: parseFloat(nav.annual_payment) || 0,
        remaining_years: parseInt(nav.remaining_years) || 0,
        is_cdd: nav.authority_name?.toLowerCase().includes('community development') || false
      }));
    } catch (error) {
      console.log(`[usePropertyTaxInfo] NAV assessments fetch error:`, error);
      return [];
    }
  };

  // Helper function to fetch tax certificates
  const fetchTaxCertificates = async (parcelId: string): Promise<TaxCertificate[]> => {
    try {
      console.log(`[usePropertyTaxInfo] Fetching tax certificates for ${parcelId}`);

      const { data: certData, error } = await supabase
        .from('tax_certificates')
        .select('*')
        .eq('parcel_id', parcelId)
        .order('certificate_date', { ascending: false });

      if (error) {
        console.log(`[usePropertyTaxInfo] Tax certificates error: ${error.message}`);
        return [];
      }

      return (certData || []).map(cert => ({
        parcel_id: cert.parcel_id,
        certificate_number: cert.certificate_number || '',
        certificate_date: cert.certificate_date || '',
        tax_year: parseInt(cert.tax_year) || 0,
        amount_due: parseFloat(cert.amount_due) || 0,
        status: cert.status || '',
        auction_date: cert.auction_date || undefined,
        sold_to: cert.sold_to || undefined
      }));
    } catch (error) {
      console.log(`[usePropertyTaxInfo] Tax certificates fetch error:`, error);
      return [];
    }
  };

  // Helper function to calculate estimated taxes
  const calculateEstimatedTaxes = (
    currentAssessment: TaxAssessmentData | null,
    navAssessments: NavAssessment[]
  ): number => {
    if (!currentAssessment) return 0;

    const baseTaxes = currentAssessment.tax_amount;
    const navTaxes = navAssessments.reduce((sum, nav) => sum + nav.annual_payment, 0);

    return baseTaxes + navTaxes;
  };

  // Helper function to calculate tax trend
  const calculateTaxTrend = (
    historicalAssessments: TaxAssessmentData[]
  ): 'increasing' | 'decreasing' | 'stable' => {
    if (historicalAssessments.length < 3) return 'stable';

    const recentYears = historicalAssessments.slice(0, 3);
    const values = recentYears.map(a => a.taxable_value);

    let increases = 0;
    let decreases = 0;

    for (let i = 1; i < values.length; i++) {
      const change = (values[i-1] - values[i]) / values[i];
      if (change > 0.05) increases++; // >5% increase
      else if (change < -0.05) decreases++; // >5% decrease
    }

    if (increases > decreases) return 'increasing';
    if (decreases > increases) return 'decreasing';
    return 'stable';
  };

  // Helper function to determine payment status
  const determinePaymentStatus = (
    taxCertificates: TaxCertificate[]
  ): 'current' | 'delinquent' | 'certificate_sold' => {
    if (taxCertificates.length === 0) return 'current';

    const recentCert = taxCertificates[0];
    const currentYear = new Date().getFullYear();

    if (recentCert.tax_year >= currentYear - 1) {
      return recentCert.sold_to ? 'certificate_sold' : 'delinquent';
    }

    return 'current';
  };

  // Helper function to identify tax risk factors
  const identifyTaxRiskFactors = (
    currentAssessment: TaxAssessmentData | null,
    navAssessments: NavAssessment[],
    taxCertificates: TaxCertificate[],
    trend: 'increasing' | 'decreasing' | 'stable'
  ): string[] => {
    const riskFactors: string[] = [];

    const totalNavAssessment = navAssessments.reduce((sum, nav) => sum + nav.total_assessment, 0);
    if (totalNavAssessment > 5000) {
      riskFactors.push(`🚨 High CDD assessment - $${totalNavAssessment.toFixed(0)}/year additional taxes`);
    } else if (totalNavAssessment > 1000) {
      riskFactors.push(`⚠️ CDD assessment - $${totalNavAssessment.toFixed(0)}/year additional taxes`);
    }

    if (currentAssessment && currentAssessment.effective_tax_rate > 2.5) {
      riskFactors.push(`💸 High tax rate - ${currentAssessment.effective_tax_rate.toFixed(2)}% effective rate`);
    }

    if (trend === 'increasing') {
      riskFactors.push('📈 Increasing tax assessments - expect higher future taxes');
    }

    if (taxCertificates.length > 0) {
      riskFactors.push(`🚨 Tax certificate history - ${taxCertificates.length} certificate(s) on record`);
    }

    const isInCdd = navAssessments.some(nav => nav.is_cdd);
    if (isInCdd) {
      const avgRemaining = navAssessments.reduce((sum, nav) => sum + nav.remaining_years, 0) / navAssessments.length;
      if (avgRemaining > 15) {
        riskFactors.push('⏰ Long-term CDD debt - substantial future tax obligations');
      }
    }

    return riskFactors;
  };

  return {
    taxInfo,
    loading,
    error,
    refetch: () => parcelId && fetchTaxInfo(parcelId),
  };
}