import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';

export interface PropertyMetrics {
  purchase_price: number;
  current_value: number;
  estimated_rent: number;
  annual_expenses: number;
  net_operating_income: number;
  cap_rate: number;
  cash_on_cash_return: number;
  total_roi: number;
  break_even_ratio: number;
  price_per_sqft: number;
  rent_to_value_ratio: number;
}

export interface CashFlowAnalysis {
  monthly_rental_income: number;
  monthly_expenses: {
    property_taxes: number;
    insurance: number;
    maintenance: number;
    property_management: number;
    vacancy_allowance: number;
    hoa_cdd_fees: number;
    other: number;
    total: number;
  };
  monthly_net_cash_flow: number;
  annual_cash_flow: number;
  cash_flow_multiple: number;
}

export interface CompetitiveAnalysis {
  comparable_properties: Array<{
    parcel_id: string;
    address: string;
    distance_miles: number;
    sale_price: number;
    sale_date: string;
    sqft: number;
    price_per_sqft: number;
    similarity_score: number;
  }>;
  market_rent_range: {
    low: number;
    median: number;
    high: number;
  };
  area_appreciation_rate: number;
  market_velocity: number; // days on market average
  inventory_levels: 'low' | 'moderate' | 'high';
}

export interface RiskAssessment {
  overall_risk_score: number; // 0-100, lower is better
  risk_factors: Array<{
    category: string;
    factor: string;
    impact: 'low' | 'medium' | 'high';
    description: string;
  }>;
  opportunities: Array<{
    category: string;
    opportunity: string;
    potential: 'low' | 'medium' | 'high';
    description: string;
  }>;
}

export interface InvestmentScenarios {
  conservative: {
    appreciation_rate: number;
    rent_growth_rate: number;
    vacancy_rate: number;
    expense_growth_rate: number;
    five_year_value: number;
    five_year_equity: number;
    five_year_total_return: number;
  };
  moderate: {
    appreciation_rate: number;
    rent_growth_rate: number;
    vacancy_rate: number;
    expense_growth_rate: number;
    five_year_value: number;
    five_year_equity: number;
    five_year_total_return: number;
  };
  optimistic: {
    appreciation_rate: number;
    rent_growth_rate: number;
    vacancy_rate: number;
    expense_growth_rate: number;
    five_year_value: number;
    five_year_equity: number;
    five_year_total_return: number;
  };
}

export interface InvestmentAnalysis {
  parcel_id: string;
  property_metrics: PropertyMetrics;
  cash_flow_analysis: CashFlowAnalysis;
  competitive_analysis: CompetitiveAnalysis;
  risk_assessment: RiskAssessment;
  investment_scenarios: InvestmentScenarios;
  recommendation: {
    score: number; // 0-100
    grade: 'A' | 'B' | 'C' | 'D' | 'F';
    action: 'strong_buy' | 'buy' | 'hold' | 'pass' | 'avoid';
    summary: string;
    key_points: string[];
  };
  last_updated: string;
}

export function useInvestmentAnalysis(
  parcelId: string | null,
  purchasePrice?: number,
  downPaymentPercent: number = 25,
  loanInterestRate: number = 7.0,
  loanTermYears: number = 30
) {
  const [analysis, setAnalysis] = useState<InvestmentAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!parcelId) {
      setAnalysis(null);
      return;
    }

    performAnalysis(parcelId, purchasePrice);
  }, [parcelId, purchasePrice, downPaymentPercent, loanInterestRate, loanTermYears]);

  const performAnalysis = async (parcelId: string, purchasePrice?: number) => {
    setLoading(true);
    setError(null);

    try {
      console.log(`[useInvestmentAnalysis] Starting analysis for parcel: ${parcelId}`);

      // Get property data from florida_parcels
      const { data: propertyData, error: propertyError } = await supabase
        .from('florida_parcels')
        .select('*')
        .eq('parcel_id', parcelId)
        .single();

      if (propertyError || !propertyData) {
        throw new Error(`Property not found: ${propertyError?.message || 'No data'}`);
      }

      // Get recent sales data for price estimation
      const recentSalePrice = await getRecentSalePrice(parcelId);
      const effectivePurchasePrice = purchasePrice || recentSalePrice || parseFloat(propertyData.just_value) || 0;

      if (effectivePurchasePrice <= 0) {
        throw new Error('Cannot analyze property without valid purchase price or valuation');
      }

      // Perform parallel analysis
      const [
        propertyMetrics,
        cashFlowAnalysis,
        competitiveAnalysis,
        riskAssessment,
        investmentScenarios
      ] = await Promise.all([
        calculatePropertyMetrics(propertyData, effectivePurchasePrice),
        calculateCashFlowAnalysis(propertyData, effectivePurchasePrice, downPaymentPercent, loanInterestRate, loanTermYears),
        performCompetitiveAnalysis(propertyData, parcelId),
        assessRisks(propertyData, parcelId),
        generateInvestmentScenarios(propertyData, effectivePurchasePrice)
      ]);

      // Generate overall recommendation
      const recommendation = generateRecommendation(
        propertyMetrics, cashFlowAnalysis, competitiveAnalysis, riskAssessment
      );

      const analysis: InvestmentAnalysis = {
        parcel_id: parcelId,
        property_metrics: propertyMetrics,
        cash_flow_analysis: cashFlowAnalysis,
        competitive_analysis: competitiveAnalysis,
        risk_assessment: riskAssessment,
        investment_scenarios: investmentScenarios,
        recommendation,
        last_updated: new Date().toISOString()
      };

      console.log(`[useInvestmentAnalysis] Analysis complete for ${parcelId}:`, {
        score: recommendation.score,
        grade: recommendation.grade,
        capRate: propertyMetrics.cap_rate,
        monthlyCashFlow: cashFlowAnalysis.monthly_net_cash_flow
      });

      setAnalysis(analysis);
    } catch (err) {
      console.error('[useInvestmentAnalysis] Analysis error:', err);
      setError(err instanceof Error ? err.message : 'Failed to perform investment analysis');
      setAnalysis(null);
    } finally {
      setLoading(false);
    }
  };

  // Helper to get recent sale price
  const getRecentSalePrice = async (parcelId: string): Promise<number> => {
    try {
      // Try multiple sales sources (matching useSalesData pattern)
      const sources = [
        { table: 'comprehensive_sales_data', priceField: 'sale_price' },
        { table: 'sdf_sales', priceField: 'sale_price' },
        { table: 'sales_history', priceField: 'sale_price' }
      ];

      for (const source of sources) {
        const { data, error } = await supabase
          .from(source.table)
          .select(source.priceField + ', sale_date')
          .eq('parcel_id', parcelId)
          .gte(source.priceField, 10000) // Filter out nominal sales
          .order('sale_date', { ascending: false })
          .limit(1);

        if (!error && data && data.length > 0) {
          const salePrice = parseFloat(data[0][source.priceField]);
          if (salePrice > 10000) {
            console.log(`[useInvestmentAnalysis] Found recent sale: $${salePrice} from ${source.table}`);
            return salePrice;
          }
        }
      }

      return 0;
    } catch (error) {
      console.log(`[useInvestmentAnalysis] Error getting recent sale price:`, error);
      return 0;
    }
  };

  // Calculate property metrics
  const calculatePropertyMetrics = async (
    propertyData: any, purchasePrice: number
  ): Promise<PropertyMetrics> => {
    const currentValue = parseFloat(propertyData.just_value) || purchasePrice;
    const totalSqft = parseFloat(propertyData.total_living_area) || parseFloat(propertyData.building_sqft) || 1;

    // Estimate market rent (0.8% - 1.2% of property value per month)
    const rentMultiplier = getRentMultiplier(propertyData.dor_uc, propertyData.county);
    const estimatedRent = currentValue * rentMultiplier / 12;

    // Calculate annual expenses (25-35% of rental income typically)
    const taxableValue = parseFloat(propertyData.taxable_value) || currentValue * 0.85;
    const propertyTaxes = taxableValue * 0.015; // 1.5% average FL tax rate
    const insurance = currentValue * 0.003; // 0.3% of value annually
    const maintenance = estimatedRent * 12 * 0.10; // 10% of rent
    const management = estimatedRent * 12 * 0.08; // 8% of rent
    const vacancy = estimatedRent * 12 * 0.08; // 8% vacancy allowance
    const annualExpenses = propertyTaxes + insurance + maintenance + management + vacancy;

    const netOperatingIncome = (estimatedRent * 12) - annualExpenses;
    const capRate = currentValue > 0 ? (netOperatingIncome / currentValue) * 100 : 0;

    // Assume 25% down payment for cash-on-cash calculation
    const downPayment = purchasePrice * (downPaymentPercent / 100);
    const cashOnCashReturn = downPayment > 0 ? (netOperatingIncome / downPayment) * 100 : 0;

    const totalROI = purchasePrice > 0 ? ((currentValue - purchasePrice + netOperatingIncome) / purchasePrice) * 100 : 0;
    const breakEvenRatio = annualExpenses > 0 ? (annualExpenses / (estimatedRent * 12)) * 100 : 0;
    const pricePerSqft = totalSqft > 0 ? purchasePrice / totalSqft : 0;
    const rentToValueRatio = currentValue > 0 ? ((estimatedRent * 12) / currentValue) * 100 : 0;

    return {
      purchase_price: purchasePrice,
      current_value: currentValue,
      estimated_rent: estimatedRent,
      annual_expenses: annualExpenses,
      net_operating_income: netOperatingIncome,
      cap_rate: capRate,
      cash_on_cash_return: cashOnCashReturn,
      total_roi: totalROI,
      break_even_ratio: breakEvenRatio,
      price_per_sqft: pricePerSqft,
      rent_to_value_ratio: rentToValueRatio
    };
  };

  // Get rent multiplier based on property type and location
  const getRentMultiplier = (dorUc: string, county: string): number => {
    // Base multiplier (monthly rent as % of value)
    let multiplier = 0.008; // 0.8% default

    // Adjust by property type
    if (dorUc?.includes('SINGLE FAMILY')) multiplier = 0.008;
    else if (dorUc?.includes('CONDO')) multiplier = 0.009;
    else if (dorUc?.includes('TOWNHOUSE')) multiplier = 0.0085;
    else if (dorUc?.includes('MOBILE')) multiplier = 0.012;

    // Adjust by county (higher cost areas typically have lower rent ratios)
    const highCostCounties = ['MIAMI-DADE', 'BROWARD', 'PALM BEACH', 'ORANGE', 'PINELLAS'];
    if (highCostCounties.includes(county?.toUpperCase())) {
      multiplier *= 0.85; // Reduce by 15% for high-cost areas
    }

    return multiplier;
  };

  // Calculate detailed cash flow analysis
  const calculateCashFlowAnalysis = async (
    propertyData: any, purchasePrice: number, downPaymentPercent: number,
    interestRate: number, loanTermYears: number
  ): Promise<CashFlowAnalysis> => {
    const currentValue = parseFloat(propertyData.just_value) || purchasePrice;
    const rentMultiplier = getRentMultiplier(propertyData.dor_uc, propertyData.county);
    const monthlyRent = (currentValue * rentMultiplier) / 12;

    // Get NAV assessments for CDD/HOA fees
    const { data: navData } = await supabase
      .from('nav_assessments')
      .select('total_assessment')
      .eq('parcel_id', propertyData.parcel_id);

    const annualNavFees = (navData || []).reduce((sum, nav) => sum + parseFloat(nav.total_assessment), 0);

    const taxableValue = parseFloat(propertyData.taxable_value) || currentValue * 0.85;
    const monthlyExpenses = {
      property_taxes: (taxableValue * 0.015) / 12,
      insurance: (currentValue * 0.003) / 12,
      maintenance: monthlyRent * 0.10,
      property_management: monthlyRent * 0.08,
      vacancy_allowance: monthlyRent * 0.08,
      hoa_cdd_fees: annualNavFees / 12,
      other: monthlyRent * 0.02, // Miscellaneous 2%
      total: 0 // Will be calculated below
    };

    monthlyExpenses.total = Object.values(monthlyExpenses).reduce((sum, val) => sum + val, 0) - monthlyExpenses.total;

    const monthlyNetCashFlow = monthlyRent - monthlyExpenses.total;
    const annualCashFlow = monthlyNetCashFlow * 12;

    // Calculate financing costs if applicable
    const loanAmount = purchasePrice * (1 - downPaymentPercent / 100);
    let monthlyLoanPayment = 0;

    if (loanAmount > 0) {
      const monthlyRate = interestRate / 100 / 12;
      const numPayments = loanTermYears * 12;
      monthlyLoanPayment = loanAmount * (monthlyRate * Math.pow(1 + monthlyRate, numPayments)) /
        (Math.pow(1 + monthlyRate, numPayments) - 1);
    }

    const cashFlowMultiple = monthlyLoanPayment > 0 ? monthlyRent / monthlyLoanPayment : 0;

    return {
      monthly_rental_income: monthlyRent,
      monthly_expenses: monthlyExpenses,
      monthly_net_cash_flow: monthlyNetCashFlow - monthlyLoanPayment,
      annual_cash_flow: (monthlyNetCashFlow - monthlyLoanPayment) * 12,
      cash_flow_multiple: cashFlowMultiple
    };
  };

  // Perform competitive market analysis
  const performCompetitiveAnalysis = async (
    propertyData: any, parcelId: string
  ): Promise<CompetitiveAnalysis> => {
    try {
      // Find comparable properties in the area
      const { data: comps, error } = await supabase
        .from('florida_parcels')
        .select('parcel_id, phy_addr1, phy_city, just_value, total_living_area, sale_price, sale_date, dor_uc')
        .eq('county', propertyData.county)
        .eq('phy_city', propertyData.phy_city)
        .eq('dor_uc', propertyData.dor_uc)
        .neq('parcel_id', parcelId)
        .not('just_value', 'is', null)
        .gte('just_value', parseFloat(propertyData.just_value) * 0.7)
        .lte('just_value', parseFloat(propertyData.just_value) * 1.3)
        .limit(20);

      const comparableProperties = (comps || [])
        .filter(comp => comp.total_living_area > 0)
        .map(comp => {
          const sqft = parseFloat(comp.total_living_area) || 1;
          const value = parseFloat(comp.just_value) || 0;
          const salePrice = parseFloat(comp.sale_price) || value;

          return {
            parcel_id: comp.parcel_id,
            address: `${comp.phy_addr1}, ${comp.phy_city}`,
            distance_miles: 0, // Would need geocoding for accurate distance
            sale_price: salePrice,
            sale_date: comp.sale_date || new Date().toISOString().split('T')[0],
            sqft: sqft,
            price_per_sqft: value / sqft,
            similarity_score: calculateSimilarityScore(propertyData, comp)
          };
        })
        .sort((a, b) => b.similarity_score - a.similarity_score)
        .slice(0, 10);

      // Calculate market rent range
      const rentMultiplier = getRentMultiplier(propertyData.dor_uc, propertyData.county);
      const baseRent = (parseFloat(propertyData.just_value) * rentMultiplier) / 12;

      const marketRentRange = {
        low: baseRent * 0.85,
        median: baseRent,
        high: baseRent * 1.15
      };

      // Calculate area appreciation (simplified - would need historical data)
      const areaAppreciationRate = 3.5; // Default 3.5% for Florida
      const marketVelocity = 45; // Average days on market

      return {
        comparable_properties: comparableProperties,
        market_rent_range: marketRentRange,
        area_appreciation_rate: areaAppreciationRate,
        market_velocity: marketVelocity,
        inventory_levels: 'moderate' // Would need market data to determine
      };
    } catch (error) {
      console.log(`[useInvestmentAnalysis] Competitive analysis error:`, error);
      return {
        comparable_properties: [],
        market_rent_range: { low: 0, median: 0, high: 0 },
        area_appreciation_rate: 0,
        market_velocity: 0,
        inventory_levels: 'moderate'
      };
    }
  };

  // Calculate similarity score between properties
  const calculateSimilarityScore = (targetProp: any, compProp: any): number => {
    let score = 0;

    // Same property type
    if (targetProp.dor_uc === compProp.dor_uc) score += 30;

    // Similar square footage (within 20%)
    const targetSqft = parseFloat(targetProp.total_living_area) || 0;
    const compSqft = parseFloat(compProp.total_living_area) || 0;
    if (targetSqft > 0 && compSqft > 0) {
      const sqftDiff = Math.abs(targetSqft - compSqft) / targetSqft;
      if (sqftDiff <= 0.2) score += 25;
      else if (sqftDiff <= 0.4) score += 15;
    }

    // Similar value (within 30%)
    const targetValue = parseFloat(targetProp.just_value) || 0;
    const compValue = parseFloat(compProp.just_value) || 0;
    if (targetValue > 0 && compValue > 0) {
      const valueDiff = Math.abs(targetValue - compValue) / targetValue;
      if (valueDiff <= 0.3) score += 25;
      else if (valueDiff <= 0.5) score += 15;
    }

    // Similar age
    const targetAge = new Date().getFullYear() - (parseInt(targetProp.year_built) || 1990);
    const compAge = new Date().getFullYear() - (parseInt(compProp.year_built) || 1990);
    const ageDiff = Math.abs(targetAge - compAge);
    if (ageDiff <= 5) score += 20;
    else if (ageDiff <= 10) score += 10;

    return score;
  };

  // Assess investment risks
  const assessRisks = async (propertyData: any, parcelId: string): Promise<RiskAssessment> => {
    const riskFactors: RiskAssessment['risk_factors'] = [];
    const opportunities: RiskAssessment['opportunities'] = [];
    let riskScore = 30; // Start at moderate risk

    // Check for tax certificates
    const { data: taxCerts } = await supabase
      .from('tax_certificates')
      .select('*')
      .eq('parcel_id', parcelId);

    if (taxCerts && taxCerts.length > 0) {
      riskFactors.push({
        category: 'Financial',
        factor: 'Tax Certificate History',
        impact: 'high',
        description: `Property has ${taxCerts.length} tax certificate(s) indicating past delinquencies`
      });
      riskScore += 20;
    }

    // Check for high NAV assessments
    const { data: navData } = await supabase
      .from('nav_assessments')
      .select('*')
      .eq('parcel_id', parcelId);

    const totalNavAssessment = (navData || []).reduce((sum, nav) => sum + parseFloat(nav.total_assessment), 0);
    if (totalNavAssessment > 5000) {
      riskFactors.push({
        category: 'Financial',
        factor: 'High CDD Assessments',
        impact: 'high',
        description: `Annual CDD fees of $${totalNavAssessment.toFixed(0)} significantly impact cash flow`
      });
      riskScore += 15;
    } else if (totalNavAssessment > 1000) {
      riskFactors.push({
        category: 'Financial',
        factor: 'Moderate CDD Assessments',
        impact: 'medium',
        description: `Annual CDD fees of $${totalNavAssessment.toFixed(0)} may impact cash flow`
      });
      riskScore += 8;
    }

    // Property age risk
    const yearBuilt = parseInt(propertyData.year_built) || 1990;
    const propertyAge = new Date().getFullYear() - yearBuilt;
    if (propertyAge > 50) {
      riskFactors.push({
        category: 'Property',
        factor: 'Older Property',
        impact: 'medium',
        description: `Property built in ${yearBuilt} may require significant maintenance and updates`
      });
      riskScore += 10;
    }

    // Market opportunities
    const justValue = parseFloat(propertyData.just_value) || 0;
    if (justValue > 100000 && justValue < 400000) {
      opportunities.push({
        category: 'Market',
        opportunity: 'Affordable Price Range',
        potential: 'high',
        description: 'Property is in strong rental demand price range for Florida market'
      });
    }

    // Property type opportunity
    if (propertyData.dor_uc?.includes('SINGLE FAMILY')) {
      opportunities.push({
        category: 'Property',
        opportunity: 'Single Family Home',
        potential: 'medium',
        description: 'Single family homes typically appreciate well and have stable rental demand'
      });
    }

    return {
      overall_risk_score: Math.min(100, Math.max(0, riskScore)),
      risk_factors: riskFactors,
      opportunities: opportunities
    };
  };

  // Generate investment scenarios
  const generateInvestmentScenarios = async (
    propertyData: any, purchasePrice: number
  ): Promise<InvestmentScenarios> => {
    const currentValue = parseFloat(propertyData.just_value) || purchasePrice;

    const scenarios = {
      conservative: {
        appreciation_rate: 2.5,
        rent_growth_rate: 2.0,
        vacancy_rate: 10.0,
        expense_growth_rate: 3.0,
        five_year_value: 0,
        five_year_equity: 0,
        five_year_total_return: 0
      },
      moderate: {
        appreciation_rate: 4.0,
        rent_growth_rate: 3.0,
        vacancy_rate: 7.0,
        expense_growth_rate: 2.5,
        five_year_value: 0,
        five_year_equity: 0,
        five_year_total_return: 0
      },
      optimistic: {
        appreciation_rate: 6.0,
        rent_growth_rate: 4.0,
        vacancy_rate: 5.0,
        expense_growth_rate: 2.0,
        five_year_value: 0,
        five_year_equity: 0,
        five_year_total_return: 0
      }
    };

    // Calculate projections for each scenario
    Object.keys(scenarios).forEach(scenarioKey => {
      const scenario = scenarios[scenarioKey as keyof typeof scenarios];

      // Five-year projected value
      scenario.five_year_value = currentValue * Math.pow(1 + scenario.appreciation_rate / 100, 5);

      // Five-year equity (assuming 25% down, 30-year loan)
      const downPayment = purchasePrice * 0.25;
      const loanAmount = purchasePrice * 0.75;
      const monthlyRate = 0.07 / 12; // 7% interest
      const paymentsRemaining = (30 * 12) - (5 * 12); // 25 years remaining
      const remainingBalance = loanAmount *
        (Math.pow(1 + monthlyRate, paymentsRemaining) - 1) /
        (Math.pow(1 + monthlyRate, 30 * 12) - 1);

      scenario.five_year_equity = scenario.five_year_value - remainingBalance;

      // Five-year total return
      const totalEquityGain = scenario.five_year_equity - downPayment;
      scenario.five_year_total_return = (totalEquityGain / downPayment) * 100;
    });

    return scenarios;
  };

  // Generate overall recommendation
  const generateRecommendation = (
    metrics: PropertyMetrics,
    cashFlow: CashFlowAnalysis,
    competitive: CompetitiveAnalysis,
    risk: RiskAssessment
  ): InvestmentAnalysis['recommendation'] => {
    let score = 50; // Base score
    const keyPoints: string[] = [];

    // Cap rate scoring
    if (metrics.cap_rate > 8) {
      score += 20;
      keyPoints.push(`Excellent cap rate of ${metrics.cap_rate.toFixed(2)}%`);
    } else if (metrics.cap_rate > 6) {
      score += 10;
      keyPoints.push(`Good cap rate of ${metrics.cap_rate.toFixed(2)}%`);
    } else if (metrics.cap_rate < 4) {
      score -= 10;
      keyPoints.push(`Low cap rate of ${metrics.cap_rate.toFixed(2)}% may limit returns`);
    }

    // Cash flow scoring
    if (cashFlow.monthly_net_cash_flow > 500) {
      score += 15;
      keyPoints.push(`Strong monthly cash flow of $${cashFlow.monthly_net_cash_flow.toFixed(0)}`);
    } else if (cashFlow.monthly_net_cash_flow > 0) {
      score += 5;
      keyPoints.push(`Positive monthly cash flow of $${cashFlow.monthly_net_cash_flow.toFixed(0)}`);
    } else {
      score -= 15;
      keyPoints.push(`Negative monthly cash flow of $${cashFlow.monthly_net_cash_flow.toFixed(0)}`);
    }

    // Risk adjustment
    score -= (risk.overall_risk_score - 30) * 0.5; // Adjust for risk above/below moderate

    if (risk.risk_factors.length > 3) {
      keyPoints.push(`${risk.risk_factors.length} significant risk factors identified`);
    }

    // Market conditions
    if (competitive.area_appreciation_rate > 5) {
      score += 10;
      keyPoints.push(`Strong market appreciation of ${competitive.area_appreciation_rate}%`);
    }

    // Final score and grade
    score = Math.max(0, Math.min(100, score));
    let grade: 'A' | 'B' | 'C' | 'D' | 'F';
    let action: 'strong_buy' | 'buy' | 'hold' | 'pass' | 'avoid';
    let summary: string;

    if (score >= 80) {
      grade = 'A';
      action = 'strong_buy';
      summary = 'Excellent investment opportunity with strong fundamentals and cash flow potential.';
    } else if (score >= 70) {
      grade = 'B';
      action = 'buy';
      summary = 'Good investment opportunity with solid returns and manageable risk.';
    } else if (score >= 60) {
      grade = 'C';
      action = 'hold';
      summary = 'Moderate investment opportunity. Consider local market conditions carefully.';
    } else if (score >= 40) {
      grade = 'D';
      action = 'pass';
      summary = 'Below-average investment opportunity with significant challenges.';
    } else {
      grade = 'F';
      action = 'avoid';
      summary = 'Poor investment opportunity with high risk and low return potential.';
    }

    return {
      score,
      grade,
      action,
      summary,
      key_points: keyPoints
    };
  };

  return {
    analysis,
    loading,
    error,
    refetch: () => parcelId && performAnalysis(parcelId, purchasePrice),
  };
}