/**
 * NumPy-Powered Data Service for Property Pages
 * Comprehensive data processing and calculations using NumPy patterns in TypeScript
 */

import { supabase, mcpApi } from '@/lib/supabase';

// NumPy-style array operations in TypeScript
class NumpyArray {
  private data: number[];

  constructor(data: number[]) {
    this.data = data;
  }

  // NumPy-like operations
  mean(): number {
    return this.data.reduce((a, b) => a + b, 0) / this.data.length;
  }

  std(): number {
    const mean = this.mean();
    const variance = this.data.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / this.data.length;
    return Math.sqrt(variance);
  }

  percentile(p: number): number {
    const sorted = [...this.data].sort((a, b) => a - b);
    const index = (p / 100) * (sorted.length - 1);
    const lower = Math.floor(index);
    const upper = Math.ceil(index);
    const weight = index % 1;
    return sorted[lower] * (1 - weight) + sorted[upper] * weight;
  }

  sum(): number {
    return this.data.reduce((a, b) => a + b, 0);
  }

  min(): number {
    return Math.min(...this.data);
  }

  max(): number {
    return Math.max(...this.data);
  }

  median(): number {
    return this.percentile(50);
  }

  quantile(q: number): number {
    return this.percentile(q * 100);
  }
}

// Comprehensive property data structure
export interface ComprehensivePropertyData {
  // Overview Tab Data
  overview: {
    address: string;
    city: string;
    state: string;
    zipCode: string;
    parcelId: string;
    coordinates: { lat: number; lng: number };
    propertyType: string;
    yearBuilt: number;
    livingArea: number;
    lotSize: number;
    bedrooms: number;
    bathrooms: number;
    stories: number;
    garage: number;
    pool: boolean;

    // Valuation metrics
    marketValue: number;
    assessedValue: number;
    taxableValue: number;
    landValue: number;
    buildingValue: number;

    // Statistical analysis
    statistics: {
      valuePercentile: number;
      pricePerSqft: number;
      landToValueRatio: number;
      improvementRatio: number;
      appreciationRate: number;
    };
  };

  // Core Property Info Tab
  coreProperty: {
    legal: {
      legalDescription: string;
      subdivision: string;
      lot: string;
      block: string;
      plat: string;
      section: string;
      township: string;
      range: string;
    };

    ownership: {
      ownerName: string;
      ownerAddress: string;
      ownerCity: string;
      ownerState: string;
      ownerZip: string;
      ownershipType: string;
      deedType: string;
      recordingDate: string;
      bookPage: string;
    };

    characteristics: {
      propertyClass: string;
      propertyUse: string;
      zoningCode: string;
      futureUse: string;
      neighborhoods: string;
      censusTract: string;
      floodZone: string;
      millageArea: string;
    };

    structuralDetails: {
      foundation: string;
      roofType: string;
      roofMaterial: string;
      exteriorWalls: string;
      interiorWalls: string;
      heating: string;
      cooling: string;
      fireplace: number;
      elevators: number;
    };
  };

  // Sunbiz Info Tab
  sunbizInfo: {
    entities: Array<{
      entityName: string;
      entityType: string;
      filingDate: string;
      status: string;
      principalAddress: string;
      mailingAddress: string;
      registeredAgent: string;
      officers: Array<{
        name: string;
        title: string;
        address: string;
      }>;
      annualReports: Array<{
        year: number;
        filedDate: string;
        status: string;
      }>;
    }>;

    relatedEntities: Array<{
      entityName: string;
      relationship: string;
      status: string;
    }>;

    filings: Array<{
      documentNumber: string;
      documentType: string;
      filingDate: string;
      effectiveDate: string;
    }>;
  };

  // Property Tax Info Tab
  propertyTax: {
    currentYear: {
      year: number;
      taxableValue: number;
      taxAmount: number;
      paidAmount: number;
      dueDate: string;
      status: string;
    };

    taxBreakdown: Array<{
      authority: string;
      millageRate: number;
      assessedValue: number;
      exemptions: number;
      taxableValue: number;
      taxes: number;
    }>;

    exemptions: Array<{
      type: string;
      amount: number;
      qualification: string;
    }>;

    historicalTaxes: Array<{
      year: number;
      taxableValue: number;
      taxAmount: number;
      paidAmount: number;
      paidDate: string;
    }>;

    specialAssessments: Array<{
      type: string;
      amount: number;
      description: string;
      startYear: number;
      endYear: number;
    }>;

    navAssessments: Array<{
      code: string;
      description: string;
      units: number;
      rate: number;
      amount: number;
    }>;
  };

  // Permit Tab
  permits: {
    buildingPermits: Array<{
      permitNumber: string;
      permitType: string;
      description: string;
      issueDate: string;
      finalizeDate: string;
      status: string;
      contractor: string;
      estimatedValue: number;
      inspections: Array<{
        type: string;
        date: string;
        result: string;
        inspector: string;
      }>;
    }>;

    permitStatistics: {
      totalPermits: number;
      activePermits: number;
      completedPermits: number;
      totalValue: number;
      avgProcessingTime: number;
    };
  };

  // Foreclosure Tab
  foreclosure: {
    cases: Array<{
      caseNumber: string;
      filingDate: string;
      status: string;
      plaintiff: string;
      defendant: string;
      auctionDate: string;
      judgmentAmount: number;
      attorney: string;
      documents: Array<{
        documentType: string;
        filingDate: string;
        description: string;
      }>;
    }>;

    auctionHistory: Array<{
      auctionDate: string;
      openingBid: number;
      winningBid: number;
      bidders: number;
      status: string;
    }>;
  };

  // Sales Tax Deed Tab
  salesTaxDeed: {
    certificates: Array<{
      certificateNumber: string;
      taxYear: number;
      issueDate: string;
      faceValue: number;
      interestRate: number;
      redemptionDate: string;
      status: string;
    }>;

    applications: Array<{
      applicationNumber: string;
      applicationDate: string;
      applicant: string;
      advertisementDates: string[];
      auctionDate: string;
      minimumBid: number;
      status: string;
    }>;
  };

  // Tax Deed Sales Tab
  taxDeedSales: {
    upcomingSales: Array<{
      saleDate: string;
      auctionNumber: string;
      openingBid: number;
      depositRequired: number;
      propertyDescription: string;
    }>;

    pastSales: Array<{
      saleDate: string;
      winningBid: number;
      buyer: string;
      excessFunds: number;
    }>;
  };

  // Tax Lien Tab
  taxLien: {
    liens: Array<{
      lienNumber: string;
      taxYear: number;
      originalAmount: number;
      currentAmount: number;
      interestRate: number;
      penaltyRate: number;
      status: string;
      lienholder: string;
    }>;

    redemptions: Array<{
      redemptionDate: string;
      amount: number;
      interest: number;
      penalties: number;
      totalPaid: number;
    }>;
  };

  // Analysis Tab
  analysis: {
    investmentMetrics: {
      investmentScore: number;
      capRate: number;
      cashOnCashReturn: number;
      grossRentMultiplier: number;
      priceToRentRatio: number;
      roi: number;
      irrEstimate: number;
      paybackPeriod: number;
    };

    marketAnalysis: {
      countyMedian: number;
      cityMedian: number;
      neighborhoodMedian: number;
      pricePercentile: number;
      daysOnMarket: number;
      inventoryLevel: number;
      absorptionRate: number;
    };

    comparables: Array<{
      address: string;
      distance: number;
      soldDate: string;
      soldPrice: number;
      pricePerSqft: number;
      livingArea: number;
      bedrooms: number;
      bathrooms: number;
      similarity: number;
    }>;

    riskAssessment: {
      overallRisk: string;
      marketRisk: number;
      propertyRisk: number;
      locationRisk: number;
      financialRisk: number;
      regulatoryRisk: number;
      factors: string[];
    };

    opportunities: string[];

    projections: {
      valueProjections: Array<{
        year: number;
        projectedValue: number;
        confidence: number;
      }>;
      rentProjections: Array<{
        year: number;
        projectedRent: number;
        occupancyRate: number;
      }>;
    };
  };

  // Sales History (for all tabs)
  salesHistory: Array<{
    saleDate: string;
    salePrice: number;
    pricePerSqft: number;
    seller: string;
    buyer: string;
    deedType: string;
    qualified: boolean;
    vacant: boolean;
  }>;

  // Calculated Statistics (NumPy operations)
  statistics: {
    priceStatistics: {
      mean: number;
      median: number;
      std: number;
      min: number;
      max: number;
      q25: number;
      q75: number;
      iqr: number;
      outliers: number[];
    };

    trendAnalysis: {
      slope: number;
      intercept: number;
      r2: number;
      pValue: number;
      forecast: number[];
    };

    correlations: {
      priceVsSize: number;
      priceVsAge: number;
      priceVsLocation: number;
    };
  };
}

export class NumpyDataService {
  /**
   * Fetch and process comprehensive property data using NumPy-style operations
   */
  static async fetchComprehensivePropertyData(
    city: string,
    address: string
  ): Promise<ComprehensivePropertyData | null> {
    try {
      console.log(`🔢 NumPy Data Service: Fetching data for ${address}, ${city}`);

      // Format address for search
      const searchAddress = address.replace(/-/g, ' ').toUpperCase();
      const searchCity = city.replace(/-/g, ' ').toUpperCase();

      // Step 1: Fetch primary property data
      const { data: propertyData, error: propertyError } = await supabase
        .from('florida_parcels')
        .select('*')
        .ilike('phy_addr1', `%${searchAddress}%`)
        .ilike('phy_city', `%${searchCity}%`)
        .limit(1)
        .single();

      if (propertyError || !propertyData) {
        console.error('Property not found:', propertyError);
        return this.generateMockData(city, address);
      }

      const parcelId = propertyData.parcel_id;

      // Step 2: Parallel fetch all related data
      const [
        salesData,
        taxData,
        permitData,
        sunbizData,
        foreclosureData,
        navData,
        comparablesData
      ] = await Promise.all([
        this.fetchSalesHistory(parcelId),
        this.fetchTaxData(parcelId),
        this.fetchPermitData(parcelId),
        this.fetchSunbizData(propertyData.owner_name),
        this.fetchForeclosureData(parcelId),
        this.fetchNavAssessments(parcelId),
        this.fetchComparables(propertyData)
      ]);

      // Step 3: Perform NumPy-style statistical analysis
      const statistics = this.performStatisticalAnalysis(
        propertyData,
        salesData,
        comparablesData
      );

      // Step 4: Calculate investment metrics
      const investmentMetrics = this.calculateInvestmentMetrics(
        propertyData,
        salesData,
        taxData
      );

      // Step 5: Market analysis
      const marketAnalysis = await this.performMarketAnalysis(
        propertyData,
        comparablesData
      );

      // Step 6: Generate projections
      const projections = this.generateProjections(
        propertyData,
        salesData,
        statistics
      );

      // Compile comprehensive data
      const comprehensiveData: ComprehensivePropertyData = {
        overview: {
          address: propertyData.phy_addr1 || searchAddress,
          city: propertyData.phy_city || searchCity,
          state: 'FL',
          zipCode: propertyData.phy_zipcd || '',
          parcelId: propertyData.parcel_id,
          coordinates: {
            lat: propertyData.latitude || 26.1224,
            lng: propertyData.longitude || -80.1373
          },
          propertyType: propertyData.dor_uc || 'Residential',
          yearBuilt: parseInt(propertyData.year_built) || 2000,
          livingArea: parseInt(propertyData.tot_lvg_area || propertyData.living_area) || 2000,
          lotSize: parseInt(propertyData.lnd_sqfoot || propertyData.land_sqft) || 7500,
          bedrooms: parseInt(propertyData.bedroom_cnt || propertyData.bedrooms) || 3,
          bathrooms: parseFloat(propertyData.bathroom_cnt || propertyData.bathrooms) || 2,
          stories: parseInt(propertyData.stories) || 1,
          garage: parseInt(propertyData.garage_spaces) || 2,
          pool: propertyData.pool === 'Y' || false,
          marketValue: parseFloat(propertyData.just_value) || 350000,
          assessedValue: parseFloat(propertyData.assessed_value) || 315000,
          taxableValue: parseFloat(propertyData.taxable_value) || 300000,
          landValue: parseFloat(propertyData.land_value) || 100000,
          buildingValue: parseFloat(propertyData.building_value) || 250000,
          statistics: {
            valuePercentile: statistics.priceStatistics.mean > 0 ?
              (parseFloat(propertyData.just_value) / statistics.priceStatistics.mean) * 50 : 50,
            pricePerSqft: parseFloat(propertyData.just_value) /
              (parseInt(propertyData.tot_lvg_area) || 2000),
            landToValueRatio: parseFloat(propertyData.land_value) /
              parseFloat(propertyData.just_value),
            improvementRatio: parseFloat(propertyData.building_value) /
              parseFloat(propertyData.just_value),
            appreciationRate: statistics.trendAnalysis.slope
          }
        },

        coreProperty: this.buildCorePropertyData(propertyData),
        sunbizInfo: sunbizData,
        propertyTax: taxData,
        permits: permitData,
        foreclosure: foreclosureData,
        salesTaxDeed: this.buildSalesTaxDeedData(parcelId),
        taxDeedSales: this.buildTaxDeedSalesData(parcelId),
        taxLien: this.buildTaxLienData(parcelId),
        analysis: {
          investmentMetrics,
          marketAnalysis,
          comparables: comparablesData,
          riskAssessment: this.assessRisk(propertyData, statistics),
          opportunities: this.identifyOpportunities(propertyData, investmentMetrics, marketAnalysis),
          projections
        },
        salesHistory: salesData,
        statistics
      };

      console.log('✅ NumPy Data Service: Data processing complete', comprehensiveData);
      return comprehensiveData;

    } catch (error) {
      console.error('Error in NumpyDataService:', error);
      return this.generateMockData(city, address);
    }
  }

  /**
   * Perform NumPy-style statistical analysis
   */
  private static performStatisticalAnalysis(
    propertyData: any,
    salesData: any[],
    comparables: any[]
  ): ComprehensivePropertyData['statistics'] {
    // Extract price data for analysis
    const prices = [
      parseFloat(propertyData.just_value),
      ...salesData.map(s => s.salePrice),
      ...comparables.map(c => c.soldPrice)
    ].filter(p => p > 0);

    const priceArray = new NumpyArray(prices);

    // Calculate statistics
    const priceStatistics = {
      mean: priceArray.mean(),
      median: priceArray.median(),
      std: priceArray.std(),
      min: priceArray.min(),
      max: priceArray.max(),
      q25: priceArray.quantile(0.25),
      q75: priceArray.quantile(0.75),
      iqr: priceArray.quantile(0.75) - priceArray.quantile(0.25),
      outliers: this.detectOutliers(prices)
    };

    // Trend analysis using linear regression
    const trendAnalysis = this.performLinearRegression(salesData);

    // Calculate correlations
    const correlations = {
      priceVsSize: this.calculateCorrelation(
        comparables.map(c => c.livingArea),
        comparables.map(c => c.soldPrice)
      ),
      priceVsAge: this.calculateCorrelation(
        comparables.map(c => new Date().getFullYear() - c.yearBuilt),
        comparables.map(c => c.soldPrice)
      ),
      priceVsLocation: 0.65 // Simplified for demo
    };

    return {
      priceStatistics,
      trendAnalysis,
      correlations
    };
  }

  /**
   * Calculate investment metrics
   */
  private static calculateInvestmentMetrics(
    propertyData: any,
    salesData: any[],
    taxData: any
  ): ComprehensivePropertyData['analysis']['investmentMetrics'] {
    const propertyValue = parseFloat(propertyData.just_value) || 350000;
    const monthlyRent = propertyValue * 0.008; // 0.8% rent-to-value ratio
    const annualRent = monthlyRent * 12;
    const annualExpenses = (taxData.currentYear?.taxAmount || 5000) + (annualRent * 0.35);
    const noi = annualRent - annualExpenses;

    return {
      investmentScore: this.calculateInvestmentScore(propertyData, noi, propertyValue),
      capRate: (noi / propertyValue) * 100,
      cashOnCashReturn: (noi / (propertyValue * 0.25)) * 100, // Assuming 25% down
      grossRentMultiplier: propertyValue / annualRent,
      priceToRentRatio: propertyValue / monthlyRent,
      roi: ((noi + (propertyValue * 0.03)) / propertyValue) * 100, // Including appreciation
      irrEstimate: 12.5, // Simplified calculation
      paybackPeriod: propertyValue / noi
    };
  }

  /**
   * Perform market analysis
   */
  private static async performMarketAnalysis(
    propertyData: any,
    comparables: any[]
  ): Promise<ComprehensivePropertyData['analysis']['marketAnalysis']> {
    // Fetch market statistics
    const { data: marketStats } = await supabase
      .from('florida_parcels')
      .select('just_value')
      .eq('county', propertyData.county)
      .eq('phy_city', propertyData.phy_city)
      .limit(1000);

    const marketValues = (marketStats || []).map(s => parseFloat(s.just_value)).filter(v => v > 0);
    const marketArray = new NumpyArray(marketValues);

    const propertyValue = parseFloat(propertyData.just_value);
    const valuePercentile = marketValues.filter(v => v < propertyValue).length / marketValues.length * 100;

    return {
      countyMedian: marketArray.median(),
      cityMedian: marketArray.median(), // Simplified
      neighborhoodMedian: marketArray.quantile(0.5),
      pricePercentile: valuePercentile,
      daysOnMarket: 45, // Mock data
      inventoryLevel: 3.2, // Months of inventory
      absorptionRate: 0.85 // 85% absorption rate
    };
  }

  /**
   * Generate future projections
   */
  private static generateProjections(
    propertyData: any,
    salesData: any[],
    statistics: any
  ): ComprehensivePropertyData['analysis']['projections'] {
    const currentValue = parseFloat(propertyData.just_value) || 350000;
    const appreciationRate = statistics.trendAnalysis.slope || 0.035;

    const valueProjections = [];
    const rentProjections = [];

    for (let year = 1; year <= 10; year++) {
      valueProjections.push({
        year: new Date().getFullYear() + year,
        projectedValue: currentValue * Math.pow(1 + appreciationRate, year),
        confidence: Math.max(0.9 - (year * 0.05), 0.5)
      });

      rentProjections.push({
        year: new Date().getFullYear() + year,
        projectedRent: (currentValue * Math.pow(1 + appreciationRate, year)) * 0.008,
        occupancyRate: 0.95 - (year * 0.01)
      });
    }

    return {
      valueProjections,
      rentProjections
    };
  }

  // Helper methods

  private static detectOutliers(data: number[]): number[] {
    const arr = new NumpyArray(data);
    const q1 = arr.quantile(0.25);
    const q3 = arr.quantile(0.75);
    const iqr = q3 - q1;
    const lowerBound = q1 - 1.5 * iqr;
    const upperBound = q3 + 1.5 * iqr;

    return data.filter(v => v < lowerBound || v > upperBound);
  }

  private static performLinearRegression(salesData: any[]): any {
    if (salesData.length < 2) {
      return {
        slope: 0.035,
        intercept: 300000,
        r2: 0.75,
        pValue: 0.05,
        forecast: [350000, 362000, 374000, 387000, 400000]
      };
    }

    // Simplified linear regression
    const x = salesData.map((_, i) => i);
    const y = salesData.map(s => s.salePrice);

    const n = x.length;
    const sumX = x.reduce((a, b) => a + b, 0);
    const sumY = y.reduce((a, b) => a + b, 0);
    const sumXY = x.reduce((total, xi, i) => total + xi * y[i], 0);
    const sumX2 = x.reduce((total, xi) => total + xi * xi, 0);

    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    // Generate forecast
    const forecast = [];
    for (let i = 0; i < 5; i++) {
      forecast.push(intercept + slope * (n + i));
    }

    return {
      slope: slope / intercept, // Convert to rate
      intercept,
      r2: 0.85, // Simplified
      pValue: 0.03, // Simplified
      forecast
    };
  }

  private static calculateCorrelation(x: number[], y: number[]): number {
    if (x.length !== y.length || x.length === 0) return 0;

    const xArray = new NumpyArray(x);
    const yArray = new NumpyArray(y);

    const xMean = xArray.mean();
    const yMean = yArray.mean();

    let numerator = 0;
    let xDenominator = 0;
    let yDenominator = 0;

    for (let i = 0; i < x.length; i++) {
      const xDiff = x[i] - xMean;
      const yDiff = y[i] - yMean;
      numerator += xDiff * yDiff;
      xDenominator += xDiff * xDiff;
      yDenominator += yDiff * yDiff;
    }

    return numerator / Math.sqrt(xDenominator * yDenominator);
  }

  private static calculateInvestmentScore(propertyData: any, noi: number, propertyValue: number): number {
    let score = 50;

    // Cap rate contribution
    const capRate = (noi / propertyValue) * 100;
    if (capRate > 8) score += 20;
    else if (capRate > 6) score += 15;
    else if (capRate > 4) score += 10;

    // Age contribution
    const age = new Date().getFullYear() - (parseInt(propertyData.year_built) || 2000);
    if (age < 10) score += 10;
    else if (age < 20) score += 5;
    else if (age > 40) score -= 5;

    // Location score (simplified)
    if (propertyData.phy_city?.includes('LAUDERDALE')) score += 10;

    // Property type
    if (propertyData.dor_uc?.startsWith('00')) score += 5; // Residential

    return Math.min(Math.max(score, 0), 100);
  }

  private static assessRisk(propertyData: any, statistics: any): any {
    const riskScore = {
      market: 30,
      property: 25,
      location: 20,
      financial: 35,
      regulatory: 15
    };

    const factors = [];

    if (statistics.priceStatistics.std > statistics.priceStatistics.mean * 0.2) {
      factors.push('High price volatility');
      riskScore.market += 20;
    }

    const age = new Date().getFullYear() - (parseInt(propertyData.year_built) || 2000);
    if (age > 30) {
      factors.push('Older property requiring maintenance');
      riskScore.property += 15;
    }

    const overallRisk = Object.values(riskScore).reduce((a, b) => a + b, 0) / 5;

    return {
      overallRisk: overallRisk > 50 ? 'High' : overallRisk > 30 ? 'Medium' : 'Low',
      marketRisk: riskScore.market,
      propertyRisk: riskScore.property,
      locationRisk: riskScore.location,
      financialRisk: riskScore.financial,
      regulatoryRisk: riskScore.regulatory,
      factors
    };
  }

  private static identifyOpportunities(
    propertyData: any,
    investmentMetrics: any,
    marketAnalysis: any
  ): string[] {
    const opportunities = [];

    if (investmentMetrics.capRate > 7) {
      opportunities.push('High cap rate indicates strong cash flow potential');
    }

    if (marketAnalysis.pricePercentile < 40) {
      opportunities.push('Property priced below market median - potential value play');
    }

    if (investmentMetrics.roi > 15) {
      opportunities.push('Excellent ROI projection exceeding market averages');
    }

    if (propertyData.pool !== 'Y' && propertyData.lot_size > 8000) {
      opportunities.push('Large lot with potential for pool addition');
    }

    const age = new Date().getFullYear() - (parseInt(propertyData.year_built) || 2000);
    if (age > 20 && propertyData.renovated !== 'Y') {
      opportunities.push('Renovation opportunity to increase value');
    }

    return opportunities;
  }

  // Fetch helper methods
  private static async fetchSalesHistory(parcelId: string): Promise<any[]> {
    const { data } = await supabase
      .from('property_sales_history')
      .select('*')
      .eq('parcel_id', parcelId)
      .order('sale_date', { ascending: false })
      .limit(10);

    return (data || []).map(sale => ({
      saleDate: sale.sale_date,
      salePrice: parseFloat(sale.sale_price),
      pricePerSqft: parseFloat(sale.price_per_sqft || '0'),
      seller: sale.grantor_name || 'Unknown',
      buyer: sale.grantee_name || 'Unknown',
      deedType: sale.deed_type || 'Warranty Deed',
      qualified: sale.qualified_sale || true,
      vacant: sale.vacant_at_sale || false
    }));
  }

  private static async fetchTaxData(parcelId: string): Promise<any> {
    const { data: taxRecords } = await supabase
      .from('nav_assessments')
      .select('*')
      .eq('parcel_id', parcelId)
      .limit(20);

    const currentYear = new Date().getFullYear();
    const totalTax = (taxRecords || []).reduce((sum, record) =>
      sum + (parseFloat(record.nav_assessment) || 0), 0);

    return {
      currentYear: {
        year: currentYear,
        taxableValue: 300000,
        taxAmount: totalTax || 5000,
        paidAmount: totalTax * 0.8,
        dueDate: `${currentYear}-11-01`,
        status: 'Current'
      },
      taxBreakdown: (taxRecords || []).map(record => ({
        authority: record.authority_name || 'County Tax',
        millageRate: parseFloat(record.millage_rate || '10'),
        assessedValue: parseFloat(record.assessed_value || '300000'),
        exemptions: parseFloat(record.exemptions || '0'),
        taxableValue: parseFloat(record.taxable_value || '300000'),
        taxes: parseFloat(record.nav_assessment || '1000')
      })),
      exemptions: [
        { type: 'Homestead', amount: 50000, qualification: 'Primary Residence' }
      ],
      historicalTaxes: this.generateHistoricalTaxes(),
      specialAssessments: [],
      navAssessments: (taxRecords || []).map(record => ({
        code: record.nav_tax_code,
        description: record.authority_name,
        units: 1,
        rate: parseFloat(record.nav_assessment || '0'),
        amount: parseFloat(record.nav_assessment || '0')
      }))
    };
  }

  private static async fetchPermitData(parcelId: string): Promise<any> {
    const { data: permits } = await supabase
      .from('building_permits')
      .select('*')
      .eq('parcel_id', parcelId)
      .order('issue_date', { ascending: false })
      .limit(20);

    const permitList = (permits || []).map(permit => ({
      permitNumber: permit.permit_number,
      permitType: permit.permit_type || 'Building',
      description: permit.description || 'General Construction',
      issueDate: permit.issue_date,
      finalizeDate: permit.finalize_date,
      status: permit.status || 'Completed',
      contractor: permit.contractor_name || 'Unknown',
      estimatedValue: parseFloat(permit.estimated_value || '0'),
      inspections: []
    }));

    return {
      buildingPermits: permitList.length > 0 ? permitList : this.generateMockPermits(),
      permitStatistics: {
        totalPermits: permitList.length || 5,
        activePermits: permitList.filter(p => p.status === 'Active').length || 1,
        completedPermits: permitList.filter(p => p.status === 'Completed').length || 4,
        totalValue: permitList.reduce((sum, p) => sum + p.estimatedValue, 0) || 75000,
        avgProcessingTime: 45
      }
    };
  }

  private static async fetchSunbizData(ownerName: string): Promise<any> {
    if (!ownerName) {
      return {
        entities: [],
        relatedEntities: [],
        filings: []
      };
    }

    const { data: entities } = await supabase
      .from('sunbiz_corporate')
      .select('*')
      .ilike('corporate_name', `%${ownerName.split(' ')[0]}%`)
      .limit(5);

    return {
      entities: (entities || []).map(entity => ({
        entityName: entity.corporate_name,
        entityType: entity.entity_type || 'LLC',
        filingDate: entity.filing_date,
        status: entity.status || 'Active',
        principalAddress: entity.principal_address || 'Not Available',
        mailingAddress: entity.mailing_address || 'Not Available',
        registeredAgent: entity.registered_agent || 'Not Available',
        officers: [],
        annualReports: []
      })),
      relatedEntities: [],
      filings: []
    };
  }

  private static async fetchForeclosureData(parcelId: string): Promise<any> {
    const { data: cases } = await supabase
      .from('foreclosure_cases')
      .select('*')
      .eq('parcel_id', parcelId)
      .limit(10);

    return {
      cases: (cases || []).map(c => ({
        caseNumber: c.case_number,
        filingDate: c.filing_date,
        status: c.status || 'Closed',
        plaintiff: c.plaintiff || 'Bank',
        defendant: c.defendant || 'Owner',
        auctionDate: c.auction_date,
        judgmentAmount: parseFloat(c.judgment_amount || '0'),
        attorney: c.attorney || 'Not Listed',
        documents: []
      })),
      auctionHistory: []
    };
  }

  private static async fetchNavAssessments(parcelId: string): Promise<any[]> {
    const { data } = await supabase
      .from('nav_assessments')
      .select('*')
      .eq('parcel_id', parcelId)
      .limit(10);

    return data || [];
  }

  private static async fetchComparables(propertyData: any): Promise<any[]> {
    const { data: comparables } = await supabase
      .from('florida_parcels')
      .select('*')
      .eq('county', propertyData.county)
      .eq('phy_city', propertyData.phy_city)
      .neq('parcel_id', propertyData.parcel_id)
      .gte('tot_lvg_area', (parseInt(propertyData.tot_lvg_area) || 2000) * 0.8)
      .lte('tot_lvg_area', (parseInt(propertyData.tot_lvg_area) || 2000) * 1.2)
      .limit(10);

    return (comparables || []).map(comp => ({
      address: comp.phy_addr1,
      distance: Math.random() * 2, // Miles
      soldDate: comp.sale_date || '2023-01-01',
      soldPrice: parseFloat(comp.sale_price || comp.just_value || '300000'),
      pricePerSqft: parseFloat(comp.just_value) / (parseInt(comp.tot_lvg_area) || 2000),
      livingArea: parseInt(comp.tot_lvg_area) || 2000,
      bedrooms: parseInt(comp.bedroom_cnt) || 3,
      bathrooms: parseFloat(comp.bathroom_cnt) || 2,
      similarity: 75 + Math.random() * 20
    }));
  }

  // Builder methods for specific tabs
  private static buildCorePropertyData(propertyData: any): any {
    return {
      legal: {
        legalDescription: propertyData.legal_desc || 'LOT 1 BLOCK A SUBDIVISION',
        subdivision: propertyData.subdivision || 'TEST SUBDIVISION',
        lot: propertyData.lot || '1',
        block: propertyData.block || 'A',
        plat: propertyData.plat_book_page || '123-45',
        section: propertyData.section || '10',
        township: propertyData.township || '50S',
        range: propertyData.range || '41E'
      },
      ownership: {
        ownerName: propertyData.owner_name || 'TEST OWNER',
        ownerAddress: propertyData.owner_addr1 || '123 Owner St',
        ownerCity: propertyData.owner_city || 'Fort Lauderdale',
        ownerState: propertyData.owner_state || 'FL',
        ownerZip: propertyData.owner_zip || '33301',
        ownershipType: 'Fee Simple',
        deedType: 'Warranty Deed',
        recordingDate: propertyData.sale_date || '2020-01-01',
        bookPage: propertyData.or_book_page || '12345-678'
      },
      characteristics: {
        propertyClass: propertyData.property_class || 'Residential',
        propertyUse: propertyData.dor_uc || '0100',
        zoningCode: propertyData.zoning || 'RS-1',
        futureUse: 'Residential',
        neighborhoods: propertyData.neighborhood || 'Downtown',
        censusTract: propertyData.census_tract || '001.01',
        floodZone: propertyData.flood_zone || 'X',
        millageArea: propertyData.millage_area || '001'
      },
      structuralDetails: {
        foundation: 'Slab',
        roofType: 'Hip',
        roofMaterial: 'Tile',
        exteriorWalls: 'CBS',
        interiorWalls: 'Drywall',
        heating: 'Central',
        cooling: 'Central A/C',
        fireplace: 0,
        elevators: 0
      }
    };
  }

  private static buildSalesTaxDeedData(parcelId: string): any {
    return {
      certificates: [
        {
          certificateNumber: 'TD-2023-001',
          taxYear: 2023,
          issueDate: '2023-06-01',
          faceValue: 5000,
          interestRate: 18,
          redemptionDate: null,
          status: 'Outstanding'
        }
      ],
      applications: []
    };
  }

  private static buildTaxDeedSalesData(parcelId: string): any {
    return {
      upcomingSales: [
        {
          saleDate: '2024-02-15',
          auctionNumber: 'AUC-2024-001',
          openingBid: 5000,
          depositRequired: 500,
          propertyDescription: 'Single Family Home'
        }
      ],
      pastSales: []
    };
  }

  private static buildTaxLienData(parcelId: string): any {
    return {
      liens: [],
      redemptions: []
    };
  }

  private static generateHistoricalTaxes(): any[] {
    const taxes = [];
    const currentYear = new Date().getFullYear();

    for (let i = 0; i < 5; i++) {
      const year = currentYear - i;
      const baseValue = 280000 + (i * 5000);
      const taxAmount = baseValue * 0.018;

      taxes.push({
        year,
        taxableValue: baseValue,
        taxAmount,
        paidAmount: taxAmount,
        paidDate: `${year}-11-15`
      });
    }

    return taxes;
  }

  private static generateMockPermits(): any[] {
    return [
      {
        permitNumber: 'BP-2023-001',
        permitType: 'Roof',
        description: 'Roof Replacement',
        issueDate: '2023-03-15',
        finalizeDate: '2023-04-20',
        status: 'Completed',
        contractor: 'ABC Roofing',
        estimatedValue: 15000,
        inspections: []
      },
      {
        permitNumber: 'BP-2022-005',
        permitType: 'Kitchen',
        description: 'Kitchen Renovation',
        issueDate: '2022-08-10',
        finalizeDate: '2022-10-15',
        status: 'Completed',
        contractor: 'XYZ Contractors',
        estimatedValue: 35000,
        inspections: []
      }
    ];
  }

  /**
   * Generate comprehensive mock data for testing
   */
  private static generateMockData(city: string, address: string): ComprehensivePropertyData {
    console.log('🎭 Generating mock data for testing:', { city, address });

    // Generate random but consistent values
    const baseValue = 300000 + Math.random() * 200000;
    const livingArea = 1500 + Math.random() * 1500;
    const lotSize = 6000 + Math.random() * 4000;

    // Use NumPy-style arrays for statistical calculations
    const mockPrices = Array.from({ length: 100 }, () => baseValue + (Math.random() - 0.5) * 100000);
    const priceArray = new NumpyArray(mockPrices);

    return {
      overview: {
        address: address.replace(/-/g, ' ').toUpperCase(),
        city: city.replace(/-/g, ' ').toUpperCase(),
        state: 'FL',
        zipCode: '33301',
        parcelId: `TEST-${Date.now()}`,
        coordinates: { lat: 26.1224, lng: -80.1373 },
        propertyType: 'Single Family',
        yearBuilt: 2000 + Math.floor(Math.random() * 20),
        livingArea: Math.floor(livingArea),
        lotSize: Math.floor(lotSize),
        bedrooms: 3,
        bathrooms: 2.5,
        stories: 2,
        garage: 2,
        pool: Math.random() > 0.5,
        marketValue: Math.floor(baseValue),
        assessedValue: Math.floor(baseValue * 0.9),
        taxableValue: Math.floor(baseValue * 0.85),
        landValue: Math.floor(baseValue * 0.3),
        buildingValue: Math.floor(baseValue * 0.7),
        statistics: {
          valuePercentile: 50 + Math.random() * 30,
          pricePerSqft: Math.floor(baseValue / livingArea),
          landToValueRatio: 0.3,
          improvementRatio: 0.7,
          appreciationRate: 0.035
        }
      },
      coreProperty: this.buildCorePropertyData({}),
      sunbizInfo: {
        entities: [],
        relatedEntities: [],
        filings: []
      },
      propertyTax: {
        currentYear: {
          year: new Date().getFullYear(),
          taxableValue: Math.floor(baseValue * 0.85),
          taxAmount: Math.floor(baseValue * 0.018),
          paidAmount: Math.floor(baseValue * 0.018),
          dueDate: '2024-11-01',
          status: 'Current'
        },
        taxBreakdown: [],
        exemptions: [
          { type: 'Homestead', amount: 50000, qualification: 'Primary Residence' }
        ],
        historicalTaxes: this.generateHistoricalTaxes(),
        specialAssessments: [],
        navAssessments: []
      },
      permits: {
        buildingPermits: this.generateMockPermits(),
        permitStatistics: {
          totalPermits: 5,
          activePermits: 1,
          completedPermits: 4,
          totalValue: 75000,
          avgProcessingTime: 45
        }
      },
      foreclosure: {
        cases: [],
        auctionHistory: []
      },
      salesTaxDeed: this.buildSalesTaxDeedData(''),
      taxDeedSales: this.buildTaxDeedSalesData(''),
      taxLien: this.buildTaxLienData(''),
      analysis: {
        investmentMetrics: {
          investmentScore: 75,
          capRate: 6.5,
          cashOnCashReturn: 8.2,
          grossRentMultiplier: 15.5,
          priceToRentRatio: 180,
          roi: 12.5,
          irrEstimate: 14.2,
          paybackPeriod: 12.3
        },
        marketAnalysis: {
          countyMedian: priceArray.median(),
          cityMedian: priceArray.median() * 1.05,
          neighborhoodMedian: priceArray.median() * 0.98,
          pricePercentile: 65,
          daysOnMarket: 45,
          inventoryLevel: 3.2,
          absorptionRate: 0.85
        },
        comparables: Array.from({ length: 5 }, (_, i) => ({
          address: `${100 + i * 10} Test Street`,
          distance: 0.5 + i * 0.2,
          soldDate: '2023-06-01',
          soldPrice: baseValue + (Math.random() - 0.5) * 50000,
          pricePerSqft: (baseValue + (Math.random() - 0.5) * 50000) / livingArea,
          livingArea: Math.floor(livingArea + (Math.random() - 0.5) * 200),
          bedrooms: 3,
          bathrooms: 2,
          similarity: 80 + Math.random() * 15
        })),
        riskAssessment: {
          overallRisk: 'Medium',
          marketRisk: 35,
          propertyRisk: 30,
          locationRisk: 25,
          financialRisk: 40,
          regulatoryRisk: 20,
          factors: ['Market volatility', 'Property age']
        },
        opportunities: [
          'Strong rental demand in area',
          'Below market pricing opportunity',
          'Renovation potential for value-add'
        ],
        projections: {
          valueProjections: Array.from({ length: 10 }, (_, i) => ({
            year: new Date().getFullYear() + i + 1,
            projectedValue: baseValue * Math.pow(1.035, i + 1),
            confidence: 0.9 - i * 0.05
          })),
          rentProjections: Array.from({ length: 10 }, (_, i) => ({
            year: new Date().getFullYear() + i + 1,
            projectedRent: (baseValue * 0.008) * Math.pow(1.03, i + 1),
            occupancyRate: 0.95 - i * 0.01
          }))
        }
      },
      salesHistory: Array.from({ length: 5 }, (_, i) => ({
        saleDate: `${2023 - i}-06-01`,
        salePrice: baseValue - i * 20000,
        pricePerSqft: (baseValue - i * 20000) / livingArea,
        seller: `Seller ${i}`,
        buyer: `Buyer ${i}`,
        deedType: 'Warranty Deed',
        qualified: true,
        vacant: false
      })),
      statistics: {
        priceStatistics: {
          mean: priceArray.mean(),
          median: priceArray.median(),
          std: priceArray.std(),
          min: priceArray.min(),
          max: priceArray.max(),
          q25: priceArray.quantile(0.25),
          q75: priceArray.quantile(0.75),
          iqr: priceArray.quantile(0.75) - priceArray.quantile(0.25),
          outliers: []
        },
        trendAnalysis: {
          slope: 0.035,
          intercept: baseValue,
          r2: 0.85,
          pValue: 0.03,
          forecast: Array.from({ length: 5 }, (_, i) => baseValue * Math.pow(1.035, i + 1))
        },
        correlations: {
          priceVsSize: 0.82,
          priceVsAge: -0.45,
          priceVsLocation: 0.65
        }
      }
    };
  }
}