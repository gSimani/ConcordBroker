/**
 * Comprehensive Property Investment Calculations
 * Advanced financial calculations for real estate investment analysis
 */

export interface PropertyFinancials {
  // Basic property info
  purchasePrice: number;
  currentValue: number;
  rentEstimate: number;
  operatingExpenses: number;
  propertyTaxes: number;
  insurance: number;
  maintenance: number;
  vacancy: number;
  management: number;

  // Financing details
  downPayment: number;
  loanAmount: number;
  interestRate: number;
  loanTerm: number;

  // Additional costs
  closingCosts: number;
  renovationCosts: number;

  // Property characteristics
  squareFootage: number;
  lotSize: number;
  yearBuilt: number;
  bedrooms: number;
  bathrooms: number;
}

export interface CalculationResults {
  // Cash flow metrics
  grossMonthlyIncome: number;
  netMonthlyIncome: number;
  monthlyOperatingExpenses: number;
  monthlyCashFlow: number;
  annualCashFlow: number;

  // Return metrics
  capRate: number;
  cashOnCashReturn: number;
  totalROI: number;
  grossRentMultiplier: number;

  // Ratios and efficiency
  rentToValueRatio: number;
  expenseRatio: number;
  debtServiceCoverageRatio: number;

  // Investment metrics
  paybackPeriod: number;
  breakEvenAnalysis: number;

  // Risk metrics
  cashFlowRisk: 'Low' | 'Medium' | 'High';
  marketRisk: 'Low' | 'Medium' | 'High';
  liquidityRisk: 'Low' | 'Medium' | 'High';

  // Appreciation and projections
  projectedAppreciation: number[];
  projectedCashFlow: number[];
  projectedValue: number[];

  // Comparative metrics
  pricePerSquareFoot: number;
  rentPerSquareFoot: number;

  // Tax implications
  depreciation: number;
  taxBenefits: number;

  // Scenario analysis
  optimisticScenario: ScenarioResults;
  pessimisticScenario: ScenarioResults;
  mostLikelyScenario: ScenarioResults;
}

export interface ScenarioResults {
  annualCashFlow: number;
  totalReturn: number;
  exitValue: number;
  totalProfit: number;
}

export interface MarketComparables {
  averageRent: number;
  averagePrice: number;
  averagePricePerSqFt: number;
  averageCapRate: number;
  averageDaysOnMarket: number;
  salesVolume: number;
  appreciation: number;
}

export class PropertyCalculations {

  /**
   * Calculate comprehensive investment metrics
   */
  static calculateInvestmentMetrics(financials: PropertyFinancials): CalculationResults {
    // Basic calculations
    const monthlyRent = financials.rentEstimate;
    const grossMonthlyIncome = monthlyRent;
    const monthlyTaxes = financials.propertyTaxes / 12;
    const monthlyInsurance = financials.insurance / 12;
    const monthlyMaintenance = monthlyRent * (financials.maintenance / 100);
    const monthlyVacancy = monthlyRent * (financials.vacancy / 100);
    const monthlyManagement = monthlyRent * (financials.management / 100);

    const monthlyOperatingExpenses = monthlyTaxes + monthlyInsurance +
                                   monthlyMaintenance + monthlyVacancy + monthlyManagement;

    // Monthly mortgage payment
    const monthlyMortgagePayment = this.calculateMortgagePayment(
      financials.loanAmount,
      financials.interestRate,
      financials.loanTerm
    );

    const netMonthlyIncome = grossMonthlyIncome - monthlyOperatingExpenses;
    const monthlyCashFlow = netMonthlyIncome - monthlyMortgagePayment;
    const annualCashFlow = monthlyCashFlow * 12;

    // Return calculations
    const capRate = ((grossMonthlyIncome * 12) - (monthlyOperatingExpenses * 12)) / financials.currentValue * 100;
    const cashInvested = financials.downPayment + financials.closingCosts + financials.renovationCosts;
    const cashOnCashReturn = annualCashFlow / cashInvested * 100;

    // Additional metrics
    const grossRentMultiplier = financials.currentValue / (monthlyRent * 12);
    const rentToValueRatio = (monthlyRent * 12) / financials.currentValue * 100;
    const expenseRatio = (monthlyOperatingExpenses * 12) / (monthlyRent * 12) * 100;

    const paybackPeriod = cashInvested / Math.max(annualCashFlow, 1);

    // Risk assessment
    const cashFlowRisk = this.assessCashFlowRisk(monthlyCashFlow, monthlyRent);
    const marketRisk = this.assessMarketRisk(financials.yearBuilt, financials.currentValue);
    const liquidityRisk = this.assessLiquidityRisk(financials.currentValue, financials.squareFootage);

    // Projections
    const projections = this.calculateProjections(financials, annualCashFlow);

    // Price metrics
    const pricePerSquareFoot = financials.currentValue / financials.squareFootage;
    const rentPerSquareFoot = (monthlyRent * 12) / financials.squareFootage;

    // Tax calculations
    const depreciation = this.calculateDepreciation(financials.currentValue, financials.yearBuilt);
    const taxBenefits = this.calculateTaxBenefits(depreciation, monthlyOperatingExpenses * 12);

    // Scenario analysis
    const scenarios = this.performScenarioAnalysis(financials, annualCashFlow);

    return {
      grossMonthlyIncome,
      netMonthlyIncome,
      monthlyOperatingExpenses,
      monthlyCashFlow,
      annualCashFlow,
      capRate,
      cashOnCashReturn,
      totalROI: cashOnCashReturn, // Simplified for now
      grossRentMultiplier,
      rentToValueRatio,
      expenseRatio,
      debtServiceCoverageRatio: netMonthlyIncome / monthlyMortgagePayment,
      paybackPeriod,
      breakEvenAnalysis: monthlyOperatingExpenses + monthlyMortgagePayment,
      cashFlowRisk,
      marketRisk,
      liquidityRisk,
      projectedAppreciation: projections.appreciation,
      projectedCashFlow: projections.cashFlow,
      projectedValue: projections.value,
      pricePerSquareFoot,
      rentPerSquareFoot,
      depreciation,
      taxBenefits,
      optimisticScenario: scenarios.optimistic,
      pessimisticScenario: scenarios.pessimistic,
      mostLikelyScenario: scenarios.mostLikely
    };
  }

  /**
   * Calculate monthly mortgage payment
   */
  static calculateMortgagePayment(loanAmount: number, annualRate: number, termYears: number): number {
    if (loanAmount === 0 || annualRate === 0) return 0;

    const monthlyRate = annualRate / 100 / 12;
    const numPayments = termYears * 12;

    return loanAmount * (monthlyRate * Math.pow(1 + monthlyRate, numPayments)) /
           (Math.pow(1 + monthlyRate, numPayments) - 1);
  }

  /**
   * Assess cash flow risk based on cash flow stability
   */
  static assessCashFlowRisk(monthlyCashFlow: number, monthlyRent: number): 'Low' | 'Medium' | 'High' {
    const cashFlowRatio = monthlyCashFlow / monthlyRent;

    if (cashFlowRatio > 0.3) return 'Low';
    if (cashFlowRatio > 0.1) return 'Medium';
    return 'High';
  }

  /**
   * Assess market risk based on property characteristics
   */
  static assessMarketRisk(yearBuilt: number, currentValue: number): 'Low' | 'Medium' | 'High' {
    const currentYear = new Date().getFullYear();
    const propertyAge = currentYear - yearBuilt;

    if (propertyAge < 10 && currentValue > 200000) return 'Low';
    if (propertyAge < 30 && currentValue > 100000) return 'Medium';
    return 'High';
  }

  /**
   * Assess liquidity risk based on market characteristics
   */
  static assessLiquidityRisk(currentValue: number, squareFootage: number): 'Low' | 'Medium' | 'High' {
    const pricePerSqFt = currentValue / squareFootage;

    if (pricePerSqFt > 150 && pricePerSqFt < 400 && squareFootage > 1000) return 'Low';
    if (pricePerSqFt > 100 && pricePerSqFt < 500) return 'Medium';
    return 'High';
  }

  /**
   * Calculate future projections
   */
  static calculateProjections(financials: PropertyFinancials, baseAnnualCashFlow: number) {
    const years = 10;
    const appreciationRate = 0.03; // 3% annual appreciation
    const rentGrowthRate = 0.025; // 2.5% annual rent growth

    const appreciation = [];
    const cashFlow = [];
    const value = [];

    for (let year = 1; year <= years; year++) {
      const projectedValue = financials.currentValue * Math.pow(1 + appreciationRate, year);
      const projectedRent = financials.rentEstimate * Math.pow(1 + rentGrowthRate, year);
      const projectedCashFlow = baseAnnualCashFlow * Math.pow(1 + rentGrowthRate, year);

      appreciation.push(appreciationRate * 100);
      cashFlow.push(projectedCashFlow);
      value.push(projectedValue);
    }

    return { appreciation, cashFlow, value };
  }

  /**
   * Calculate depreciation for tax purposes
   */
  static calculateDepreciation(currentValue: number, yearBuilt: number): number {
    // Residential rental property depreciates over 27.5 years
    const depreciationPeriod = 27.5;
    const buildingValue = currentValue * 0.8; // Assume 80% building, 20% land

    return buildingValue / depreciationPeriod;
  }

  /**
   * Calculate tax benefits
   */
  static calculateTaxBenefits(depreciation: number, operatingExpenses: number): number {
    const taxRate = 0.22; // Assumed tax rate
    const deductibleExpenses = depreciation + operatingExpenses;

    return deductibleExpenses * taxRate;
  }

  /**
   * Perform scenario analysis
   */
  static performScenarioAnalysis(financials: PropertyFinancials, baseCashFlow: number) {
    const optimistic: ScenarioResults = {
      annualCashFlow: baseCashFlow * 1.3,
      totalReturn: baseCashFlow * 1.3 * 10,
      exitValue: financials.currentValue * 1.5,
      totalProfit: (baseCashFlow * 1.3 * 10) + (financials.currentValue * 0.5)
    };

    const pessimistic: ScenarioResults = {
      annualCashFlow: baseCashFlow * 0.7,
      totalReturn: baseCashFlow * 0.7 * 10,
      exitValue: financials.currentValue * 1.1,
      totalProfit: (baseCashFlow * 0.7 * 10) + (financials.currentValue * 0.1)
    };

    const mostLikely: ScenarioResults = {
      annualCashFlow: baseCashFlow,
      totalReturn: baseCashFlow * 10,
      exitValue: financials.currentValue * 1.3,
      totalProfit: (baseCashFlow * 10) + (financials.currentValue * 0.3)
    };

    return { optimistic, pessimistic, mostLikely };
  }

  /**
   * Compare with market comparables
   */
  static compareWithMarket(
    propertyMetrics: CalculationResults,
    marketComparables: MarketComparables
  ) {
    return {
      capRateComparison: propertyMetrics.capRate - marketComparables.averageCapRate,
      priceComparison: propertyMetrics.pricePerSquareFoot - marketComparables.averagePricePerSqFt,
      rentComparison: propertyMetrics.rentPerSquareFoot - (marketComparables.averageRent / 12),
      valuePosition: propertyMetrics.pricePerSquareFoot > marketComparables.averagePricePerSqFt ? 'Above Market' : 'Below Market'
    };
  }

  /**
   * Calculate break-even analysis
   */
  static calculateBreakEven(financials: PropertyFinancials): {
    breakEvenRent: number;
    breakEvenOccupancy: number;
    breakEvenPurchasePrice: number;
  } {
    const monthlyExpenses = (financials.propertyTaxes + financials.insurance) / 12 +
                           financials.rentEstimate * (financials.maintenance + financials.management) / 100;

    const monthlyMortgage = this.calculateMortgagePayment(
      financials.loanAmount,
      financials.interestRate,
      financials.loanTerm
    );

    const breakEvenRent = monthlyExpenses + monthlyMortgage;
    const breakEvenOccupancy = breakEvenRent / financials.rentEstimate * 100;

    // Calculate what purchase price would break even with current rent
    const maxLoanForBreakEven = this.calculateMaxLoan(
      financials.rentEstimate - monthlyExpenses,
      financials.interestRate,
      financials.loanTerm
    );
    const breakEvenPurchasePrice = maxLoanForBreakEven + financials.downPayment;

    return {
      breakEvenRent,
      breakEvenOccupancy,
      breakEvenPurchasePrice
    };
  }

  /**
   * Calculate maximum loan amount for given payment
   */
  static calculateMaxLoan(monthlyPayment: number, annualRate: number, termYears: number): number {
    if (monthlyPayment <= 0 || annualRate <= 0) return 0;

    const monthlyRate = annualRate / 100 / 12;
    const numPayments = termYears * 12;

    return monthlyPayment * (Math.pow(1 + monthlyRate, numPayments) - 1) /
           (monthlyRate * Math.pow(1 + monthlyRate, numPayments));
  }

  /**
   * Calculate DSCR (Debt Service Coverage Ratio)
   */
  static calculateDSCR(
    netOperatingIncome: number,
    totalDebtService: number
  ): number {
    return totalDebtService > 0 ? netOperatingIncome / totalDebtService : 0;
  }

  /**
   * Calculate IRR (Internal Rate of Return) approximation
   */
  static calculateIRR(
    initialInvestment: number,
    cashFlows: number[],
    finalValue: number
  ): number {
    // Simplified IRR calculation using Newton-Raphson method
    let rate = 0.1; // Initial guess: 10%
    const tolerance = 0.0001;
    const maxIterations = 100;

    for (let i = 0; i < maxIterations; i++) {
      let npv = -initialInvestment;
      let dnpv = 0;

      // Calculate NPV and its derivative
      for (let year = 0; year < cashFlows.length; year++) {
        const discountFactor = Math.pow(1 + rate, year + 1);
        npv += cashFlows[year] / discountFactor;
        dnpv -= (year + 1) * cashFlows[year] / Math.pow(1 + rate, year + 2);
      }

      // Add final value
      const finalDiscountFactor = Math.pow(1 + rate, cashFlows.length);
      npv += finalValue / finalDiscountFactor;
      dnpv -= cashFlows.length * finalValue / Math.pow(1 + rate, cashFlows.length + 1);

      if (Math.abs(npv) < tolerance) {
        return rate * 100;
      }

      rate = rate - npv / dnpv;

      // Prevent negative rates
      if (rate < 0) rate = 0.01;
    }

    return rate * 100;
  }

  /**
   * Calculate property investment score (0-100)
   */
  static calculateInvestmentScore(metrics: CalculationResults): number {
    let score = 50; // Base score

    // Cap rate scoring (30% weight)
    if (metrics.capRate > 8) score += 15;
    else if (metrics.capRate > 6) score += 10;
    else if (metrics.capRate > 4) score += 5;
    else if (metrics.capRate < 2) score -= 10;

    // Cash flow scoring (25% weight)
    if (metrics.monthlyCashFlow > 500) score += 12;
    else if (metrics.monthlyCashFlow > 200) score += 8;
    else if (metrics.monthlyCashFlow > 0) score += 4;
    else score -= 15;

    // Cash-on-cash return scoring (20% weight)
    if (metrics.cashOnCashReturn > 12) score += 10;
    else if (metrics.cashOnCashReturn > 8) score += 6;
    else if (metrics.cashOnCashReturn > 4) score += 3;
    else if (metrics.cashOnCashReturn < 0) score -= 10;

    // Risk assessment (15% weight)
    if (metrics.cashFlowRisk === 'Low') score += 7;
    else if (metrics.cashFlowRisk === 'Medium') score += 3;
    else score -= 5;

    if (metrics.marketRisk === 'Low') score += 4;
    else if (metrics.marketRisk === 'Medium') score += 2;
    else score -= 3;

    // Efficiency metrics (10% weight)
    if (metrics.expenseRatio < 40) score += 5;
    else if (metrics.expenseRatio > 60) score -= 3;

    if (metrics.debtServiceCoverageRatio > 1.25) score += 3;
    else if (metrics.debtServiceCoverageRatio < 1.1) score -= 5;

    // Ensure score is between 0 and 100
    return Math.max(0, Math.min(100, Math.round(score)));
  }
}

/**
 * Market Analysis Utilities
 */
export class MarketAnalysis {

  /**
   * Calculate market velocity and trends
   */
  static calculateMarketVelocity(
    salesData: { date: string; price: number; daysOnMarket: number }[]
  ) {
    const recentSales = salesData.filter(sale =>
      new Date(sale.date) > new Date(Date.now() - 90 * 24 * 60 * 60 * 1000) // Last 90 days
    );

    const avgDaysOnMarket = recentSales.reduce((sum, sale) => sum + sale.daysOnMarket, 0) / recentSales.length;
    const avgPrice = recentSales.reduce((sum, sale) => sum + sale.price, 0) / recentSales.length;

    const velocity = avgDaysOnMarket < 30 ? 'Fast' : avgDaysOnMarket < 60 ? 'Moderate' : 'Slow';

    return {
      velocity,
      avgDaysOnMarket,
      avgPrice,
      salesVolume: recentSales.length,
      trend: this.calculatePriceTrend(salesData)
    };
  }

  /**
   * Calculate price trend from sales data
   */
  static calculatePriceTrend(salesData: { date: string; price: number }[]) {
    if (salesData.length < 2) return 'Stable';

    const sortedSales = salesData.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    const oldSales = sortedSales.slice(0, Math.floor(sortedSales.length / 2));
    const newSales = sortedSales.slice(Math.floor(sortedSales.length / 2));

    const oldAvg = oldSales.reduce((sum, sale) => sum + sale.price, 0) / oldSales.length;
    const newAvg = newSales.reduce((sum, sale) => sum + sale.price, 0) / newSales.length;

    const change = (newAvg - oldAvg) / oldAvg;

    if (change > 0.05) return 'Rising';
    if (change < -0.05) return 'Declining';
    return 'Stable';
  }

  /**
   * Calculate comparable property analysis
   */
  static analyzeComparables(
    targetProperty: { price: number; sqft: number; bedrooms: number; bathrooms: number },
    comparables: Array<{ price: number; sqft: number; bedrooms: number; bathrooms: number }>
  ) {
    const relevantComps = comparables.filter(comp =>
      Math.abs(comp.bedrooms - targetProperty.bedrooms) <= 1 &&
      Math.abs(comp.bathrooms - targetProperty.bathrooms) <= 1 &&
      comp.sqft >= targetProperty.sqft * 0.8 &&
      comp.sqft <= targetProperty.sqft * 1.2
    );

    if (relevantComps.length === 0) return null;

    const avgPrice = relevantComps.reduce((sum, comp) => sum + comp.price, 0) / relevantComps.length;
    const avgPricePerSqFt = relevantComps.reduce((sum, comp) => sum + (comp.price / comp.sqft), 0) / relevantComps.length;

    const targetPricePerSqFt = targetProperty.price / targetProperty.sqft;
    const priceVariance = (targetPricePerSqFt - avgPricePerSqFt) / avgPricePerSqFt;

    return {
      avgPrice,
      avgPricePerSqFt,
      targetPricePerSqFt,
      priceVariance: priceVariance * 100,
      comparableCount: relevantComps.length,
      marketPosition: priceVariance > 0.1 ? 'Above Market' : priceVariance < -0.1 ? 'Below Market' : 'Market Rate'
    };
  }
}