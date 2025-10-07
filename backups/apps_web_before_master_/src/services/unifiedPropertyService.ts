/**
 * Unified Property Service
 * Consolidates all property data sources and APIs
 */

import { api } from '@/api/client';

export class UnifiedPropertyService {
  private static instance: UnifiedPropertyService;

  // Singleton pattern for consistent state
  static getInstance() {
    if (!this.instance) {
      this.instance = new UnifiedPropertyService();
    }
    return this.instance;
  }

  /**
   * Fetch complete property data from all sources
   */
  async getCompletePropertyData(parcelId: string) {
    try {
      // Parallel fetch from all data sources
      const [
        coreData,
        salesHistory,
        taxCertificates,
        investmentAnalysis,
        sunbizMatches
      ] = await Promise.all([
        this.fetchCorePropertyData(parcelId),
        this.fetchSalesHistory(parcelId),
        this.fetchTaxCertificates(parcelId),
        this.fetchInvestmentAnalysis(parcelId),
        this.fetchSunbizMatches(parcelId)
      ]);

      // Merge all data with field normalization
      return this.mergePropertyData({
        coreData,
        salesHistory,
        taxCertificates,
        investmentAnalysis,
        sunbizMatches
      });
    } catch (error) {
      console.error('Error fetching complete property data:', error);
      throw error;
    }
  }

  /**
   * Normalize field names across different data sources
   */
  private normalizePropertyData(data: any) {
    return {
      // Always provide both field name formats
      parcel_id: data.parcel_id || data.id,

      // Owner fields
      own_name: data.own_name || data.owner_name || data.owner,
      owner_name: data.owner_name || data.own_name || data.owner,

      // Value fields
      jv: data.jv || data.just_value || data.market_value,
      just_value: data.just_value || data.jv || data.market_value,
      market_value: data.market_value || data.jv || data.just_value,

      // Building fields
      tot_lvg_area: data.tot_lvg_area || data.building_sqft || data.living_area,
      building_sqft: data.building_sqft || data.tot_lvg_area || data.living_area,

      // Year built
      act_yr_blt: data.act_yr_blt || data.year_built || data.built_year,
      year_built: data.year_built || data.act_yr_blt || data.built_year,

      // Property use
      propertyUse: data.propertyUse || data.property_use || data.use_code,
      property_use: data.property_use || data.propertyUse || data.use_code,

      ...data // Preserve all other fields
    };
  }

  private async fetchCorePropertyData(parcelId: string) {
    // Fetch from your primary API
    const response = await api.get(`/properties/${parcelId}`);
    return this.normalizePropertyData(response.data);
  }

  private async fetchSalesHistory(parcelId: string) {
    // Fetch from sales API endpoint
    const response = await api.get(`/api/sales-history/${parcelId}`);
    return response.data;
  }

  private async fetchTaxCertificates(parcelId: string) {
    // Fetch tax certificate data
    const response = await api.get(`/api/tax-certificates/${parcelId}`);
    return response.data;
  }

  private async fetchInvestmentAnalysis(parcelId: string) {
    // Fetch investment scoring
    const response = await api.get(`/api/investment-analysis/${parcelId}`);
    return response.data;
  }

  private async fetchSunbizMatches(parcelId: string) {
    // Fetch Sunbiz entity matches
    const response = await api.get(`/api/sunbiz/matches/${parcelId}`);
    return response.data;
  }

  private mergePropertyData(sources: any) {
    const merged = {
      ...sources.coreData,
      salesHistory: sources.salesHistory,
      taxCertificates: sources.taxCertificates,
      investmentAnalysis: sources.investmentAnalysis,
      sunbizMatches: sources.sunbizMatches,

      // Add computed fields
      hasCompletData: !!(sources.coreData && sources.salesHistory),
      dataQuality: this.calculateDataQuality(sources),
      lastUpdated: new Date().toISOString()
    };

    return this.normalizePropertyData(merged);
  }

  private calculateDataQuality(sources: any): number {
    let score = 0;
    let fields = 0;

    // Check core data completeness
    if (sources.coreData?.jv) { score++; fields++; }
    if (sources.coreData?.own_name) { score++; fields++; }
    if (sources.coreData?.phy_addr1) { score++; fields++; }
    if (sources.salesHistory?.length > 0) { score++; fields++; }
    if (sources.investmentAnalysis?.score) { score++; fields++; }

    return fields > 0 ? (score / fields) * 100 : 0;
  }
}

export const propertyService = UnifiedPropertyService.getInstance();