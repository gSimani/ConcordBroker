// Property Analytics Module with NumPy-style calculations
// This module provides comprehensive data analysis for properties

import * as math from 'mathjs'

export interface PropertyMetrics {
  // Financial Metrics
  roi: number
  capRate: number
  grossRentMultiplier: number
  cashFlow: number
  pricePerSqft: number
  landValueRatio: number
  improvementRatio: number

  // Market Analysis
  marketTrend: 'appreciating' | 'stable' | 'depreciating'
  priceDeviation: number
  daysOnMarket: number
  listToSaleRatio: number

  // Risk Metrics
  riskScore: number
  volatilityIndex: number
  liquidityScore: number

  // Comparative Metrics
  neighborhoodAvgPrice: number
  percentileRank: number
  valueScore: number
}

export interface TaxCalculations {
  effectiveTaxRate: number
  monthlyTaxPayment: number
  annualTaxSavings: number
  homesteadSavings: number
  totalExemptions: number
  millageBreakdown: {
    county: number
    school: number
    city: number
    special: number
  }
}

export interface InvestmentAnalysis {
  npv: number // Net Present Value
  irr: number // Internal Rate of Return
  paybackPeriod: number // Years to recover investment
  breakEvenPoint: number
  equityBuildup: number[]
  appreciationForecast: number[]
  totalReturn: number
}

export class PropertyAnalytics {
  // Calculate Return on Investment
  static calculateROI(
    purchasePrice: number,
    currentValue: number,
    rentalIncome: number,
    expenses: number,
    years: number = 1
  ): number {
    const totalRentalIncome = rentalIncome * 12 * years
    const totalExpenses = expenses * 12 * years
    const netProfit = (currentValue - purchasePrice) + totalRentalIncome - totalExpenses
    return (netProfit / purchasePrice) * 100
  }

  // Calculate Capitalization Rate
  static calculateCapRate(
    netOperatingIncome: number,
    propertyValue: number
  ): number {
    if (propertyValue === 0) return 0
    return (netOperatingIncome / propertyValue) * 100
  }

  // Calculate Gross Rent Multiplier
  static calculateGRM(
    propertyPrice: number,
    monthlyRent: number
  ): number {
    if (monthlyRent === 0) return 0
    const annualRent = monthlyRent * 12
    return propertyPrice / annualRent
  }

  // Calculate Cash Flow
  static calculateCashFlow(
    rentalIncome: number,
    mortgage: number,
    taxes: number,
    insurance: number,
    hoa: number,
    maintenance: number,
    management: number = 0
  ): number {
    const totalExpenses = mortgage + taxes + insurance + hoa + maintenance + management
    return rentalIncome - totalExpenses
  }

  // Statistical Analysis using math.js (NumPy-like operations)
  static calculateStatistics(values: number[]): {
    mean: number
    median: number
    std: number
    variance: number
    min: number
    max: number
    q1: number
    q3: number
    iqr: number
    outliers: number[]
  } {
    if (!values || values.length === 0) {
      return {
        mean: 0, median: 0, std: 0, variance: 0,
        min: 0, max: 0, q1: 0, q3: 0, iqr: 0, outliers: []
      }
    }

    const sorted = [...values].sort((a, b) => a - b)
    const mean = math.mean(values)
    const median = math.median(values)
    const std = math.std(values)
    const variance = math.variance(values)

    // Quartiles
    const q1Index = Math.floor(sorted.length * 0.25)
    const q3Index = Math.floor(sorted.length * 0.75)
    const q1 = sorted[q1Index]
    const q3 = sorted[q3Index]
    const iqr = q3 - q1

    // Find outliers using IQR method
    const lowerBound = q1 - 1.5 * iqr
    const upperBound = q3 + 1.5 * iqr
    const outliers = values.filter(v => v < lowerBound || v > upperBound)

    return {
      mean,
      median,
      std: typeof std === 'number' ? std : 0,
      variance: typeof variance === 'number' ? variance : 0,
      min: Math.min(...values),
      max: Math.max(...values),
      q1,
      q3,
      iqr,
      outliers
    }
  }

  // Price Trend Analysis
  static analyzePriceTrend(
    salesHistory: Array<{ date: string; price: number }>
  ): {
    trend: 'up' | 'down' | 'stable'
    slope: number
    r2: number
    forecast: number[]
  } {
    if (!salesHistory || salesHistory.length < 2) {
      return { trend: 'stable', slope: 0, r2: 0, forecast: [] }
    }

    // Convert dates to numeric values (days from first sale)
    const firstDate = new Date(salesHistory[0].date).getTime()
    const points = salesHistory.map(sale => ({
      x: (new Date(sale.date).getTime() - firstDate) / (1000 * 60 * 60 * 24),
      y: sale.price
    }))

    // Linear regression using math.js
    const xValues = points.map(p => p.x)
    const yValues = points.map(p => p.y)

    // Calculate slope and intercept
    const n = points.length
    const sumX = math.sum(xValues)
    const sumY = math.sum(yValues)
    const sumXY = math.sum(xValues.map((x, i) => x * yValues[i]))
    const sumX2 = math.sum(xValues.map(x => x * x))

    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX)
    const intercept = (sumY - slope * sumX) / n

    // Calculate R-squared
    const yMean = math.mean(yValues)
    const ssRes = math.sum(yValues.map((y, i) => Math.pow(y - (slope * xValues[i] + intercept), 2)))
    const ssTot = math.sum(yValues.map(y => Math.pow(y - yMean, 2)))
    const r2 = 1 - (ssRes / ssTot)

    // Forecast next 5 years
    const lastX = Math.max(...xValues)
    const forecast = [1, 2, 3, 4, 5].map(years => {
      const futureX = lastX + (years * 365)
      return slope * futureX + intercept
    })

    // Determine trend
    let trend: 'up' | 'down' | 'stable'
    if (Math.abs(slope) < 10) trend = 'stable'
    else if (slope > 0) trend = 'up'
    else trend = 'down'

    return { trend, slope, r2, forecast }
  }

  // Market Comparison Analysis
  static compareToMarket(
    propertyValue: number,
    comparables: number[]
  ): {
    percentile: number
    zScore: number
    isUndervalued: boolean
    isOvervalued: boolean
    fairValue: number
  } {
    if (!comparables || comparables.length === 0) {
      return {
        percentile: 50,
        zScore: 0,
        isUndervalued: false,
        isOvervalued: false,
        fairValue: propertyValue
      }
    }

    const stats = this.calculateStatistics(comparables)

    // Calculate percentile
    const below = comparables.filter(v => v < propertyValue).length
    const percentile = (below / comparables.length) * 100

    // Calculate z-score
    const zScore = stats.std > 0 ? (propertyValue - stats.mean) / stats.std : 0

    // Determine if under/overvalued
    const isUndervalued = zScore < -1
    const isOvervalued = zScore > 1

    // Fair value is the median of comparables
    const fairValue = stats.median

    return {
      percentile,
      zScore,
      isUndervalued,
      isOvervalued,
      fairValue
    }
  }

  // Tax Analysis
  static analyzeTaxes(
    assessedValue: number,
    taxableValue: number,
    exemptions: number,
    millageRate: number,
    homesteadExemption: boolean
  ): TaxCalculations {
    const baseExemption = homesteadExemption ? 50000 : 0
    const totalExemptions = exemptions + baseExemption

    const adjustedTaxableValue = Math.max(0, taxableValue - totalExemptions)
    const annualTax = (adjustedTaxableValue / 1000) * millageRate
    const monthlyTax = annualTax / 12

    const effectiveRate = assessedValue > 0 ? (annualTax / assessedValue) * 100 : 0
    const homesteadSavings = homesteadExemption ? (baseExemption / 1000) * millageRate : 0

    // Typical millage breakdown (example for Broward County)
    const millageBreakdown = {
      county: millageRate * 0.35,
      school: millageRate * 0.40,
      city: millageRate * 0.15,
      special: millageRate * 0.10
    }

    return {
      effectiveTaxRate: effectiveRate,
      monthlyTaxPayment: monthlyTax,
      annualTaxSavings: totalExemptions * millageRate / 1000,
      homesteadSavings,
      totalExemptions,
      millageBreakdown
    }
  }

  // Investment Analysis with NPV and IRR
  static analyzeInvestment(
    initialInvestment: number,
    cashFlows: number[],
    appreciationRate: number = 0.03,
    discountRate: number = 0.08
  ): InvestmentAnalysis {
    // Calculate NPV
    let npv = -initialInvestment
    cashFlows.forEach((cf, i) => {
      npv += cf / Math.pow(1 + discountRate, i + 1)
    })

    // Calculate IRR using Newton's method
    let irr = 0.1 // Initial guess
    for (let i = 0; i < 100; i++) {
      let npvAtRate = -initialInvestment
      let npvDerivative = 0

      cashFlows.forEach((cf, j) => {
        const t = j + 1
        npvAtRate += cf / Math.pow(1 + irr, t)
        npvDerivative -= t * cf / Math.pow(1 + irr, t + 1)
      })

      const newIrr = irr - npvAtRate / npvDerivative
      if (Math.abs(newIrr - irr) < 0.0001) break
      irr = newIrr
    }

    // Calculate payback period
    let cumulative = -initialInvestment
    let paybackPeriod = 0
    for (let i = 0; i < cashFlows.length; i++) {
      cumulative += cashFlows[i]
      if (cumulative >= 0) {
        paybackPeriod = i + 1 - (cumulative - cashFlows[i]) / cashFlows[i]
        break
      }
    }

    // Calculate break-even point
    const breakEvenPoint = initialInvestment / (cashFlows[0] / 12)

    // Calculate equity buildup
    const equityBuildup = cashFlows.map((_, i) => {
      return initialInvestment * Math.pow(1 + appreciationRate, i + 1)
    })

    // Appreciation forecast
    const appreciationForecast = [1, 3, 5, 7, 10].map(years => {
      return initialInvestment * Math.pow(1 + appreciationRate, years)
    })

    // Total return
    const totalCashFlow = math.sum(cashFlows)
    const finalValue = initialInvestment * Math.pow(1 + appreciationRate, cashFlows.length)
    const totalReturn = ((finalValue + totalCashFlow - initialInvestment) / initialInvestment) * 100

    return {
      npv,
      irr: irr * 100,
      paybackPeriod,
      breakEvenPoint,
      equityBuildup,
      appreciationForecast,
      totalReturn
    }
  }

  // Risk Assessment
  static assessRisk(
    property: any,
    marketData: any
  ): {
    score: number
    factors: Array<{ name: string; impact: number; description: string }>
  } {
    const factors = []
    let score = 50 // Base score

    // Age factor
    const age = new Date().getFullYear() - (property.year_built || 2000)
    if (age > 50) {
      factors.push({ name: 'Property Age', impact: -10, description: 'Built over 50 years ago' })
      score -= 10
    } else if (age < 10) {
      factors.push({ name: 'Property Age', impact: 5, description: 'Built within last 10 years' })
      score += 5
    }

    // Location factors
    if (property.flood_zone === 'AE' || property.flood_zone === 'VE') {
      factors.push({ name: 'Flood Zone', impact: -15, description: 'High-risk flood zone' })
      score -= 15
    }

    // Market factors
    if (marketData?.vacancy_rate > 10) {
      factors.push({ name: 'Vacancy Rate', impact: -8, description: 'High area vacancy rate' })
      score -= 8
    }

    // HOA/CDD factors
    if (property.hoa_fee > 500) {
      factors.push({ name: 'HOA Fees', impact: -5, description: 'High monthly HOA fees' })
      score -= 5
    }

    // Positive factors
    if (property.recent_renovations) {
      factors.push({ name: 'Renovations', impact: 10, description: 'Recently renovated' })
      score += 10
    }

    if (property.school_rating > 7) {
      factors.push({ name: 'School District', impact: 8, description: 'Highly-rated schools' })
      score += 8
    }

    return {
      score: Math.max(0, Math.min(100, score)),
      factors
    }
  }
}

// Export calculation utilities
export const PropertyCalculations = {
  // Calculate mortgage payment
  mortgagePayment: (
    principal: number,
    rate: number,
    years: number
  ): number => {
    const monthlyRate = rate / 100 / 12
    const numPayments = years * 12
    if (monthlyRate === 0) return principal / numPayments

    const payment = principal *
      (monthlyRate * Math.pow(1 + monthlyRate, numPayments)) /
      (Math.pow(1 + monthlyRate, numPayments) - 1)

    return payment
  },

  // Calculate affordability
  affordability: (
    income: number,
    debts: number,
    downPayment: number,
    rate: number = 0.065
  ): number => {
    const monthlyIncome = income / 12
    const dtiLimit = 0.43 // 43% DTI ratio limit
    const maxMonthlyPayment = monthlyIncome * dtiLimit - debts

    // Calculate max loan amount
    const monthlyRate = rate / 12
    const numPayments = 30 * 12
    const maxLoan = maxMonthlyPayment *
      (Math.pow(1 + monthlyRate, numPayments) - 1) /
      (monthlyRate * Math.pow(1 + monthlyRate, numPayments))

    return maxLoan + downPayment
  },

  // Calculate rental yield
  rentalYield: (
    monthlyRent: number,
    propertyValue: number,
    expenses: number = 0
  ): number => {
    const annualRent = monthlyRent * 12
    const netRent = annualRent - expenses
    return (netRent / propertyValue) * 100
  }
}