import { PropertyData } from '@/hooks/usePropertyData'
import {
  Calculator,
  TrendingUp,
  DollarSign,
  PieChart,
  Home,
  AlertCircle,
  CheckCircle,
  BarChart3,
  Target,
  Percent,
  Calendar,
  FileText,
  ArrowUp,
  ArrowDown,
  Building
} from 'lucide-react'
import { useState, useEffect } from 'react'
import { PropertyDataAnalyzer } from '@/utils/property-intelligence'

interface InvestmentAnalysisTabProps {
  data: PropertyData
}

interface FinancialMetrics {
  purchasePrice: number
  downPayment: number
  loanAmount: number
  interestRate: number
  loanTerm: number
  monthlyPayment: number
  propertyTaxes: number
  insurance: number
  hoa: number
  maintenance: number
  vacancy: number
  management: number
  monthlyRent: number
  monthlyCashFlow: number
  annualCashFlow: number
  capRate: number
  cashOnCashReturn: number
  totalMonthlyExpenses: number
  totalAnnualExpenses: number
  grossRentalYield: number
  netOperatingIncome: number
  debtServiceCoverageRatio: number
  breakEvenRatio: number
}

export function InvestmentAnalysisTab({ data }: InvestmentAnalysisTabProps) {
  const { bcpaData, lastSale, navData } = data

  // Get property values
  const marketValue = bcpaData?.market_value || bcpaData?.marketValue || 0
  const assessedValue = bcpaData?.assessed_value || bcpaData?.assessedValue || 0
  const taxableValue = bcpaData?.taxable_value || bcpaData?.taxableValue || 0
  const livingArea = bcpaData?.living_area || bcpaData?.livingArea || bcpaData?.buildingSqFt || 0

  // Initialize financial metrics with defaults
  const [metrics, setMetrics] = useState<FinancialMetrics>({
    purchasePrice: parseFloat(String(marketValue || 0)),
    downPayment: parseFloat(String(marketValue || 0)) * 0.2, // 20% default
    loanAmount: parseFloat(String(marketValue || 0)) * 0.8,
    interestRate: 7.0, // Current market rate
    loanTerm: 30,
    monthlyPayment: 0,
    propertyTaxes: parseFloat(String(taxableValue || 0)) * 0.015 / 12, // 1.5% annual
    insurance: parseFloat(String(marketValue || 0)) * 0.005 / 12, // 0.5% annual
    hoa: 0,
    maintenance: parseFloat(String(marketValue || 0)) * 0.01 / 12, // 1% annual
    vacancy: 0.05, // 5% vacancy rate
    management: 0.08, // 8% management fee
    monthlyRent: 0,
    monthlyCashFlow: 0,
    annualCashFlow: 0,
    capRate: 0,
    cashOnCashReturn: 0,
    totalMonthlyExpenses: 0,
    totalAnnualExpenses: 0,
    grossRentalYield: 0,
    netOperatingIncome: 0,
    debtServiceCoverageRatio: 0,
    breakEvenRatio: 0
  })

  // Estimate monthly rent based on market data
  useEffect(() => {
    const sqft = parseFloat(String(livingArea || 0))
    let estimatedRent = 0

    if (sqft > 0) {
      // Estimate based on property type and size
      const propertyUse = bcpaData?.property_use || bcpaData?.property_use_code || '0'
      const useCode = parseInt(String(propertyUse))

      if (useCode >= 1 && useCode <= 4) {
        // Residential: $1.5-2.5 per sqft typical in Florida
        estimatedRent = sqft * 1.8
      } else if (useCode >= 5 && useCode <= 39) {
        // Commercial: Higher rates
        estimatedRent = sqft * 2.5
      }
    } else if (marketValue) {
      // Fallback: 0.8-1% of property value as monthly rent (1% rule)
      estimatedRent = parseFloat(String(marketValue)) * 0.008
    }

    setMetrics(prev => ({ ...prev, monthlyRent: Math.round(estimatedRent) }))
  }, [bcpaData, marketValue, livingArea])

  // Calculate financial metrics when inputs change
  useEffect(() => {
    calculateMetrics()
  }, [metrics.purchasePrice, metrics.downPayment, metrics.interestRate, metrics.loanTerm, metrics.monthlyRent])

  const calculateMetrics = () => {
    const principal = metrics.loanAmount
    const monthlyRate = metrics.interestRate / 100 / 12
    const numPayments = metrics.loanTerm * 12

    // Calculate monthly mortgage payment (P&I)
    let monthlyPayment = 0
    if (monthlyRate > 0) {
      monthlyPayment = principal * (monthlyRate * Math.pow(1 + monthlyRate, numPayments)) /
                       (Math.pow(1 + monthlyRate, numPayments) - 1)
    }

    // Calculate total monthly expenses
    const totalMonthlyExpenses =
      monthlyPayment +
      metrics.propertyTaxes +
      metrics.insurance +
      metrics.hoa +
      metrics.maintenance

    // Calculate effective rental income after vacancy and management
    const effectiveRent = metrics.monthlyRent * (1 - metrics.vacancy) * (1 - metrics.management)

    // Calculate cash flow
    const monthlyCashFlow = effectiveRent - totalMonthlyExpenses
    const annualCashFlow = monthlyCashFlow * 12

    // Calculate NOI (Net Operating Income)
    const annualRent = metrics.monthlyRent * 12
    const noi = annualRent * (1 - metrics.vacancy) -
                (metrics.propertyTaxes + metrics.insurance + metrics.maintenance) * 12

    // Calculate Cap Rate
    const capRate = metrics.purchasePrice > 0 ? (noi / metrics.purchasePrice) * 100 : 0

    // Calculate Cash-on-Cash Return
    const cashOnCashReturn = metrics.downPayment > 0 ? (annualCashFlow / metrics.downPayment) * 100 : 0

    // Calculate Gross Rental Yield
    const grossRentalYield = metrics.purchasePrice > 0 ? (annualRent / metrics.purchasePrice) * 100 : 0

    // Calculate DSCR (Debt Service Coverage Ratio)
    const annualDebtService = monthlyPayment * 12
    const dscr = annualDebtService > 0 ? noi / annualDebtService : 0

    // Calculate Break-Even Ratio
    const breakEvenRatio = annualRent > 0 ?
      ((totalMonthlyExpenses * 12) / annualRent) * 100 : 0

    setMetrics(prev => ({
      ...prev,
      monthlyPayment,
      monthlyCashFlow,
      annualCashFlow,
      capRate,
      cashOnCashReturn,
      totalMonthlyExpenses,
      totalAnnualExpenses: totalMonthlyExpenses * 12,
      grossRentalYield,
      netOperatingIncome: noi,
      debtServiceCoverageRatio: dscr,
      breakEvenRatio
    }))
  }

  // Format currency
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value)
  }

  // Get investment recommendations
  const getInvestmentRecommendations = () => {
    const recommendations = []

    if (metrics.capRate > 8) {
      recommendations.push({ type: 'positive', text: 'Strong cap rate above 8% - Good investment potential' })
    } else if (metrics.capRate < 5) {
      recommendations.push({ type: 'warning', text: 'Low cap rate below 5% - May indicate overpriced property' })
    }

    if (metrics.cashOnCashReturn > 10) {
      recommendations.push({ type: 'positive', text: 'Excellent cash-on-cash return above 10%' })
    } else if (metrics.cashOnCashReturn < 0) {
      recommendations.push({ type: 'negative', text: 'Negative cash flow - Property will require monthly subsidization' })
    }

    if (metrics.debtServiceCoverageRatio > 1.25) {
      recommendations.push({ type: 'positive', text: 'DSCR above 1.25 - Lender-friendly investment' })
    } else if (metrics.debtServiceCoverageRatio < 1) {
      recommendations.push({ type: 'warning', text: 'DSCR below 1.0 - May have difficulty qualifying for financing' })
    }

    if (metrics.breakEvenRatio < 75) {
      recommendations.push({ type: 'positive', text: 'Low break-even ratio - Good margin of safety' })
    } else if (metrics.breakEvenRatio > 90) {
      recommendations.push({ type: 'warning', text: 'High break-even ratio - Limited buffer for expenses' })
    }

    // Add property intelligence
    const intelligence = PropertyDataAnalyzer.analyzeProperty(bcpaData, lastSale)
    if (intelligence.dataCompleteness < 50) {
      recommendations.push({ type: 'warning', text: 'Limited property data available - Consider ordering detailed report' })
    }

    return recommendations
  }

  return (
    <div className="space-y-6">
      {/* Financial Calculator */}
      <div className="card-executive animate-elegant">
        <div className="elegant-card-header">
          <h3 className="elegant-card-title gold-accent flex items-center">
            <div className="p-2 rounded-lg mr-3" style={{background: '#2c3e50'}}>
              <Calculator className="w-4 h-4 text-white" />
            </div>
            Investment Calculator
          </h3>
          <p className="text-sm mt-2 text-gray-elegant">Customize assumptions to analyze investment potential</p>
        </div>
        <div className="pt-6">
          <div className="grid grid-cols-3 gap-6">
            {/* Input Parameters */}
            <div className="space-y-4">
              <h4 className="text-sm font-semibold text-navy uppercase tracking-wider">Purchase Details</h4>
              <div>
                <label className="text-xs text-gray-elegant">Purchase Price</label>
                <input
                  type="number"
                  value={metrics.purchasePrice}
                  onChange={(e) => setMetrics(prev => ({
                    ...prev,
                    purchasePrice: parseFloat(e.target.value) || 0,
                    loanAmount: (parseFloat(e.target.value) || 0) - prev.downPayment
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-gold"
                />
              </div>
              <div>
                <label className="text-xs text-gray-elegant">Down Payment (20%)</label>
                <input
                  type="number"
                  value={metrics.downPayment}
                  onChange={(e) => setMetrics(prev => ({
                    ...prev,
                    downPayment: parseFloat(e.target.value) || 0,
                    loanAmount: prev.purchasePrice - (parseFloat(e.target.value) || 0)
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-gold"
                />
              </div>
              <div>
                <label className="text-xs text-gray-elegant">Interest Rate (%)</label>
                <input
                  type="number"
                  step="0.1"
                  value={metrics.interestRate}
                  onChange={(e) => setMetrics(prev => ({ ...prev, interestRate: parseFloat(e.target.value) || 0 }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-gold"
                />
              </div>
              <div>
                <label className="text-xs text-gray-elegant">Loan Term (years)</label>
                <input
                  type="number"
                  value={metrics.loanTerm}
                  onChange={(e) => setMetrics(prev => ({ ...prev, loanTerm: parseInt(e.target.value) || 30 }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-gold"
                />
              </div>
            </div>

            {/* Income & Expenses */}
            <div className="space-y-4">
              <h4 className="text-sm font-semibold text-navy uppercase tracking-wider">Income & Expenses</h4>
              <div>
                <label className="text-xs text-gray-elegant">Monthly Rent</label>
                <input
                  type="number"
                  value={metrics.monthlyRent}
                  onChange={(e) => setMetrics(prev => ({ ...prev, monthlyRent: parseFloat(e.target.value) || 0 }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-gold"
                />
              </div>
              <div>
                <label className="text-xs text-gray-elegant">Property Taxes/mo</label>
                <input
                  type="number"
                  value={metrics.propertyTaxes}
                  onChange={(e) => setMetrics(prev => ({ ...prev, propertyTaxes: parseFloat(e.target.value) || 0 }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-gold"
                />
              </div>
              <div>
                <label className="text-xs text-gray-elegant">Insurance/mo</label>
                <input
                  type="number"
                  value={metrics.insurance}
                  onChange={(e) => setMetrics(prev => ({ ...prev, insurance: parseFloat(e.target.value) || 0 }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-gold"
                />
              </div>
              <div>
                <label className="text-xs text-gray-elegant">HOA/mo</label>
                <input
                  type="number"
                  value={metrics.hoa}
                  onChange={(e) => setMetrics(prev => ({ ...prev, hoa: parseFloat(e.target.value) || 0 }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-gold"
                />
              </div>
            </div>

            {/* Key Metrics */}
            <div className="space-y-4">
              <h4 className="text-sm font-semibold text-navy uppercase tracking-wider">Key Metrics</h4>
              <div className="space-y-3">
                <div className={`p-3 rounded-lg border ${metrics.monthlyCashFlow >= 0 ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                  <p className="text-xs text-gray-elegant">Monthly Cash Flow</p>
                  <p className={`text-xl font-semibold ${metrics.monthlyCashFlow >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(metrics.monthlyCashFlow)}
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-gold-light border border-gold">
                  <p className="text-xs text-gray-elegant">Cap Rate</p>
                  <p className="text-xl font-semibold text-navy">{metrics.capRate.toFixed(2)}%</p>
                </div>
                <div className="p-3 rounded-lg bg-blue-50 border border-blue-200">
                  <p className="text-xs text-gray-elegant">Cash-on-Cash Return</p>
                  <p className="text-xl font-semibold text-blue-600">{metrics.cashOnCashReturn.toFixed(2)}%</p>
                </div>
                <div className="p-3 rounded-lg bg-purple-50 border border-purple-200">
                  <p className="text-xs text-gray-elegant">DSCR</p>
                  <p className="text-xl font-semibold text-purple-600">{metrics.debtServiceCoverageRatio.toFixed(2)}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Analysis */}
      <div className="grid grid-cols-2 gap-6">
        {/* Cash Flow Breakdown */}
        <div className="card-executive animate-elegant">
          <div className="elegant-card-header">
            <h3 className="elegant-card-title flex items-center">
              <DollarSign className="w-4 h-4 mr-2 text-gold" />
              Cash Flow Analysis
            </h3>
          </div>
          <div className="pt-4">
            <div className="space-y-3">
              <div className="pb-3 border-b border-gray-200">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-elegant">Gross Monthly Rent</span>
                  <span className="text-sm font-medium text-green-600">+{formatCurrency(metrics.monthlyRent)}</span>
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-xs uppercase tracking-wider text-gray-500 font-semibold">Monthly Expenses</p>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-elegant">Mortgage (P&I)</span>
                  <span className="text-sm text-red-600">-{formatCurrency(metrics.monthlyPayment)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-elegant">Property Taxes</span>
                  <span className="text-sm text-red-600">-{formatCurrency(metrics.propertyTaxes)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-elegant">Insurance</span>
                  <span className="text-sm text-red-600">-{formatCurrency(metrics.insurance)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-elegant">HOA Fees</span>
                  <span className="text-sm text-red-600">-{formatCurrency(metrics.hoa)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-elegant">Maintenance</span>
                  <span className="text-sm text-red-600">-{formatCurrency(metrics.maintenance)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-elegant">Vacancy ({(metrics.vacancy * 100).toFixed(0)}%)</span>
                  <span className="text-sm text-red-600">-{formatCurrency(metrics.monthlyRent * metrics.vacancy)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-elegant">Management ({(metrics.management * 100).toFixed(0)}%)</span>
                  <span className="text-sm text-red-600">-{formatCurrency(metrics.monthlyRent * metrics.management)}</span>
                </div>
              </div>

              <div className="pt-3 border-t-2 border-gold">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-semibold text-navy">Net Monthly Cash Flow</span>
                  <span className={`text-lg font-bold ${metrics.monthlyCashFlow >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(metrics.monthlyCashFlow)}
                  </span>
                </div>
                <div className="flex justify-between items-center mt-1">
                  <span className="text-xs text-gray-elegant">Annual Cash Flow</span>
                  <span className={`text-sm font-medium ${metrics.annualCashFlow >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(metrics.annualCashFlow)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Investment Metrics */}
        <div className="card-executive animate-elegant">
          <div className="elegant-card-header">
            <h3 className="elegant-card-title flex items-center">
              <BarChart3 className="w-4 h-4 mr-2 text-gold" />
              Investment Metrics
            </h3>
          </div>
          <div className="pt-4">
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 rounded-lg bg-gray-50">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-gray-elegant">Cap Rate</span>
                    <Target className="w-3 h-3 text-gold" />
                  </div>
                  <p className="text-lg font-semibold text-navy">{metrics.capRate.toFixed(2)}%</p>
                  <p className="text-xs text-gray-500">NOI / Purchase Price</p>
                </div>

                <div className="p-3 rounded-lg bg-gray-50">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-gray-elegant">Cash-on-Cash</span>
                    <Percent className="w-3 h-3 text-blue-600" />
                  </div>
                  <p className="text-lg font-semibold text-navy">{metrics.cashOnCashReturn.toFixed(2)}%</p>
                  <p className="text-xs text-gray-500">Annual CF / Down Payment</p>
                </div>

                <div className="p-3 rounded-lg bg-gray-50">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-gray-elegant">Gross Yield</span>
                    <TrendingUp className="w-3 h-3 text-green-600" />
                  </div>
                  <p className="text-lg font-semibold text-navy">{metrics.grossRentalYield.toFixed(2)}%</p>
                  <p className="text-xs text-gray-500">Annual Rent / Price</p>
                </div>

                <div className="p-3 rounded-lg bg-gray-50">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-gray-elegant">DSCR</span>
                    <FileText className="w-3 h-3 text-purple-600" />
                  </div>
                  <p className="text-lg font-semibold text-navy">{metrics.debtServiceCoverageRatio.toFixed(2)}</p>
                  <p className="text-xs text-gray-500">NOI / Debt Service</p>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-gold-light">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-navy">Break-Even Occupancy</span>
                  <span className="text-sm font-bold text-navy">{metrics.breakEvenRatio.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${metrics.breakEvenRatio < 75 ? 'bg-green-500' : metrics.breakEvenRatio < 90 ? 'bg-yellow-500' : 'bg-red-500'}`}
                    style={{ width: `${Math.min(metrics.breakEvenRatio, 100)}%` }}
                  />
                </div>
                <p className="text-xs text-gray-600 mt-1">
                  {metrics.breakEvenRatio < 75 ? 'Excellent margin' : metrics.breakEvenRatio < 90 ? 'Acceptable margin' : 'Tight margin'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Investment Recommendations */}
      <div className="card-executive animate-elegant">
        <div className="elegant-card-header">
          <h3 className="elegant-card-title gold-accent flex items-center">
            <div className="p-2 bg-navy rounded-lg mr-3">
              <Target className="w-4 h-4 text-white" />
            </div>
            Investment Recommendations
          </h3>
        </div>
        <div className="pt-6">
          <div className="space-y-3">
            {getInvestmentRecommendations().map((rec, index) => (
              <div
                key={index}
                className={`flex items-start p-3 rounded-lg ${
                  rec.type === 'positive' ? 'bg-green-50 border border-green-200' :
                  rec.type === 'warning' ? 'bg-orange-50 border border-orange-200' :
                  'bg-red-50 border border-red-200'
                }`}
              >
                {rec.type === 'positive' ? (
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 mr-3 flex-shrink-0" />
                ) : (
                  <AlertCircle className={`w-5 h-5 ${rec.type === 'warning' ? 'text-orange-600' : 'text-red-600'} mt-0.5 mr-3 flex-shrink-0`} />
                )}
                <p className="text-sm text-gray-700">{rec.text}</p>
              </div>
            ))}
          </div>

          {/* Summary Score */}
          <div className="mt-6 p-4 bg-gradient-to-r from-gold-light to-white rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-lg font-semibold text-navy">Overall Investment Score</h4>
                <p className="text-sm text-gray-600">Based on current market conditions and property metrics</p>
              </div>
              <div className="text-center">
                <div className={`text-4xl font-bold ${
                  metrics.capRate > 7 && metrics.cashOnCashReturn > 8 ? 'text-green-600' :
                  metrics.capRate > 5 && metrics.cashOnCashReturn > 5 ? 'text-yellow-600' :
                  'text-red-600'
                }`}>
                  {metrics.capRate > 7 && metrics.cashOnCashReturn > 8 ? 'A' :
                   metrics.capRate > 5 && metrics.cashOnCashReturn > 5 ? 'B' :
                   metrics.capRate > 3 && metrics.cashOnCashReturn > 0 ? 'C' : 'D'}
                </div>
                <p className="text-xs text-gray-500">Investment Grade</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="p-4 bg-gray-100 rounded-lg">
        <p className="text-xs text-gray-600 italic">
          <AlertCircle className="w-3 h-3 inline mr-1" />
          This analysis is for informational purposes only and should not be considered financial advice.
          Actual returns may vary based on market conditions, property management, and other factors.
          Please consult with qualified real estate and financial professionals before making investment decisions.
        </p>
      </div>
    </div>
  )
}