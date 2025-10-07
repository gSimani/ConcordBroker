import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Building,
  Calculator,
  TrendingUp,
  BarChart3,
  GitBranch,
  Target,
  Save,
  Download,
  AlertCircle,
  Plus,
  FileText,
  DollarSign,
  Percent,
  PieChart,
  Home,
  CheckCircle,
  ArrowUp,
  ArrowDown,
  Calendar
} from 'lucide-react';
import { supabase } from '@/lib/supabase';
import { PropertyData } from '@/hooks/usePropertyData';
import { useInvestmentAnalysis } from '@/hooks/useInvestmentAnalysis';

// Types
export interface PropertyBasics {
  property_name: string;
  property_address: string;
  purchase_price: number;
  year_built: number;
  total_sqft: number;
  lot_size_sqft: number;
  number_of_units: number;
}

export interface UnitMixData {
  id: string;
  unit_type: string;
  unit_count: number;
  sqft_per_unit: number;
  current_rent: number;
  market_rent: number;
}

export interface FinancingData {
  down_payment_percent: number;
  interest_rate: number;
  loan_term_years: number;
  points_fees: number;
  closing_costs_percent: number;
}

export interface IncomeData {
  other_income_monthly: number;
  vacancy_rate: number;
  annual_rent_growth: number;
  lease_up_months: number;
}

export interface ExpenseData {
  property_taxes: number;
  insurance: number;
  management_fee_percent: number;
  maintenance_repairs: number;
  utilities_electric: number;
  utilities_water: number;
  landscaping: number;
  pest_control: number;
  other_expenses: number;
  capital_reserves_percent: number;
  expense_growth_rate: number;
}

export interface AnalysisParams {
  holding_period_years: number;
  annual_appreciation: number;
  exit_cap_rate: number;
  selling_costs_percent: number;
  improvement_capex: number;
}

export interface CalculatedMetrics {
  // Financial calculations
  down_payment_amount: number;
  loan_amount: number;
  monthly_payment: number;
  annual_debt_service: number;
  ltv_ratio: number;

  // Income calculations
  gross_potential_rent: number;
  total_other_income: number;
  vacancy_loss: number;
  effective_gross_income: number;

  // Expense calculations
  management_fee: number;
  capital_reserves: number;
  total_operating_expenses: number;
  expense_ratio: number;

  // Cash flow calculations
  net_operating_income: number;
  before_tax_cash_flow: number;
  monthly_cash_flow: number;

  // Return metrics
  cap_rate: number;
  cash_on_cash_return: number;
  debt_service_coverage_ratio: number;
  gross_rent_multiplier: number;
  break_even_ratio: number;
}

export interface InvestmentAnalysis {
  id?: string;
  property_id?: string;
  parcel_id: string;
  analysis_name: string;
  property_data: PropertyBasics;
  unit_mix_data: UnitMixData[];
  financing_data: FinancingData;
  income_data: IncomeData;
  expense_data: ExpenseData;
  analysis_params: AnalysisParams;
  calculated_metrics?: CalculatedMetrics;
  cash_flow_projections?: any;
  return_metrics?: any;
  scenario_data?: any;
}

interface InvestmentAnalysisTabProps {
  data: PropertyData;
  parcelId?: string;
}

// Calculate mortgage payment using standard formula
const calculateMortgagePayment = (principal: number, annualRate: number, years: number): number => {
  if (principal <= 0 || annualRate <= 0 || years <= 0) return 0;

  const monthlyRate = annualRate / 100 / 12;
  const numPayments = years * 12;

  if (monthlyRate === 0) {
    return principal / numPayments;
  }

  const payment = principal *
    (monthlyRate * Math.pow(1 + monthlyRate, numPayments)) /
    (Math.pow(1 + monthlyRate, numPayments) - 1);

  return payment;
};

export function InvestmentAnalysisTab({ data, parcelId }: InvestmentAnalysisTabProps) {
  const { bcpaData, lastSale, navData } = data;

  // Use the real investment analysis hook
  const finalParcelId = parcelId || bcpaData?.parcel_id || data.parcelId;
  const { investmentAnalysis, loading: hookLoading, error: hookError } = useInvestmentAnalysis(finalParcelId);

  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysisName, setAnalysisName] = useState('');
  const [currentAnalysisId, setCurrentAnalysisId] = useState<string | null>(null);

  // Get property values from hook or fallback to passed data
  const marketValue = investmentAnalysis?.market_value || bcpaData?.market_value || bcpaData?.marketValue || 0;
  const assessedValue = investmentAnalysis?.assessed_value || bcpaData?.assessed_value || bcpaData?.assessedValue || 0;
  const taxableValue = investmentAnalysis?.taxable_value || bcpaData?.taxable_value || bcpaData?.taxableValue || 0;
  const livingArea = investmentAnalysis?.building_sqft || bcpaData?.living_area || bcpaData?.livingArea || bcpaData?.buildingSqFt || 0;

  // Get property use code for unit type
  const getPropertyUseType = () => {
    const useCode = bcpaData?.property_use || bcpaData?.dor_uc || '001';
    const subUse = bcpaData?.property_sub_use || '';
    return `${useCode}${subUse ? ` - ${subUse}` : ''}`;
  };

  // State for CAP rate targeting
  const [targetCapRate, setTargetCapRate] = useState(6);
  const [manualCapRateInput, setManualCapRateInput] = useState('6');

  // Analysis data state with defaults from investment analysis hook or property data
  const [analysis, setAnalysis] = useState<InvestmentAnalysis>({
    parcel_id: finalParcelId || bcpaData?.parcel_id || '',
    analysis_name: '',
    property_data: {
      property_name: investmentAnalysis?.property_name || bcpaData?.property_address || bcpaData?.phy_addr1 || '',
      property_address: investmentAnalysis?.property_address || bcpaData?.property_address_full || `${bcpaData?.phy_addr1 || ''} ${bcpaData?.phy_addr2 || ''}`.trim() || '',
      purchase_price: investmentAnalysis?.estimated_value || parseFloat(String(marketValue || 0)),
      year_built: investmentAnalysis?.year_built || bcpaData?.year_built || bcpaData?.actual_year_built || 2000,
      total_sqft: investmentAnalysis?.building_sqft || parseFloat(String(livingArea || bcpaData?.tot_lvg_area || 0)),
      lot_size_sqft: investmentAnalysis?.lot_sqft || bcpaData?.land_sqft || bcpaData?.lnd_sqfoot || 0,
      number_of_units: investmentAnalysis?.units || bcpaData?.units || bcpaData?.no_units || 1
    },
    unit_mix_data: [{
      id: '1',
      unit_type: getPropertyUseType(),
      unit_count: investmentAnalysis?.units || bcpaData?.units || bcpaData?.no_units || 1,
      sqft_per_unit: investmentAnalysis?.building_sqft || parseFloat(String(livingArea || bcpaData?.tot_lvg_area || 800)),
      current_rent: investmentAnalysis?.estimated_monthly_rent || Math.round((marketValue || 0) * 0.007), // Estimate 0.7% of value as monthly rent
      market_rent: investmentAnalysis?.market_rent || Math.round((marketValue || 0) * 0.008) // Estimate 0.8% of value as market rent
    }],
    financing_data: {
      down_payment_percent: 25,
      interest_rate: 7.5,
      loan_term_years: 30,
      points_fees: 0,
      closing_costs_percent: 2.5
    },
    income_data: {
      other_income_monthly: 0,
      vacancy_rate: 5,
      annual_rent_growth: 3,
      lease_up_months: 0
    },
    expense_data: {
      property_taxes: investmentAnalysis?.estimated_annual_taxes || parseFloat(String(taxableValue || 0)) * 0.015,
      insurance: investmentAnalysis?.estimated_annual_insurance || parseFloat(String(marketValue || 0)) * 0.005,
      management_fee_percent: 8,
      maintenance_repairs: parseFloat(String(marketValue || 0)) * 0.01,
      utilities_electric: 0,
      utilities_water: 0,
      landscaping: 0,
      pest_control: 0,
      other_expenses: 0,
      capital_reserves_percent: 3,
      expense_growth_rate: 3
    },
    analysis_params: {
      holding_period_years: 10,
      annual_appreciation: 3.5,
      exit_cap_rate: 6,
      selling_costs_percent: 6,
      improvement_capex: 0
    }
  });

  // Update analysis when investment hook data loads
  useEffect(() => {
    if (investmentAnalysis && !loading && !saving) {
      setAnalysis(prev => ({
        ...prev,
        parcel_id: finalParcelId || prev.parcel_id,
        property_data: {
          ...prev.property_data,
          property_name: investmentAnalysis.property_name || prev.property_data.property_name,
          property_address: investmentAnalysis.property_address || prev.property_data.property_address,
          purchase_price: investmentAnalysis.estimated_value || prev.property_data.purchase_price,
          year_built: investmentAnalysis.year_built || prev.property_data.year_built,
          total_sqft: investmentAnalysis.building_sqft || prev.property_data.total_sqft,
          lot_size_sqft: investmentAnalysis.lot_sqft || prev.property_data.lot_size_sqft,
          number_of_units: investmentAnalysis.units || prev.property_data.number_of_units
        },
        unit_mix_data: prev.unit_mix_data.map(unit => ({
          ...unit,
          unit_count: investmentAnalysis.units || unit.unit_count,
          sqft_per_unit: investmentAnalysis.building_sqft || unit.sqft_per_unit,
          current_rent: investmentAnalysis.estimated_monthly_rent || unit.current_rent,
          market_rent: investmentAnalysis.market_rent || unit.market_rent
        })),
        expense_data: {
          ...prev.expense_data,
          property_taxes: investmentAnalysis.estimated_annual_taxes || prev.expense_data.property_taxes,
          insurance: investmentAnalysis.estimated_annual_insurance || prev.expense_data.insurance
        }
      }));
    }
  }, [investmentAnalysis, loading, saving, finalParcelId]);

  // Calculate all metrics
  const calculateMetrics = (): CalculatedMetrics => {
    const { property_data, financing_data, unit_mix_data, income_data, expense_data } = analysis;

    // Financing calculations
    const down_payment_amount = property_data.purchase_price * financing_data.down_payment_percent / 100;
    const loan_amount = property_data.purchase_price - down_payment_amount;
    const monthly_rate = financing_data.interest_rate / 100 / 12;
    const num_payments = financing_data.loan_term_years * 12;

    let monthly_payment = 0;
    if (monthly_rate > 0) {
      monthly_payment = loan_amount * (monthly_rate * Math.pow(1 + monthly_rate, num_payments)) /
                       (Math.pow(1 + monthly_rate, num_payments) - 1);
    }

    const annual_debt_service = monthly_payment * 12;
    const ltv_ratio = loan_amount / property_data.purchase_price * 100;

    // Income calculations
    const gross_potential_rent = unit_mix_data.reduce((sum, unit) =>
      sum + (unit.current_rent * unit.unit_count * 12), 0);
    const total_other_income = income_data.other_income_monthly * 12;
    const vacancy_loss = (gross_potential_rent + total_other_income) * income_data.vacancy_rate / 100;
    const effective_gross_income = gross_potential_rent + total_other_income - vacancy_loss;

    // Expense calculations
    const management_fee = effective_gross_income * expense_data.management_fee_percent / 100;
    const capital_reserves = effective_gross_income * expense_data.capital_reserves_percent / 100;
    const total_operating_expenses = expense_data.property_taxes + expense_data.insurance +
      management_fee + expense_data.maintenance_repairs + expense_data.utilities_electric +
      expense_data.utilities_water + expense_data.landscaping + expense_data.pest_control +
      expense_data.other_expenses + capital_reserves;
    const expense_ratio = effective_gross_income > 0 ? total_operating_expenses / effective_gross_income * 100 : 0;

    // Cash flow calculations
    const net_operating_income = effective_gross_income - total_operating_expenses;
    const before_tax_cash_flow = net_operating_income - annual_debt_service;
    const monthly_cash_flow = before_tax_cash_flow / 12;

    // Return metrics
    const cap_rate = property_data.purchase_price > 0 ? (net_operating_income / property_data.purchase_price) * 100 : 0;
    const cash_on_cash_return = down_payment_amount > 0 ? (before_tax_cash_flow / down_payment_amount) * 100 : 0;
    const debt_service_coverage_ratio = annual_debt_service > 0 ? net_operating_income / annual_debt_service : 0;
    const gross_rent_multiplier = gross_potential_rent > 0 ? property_data.purchase_price / gross_potential_rent : 0;
    const break_even_ratio = effective_gross_income > 0 ?
      ((total_operating_expenses + annual_debt_service) / effective_gross_income) * 100 : 0;

    return {
      down_payment_amount,
      loan_amount,
      monthly_payment,
      annual_debt_service,
      ltv_ratio,
      gross_potential_rent,
      total_other_income,
      vacancy_loss,
      effective_gross_income,
      management_fee,
      capital_reserves,
      total_operating_expenses,
      expense_ratio,
      net_operating_income,
      before_tax_cash_flow,
      monthly_cash_flow,
      cap_rate,
      cash_on_cash_return,
      debt_service_coverage_ratio,
      gross_rent_multiplier,
      break_even_ratio
    };
  };

  const metrics = calculateMetrics();

  // Colors for ConcordBroker brand
  const navyColor = '#2c3e50';
  const goldColor = '#d4af37';
  const goldLightColor = '#f4e5c2';

  // Format currency
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  // Format percentage
  const formatPercent = (value: number) => {
    return `${value.toFixed(2)}%`;
  };

  // Get investment grade
  const getInvestmentGrade = () => {
    if (metrics.cap_rate > 8 && metrics.cash_on_cash_return > 12) return { grade: 'A+', color: 'text-green-600' };
    if (metrics.cap_rate > 7 && metrics.cash_on_cash_return > 10) return { grade: 'A', color: 'text-green-600' };
    if (metrics.cap_rate > 6 && metrics.cash_on_cash_return > 8) return { grade: 'B', color: 'text-blue-600' };
    if (metrics.cap_rate > 5 && metrics.cash_on_cash_return > 6) return { grade: 'C', color: 'text-yellow-600' };
    return { grade: 'D', color: 'text-red-600' };
  };

  const investmentGrade = getInvestmentGrade();

  // Calculate suggested purchase price based on target CAP rate
  const calculatePurchasePriceFromCap = (capRate: number): number => {
    const noi = metrics.net_operating_income;
    if (!noi || noi <= 0) return 0;
    // Handle negative cap rates
    if (capRate === 0) return 0;
    return Math.abs(noi / (capRate / 100));
  };

  // Save analysis
  const saveAnalysis = async () => {
    if (!analysisName.trim()) {
      setError('Please enter an analysis name');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const analysisData = {
        parcel_id: analysis.parcel_id,
        user_id: 'demo-user', // Use demo user ID for now since there's no auth
        analysis_name: analysisName.trim(),
        property_data: analysis.property_data,
        unit_mix_data: analysis.unit_mix_data,
        financing_data: analysis.financing_data,
        income_data: analysis.income_data,
        expense_data: analysis.expense_data,
        analysis_params: analysis.analysis_params,
        calculated_metrics: metrics,
        status: 'active'
      };

      let result;
      if (currentAnalysisId) {
        result = await supabase
          .from('investment_analyses')
          .update(analysisData)
          .eq('id', currentAnalysisId)
          .select()
          .single();
      } else {
        result = await supabase
          .from('investment_analyses')
          .insert(analysisData)
          .select()
          .single();
      }

      if (result.error) throw result.error;

      setCurrentAnalysisId(result.data.id);
    } catch (error: any) {
      console.error('Error saving analysis:', error);
      setError('Failed to save analysis');
    } finally {
      setSaving(false);
    }
  };

  const tabs = [
    { id: 'overview', name: 'Overview', icon: Home },
    { id: 'property', name: 'Property', icon: Building },
    { id: 'financing', name: 'Financing', icon: DollarSign },
    { id: 'income', name: 'Income', icon: TrendingUp },
    { id: 'expenses', name: 'Expenses', icon: FileText },
    { id: 'returns', name: 'Returns', icon: Target },
    { id: 'calculators', name: 'Calculators', icon: Calculator }
  ];

  return (
    <div className="w-full max-w-7xl mx-auto space-y-6" id="investment-analysis-main">
      {/* Header */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h2 className="text-2xl font-semibold flex items-center gap-2" style={{ color: navyColor }}>
              <Calculator className="w-6 h-6" style={{ color: goldColor }} />
              Investment Analysis
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Professional-grade real estate investment analysis
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Input
              placeholder="Analysis Name"
              value={analysisName}
              onChange={(e) => setAnalysisName(e.target.value)}
              className="w-48"
            />
            <Button
              onClick={saveAnalysis}
              disabled={saving || !analysisName.trim()}
              style={{ backgroundColor: goldColor, color: navyColor }}
              className="hover:opacity-90 font-semibold"
            >
              {saving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-navy border-t-transparent mr-2"></div>
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Save Analysis
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">{error}</AlertDescription>
        </Alert>
      )}

      {/* Main Analysis Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        {/* Tab Navigation - Fixed Alignment */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-2 overflow-x-auto">
          <TabsList className="flex min-w-max gap-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <TabsTrigger
                  key={tab.id}
                  value={tab.id}
                  className="flex flex-col items-center justify-center gap-1 p-3 text-xs data-[state=active]:text-navy min-w-[100px] flex-shrink-0"
                  style={{
                    backgroundColor: activeTab === tab.id ? goldLightColor : 'transparent',
                    color: activeTab === tab.id ? navyColor : undefined
                  }}
                >
                  <Icon className="w-4 h-4" />
                  <span className="font-medium whitespace-nowrap">{tab.name}</span>
                </TabsTrigger>
              );
            })}
          </TabsList>
        </div>

        {/* Overview Tab */}
        <TabsContent value="overview" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Investment Summary Card */}
            <Card className="p-6 col-span-2">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold" style={{ color: navyColor }}>
                  Investment Summary
                </h3>
                <div className="text-center">
                  <div className={`text-4xl font-bold ${investmentGrade.color}`}>
                    {investmentGrade.grade}
                  </div>
                  <p className="text-xs text-gray-500">Investment Grade</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-3" style={{ color: navyColor }}>Purchase Details</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Purchase Price:</span>
                      <span className="font-medium">{formatCurrency(analysis.property_data.purchase_price)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Down Payment ({analysis.financing_data.down_payment_percent}%):</span>
                      <span className="font-medium">{formatCurrency(metrics.down_payment_amount)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Loan Amount:</span>
                      <span className="font-medium">{formatCurrency(metrics.loan_amount)}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium mb-3" style={{ color: navyColor }}>Cash Flow Analysis</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Monthly Rent:</span>
                      <span className="font-medium text-green-600">+{formatCurrency(metrics.gross_potential_rent / 12)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Monthly Expenses:</span>
                      <span className="font-medium text-red-600">-{formatCurrency((metrics.total_operating_expenses + metrics.annual_debt_service) / 12)}</span>
                    </div>
                    <div className="flex justify-between font-semibold">
                      <span>Monthly Cash Flow:</span>
                      <span className={metrics.monthly_cash_flow >= 0 ? 'text-green-600' : 'text-red-600'}>
                        {formatCurrency(metrics.monthly_cash_flow)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </Card>

            {/* Key Metrics Card */}
            <Card className="p-6">
              <h3 className="text-xl font-semibold mb-6" style={{ color: navyColor }}>
                Key Metrics
              </h3>
              <div className="space-y-4">
                <div className="p-4 rounded-lg" style={{ backgroundColor: goldLightColor }}>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Cap Rate</span>
                    <Target className="w-4 h-4" style={{ color: goldColor }} />
                  </div>
                  <div className="text-2xl font-bold" style={{ color: navyColor }}>
                    {formatPercent(metrics.cap_rate)}
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-blue-50">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Cash-on-Cash</span>
                    <Percent className="w-4 h-4 text-blue-600" />
                  </div>
                  <div className="text-2xl font-bold text-blue-600">
                    {formatPercent(metrics.cash_on_cash_return)}
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-green-50">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">DSCR</span>
                    <CheckCircle className="w-4 h-4 text-green-600" />
                  </div>
                  <div className="text-2xl font-bold text-green-600">
                    {metrics.debt_service_coverage_ratio.toFixed(2)}
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* CAP Rate Calculator */}
          <Card className="p-6">
            <h3 className="text-xl font-semibold mb-6" style={{ color: navyColor }}>
              CAP Rate Analysis & Purchase Price Calculator
            </h3>

            {/* Target CAP Rate Slider */}
            <div className="mb-6 p-4 rounded-lg" style={{ backgroundColor: goldLightColor }}>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Target CAP Rate: <span className="text-2xl font-bold" style={{ color: navyColor }}>{targetCapRate.toFixed(1)}%</span>
              </label>
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-600">-10%</span>
                <input
                  type="range"
                  min="-10"
                  max="20"
                  step="0.1"
                  value={targetCapRate}
                  onChange={(e) => {
                    const value = parseFloat(e.target.value);
                    setTargetCapRate(value);
                    setManualCapRateInput(value.toFixed(1));
                  }}
                  className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  style={{
                    background: `linear-gradient(to right, #dc2626 0%, #f59e0b 33%, #10b981 66%, #059669 100%)`
                  }}
                />
                <span className="text-sm text-gray-600">20%</span>
                <Input
                  type="number"
                  value={manualCapRateInput}
                  onChange={(e) => {
                    setManualCapRateInput(e.target.value);
                    const value = parseFloat(e.target.value);
                    if (!isNaN(value) && value >= -10 && value <= 20) {
                      setTargetCapRate(value);
                    }
                  }}
                  onBlur={(e) => {
                    const value = parseFloat(e.target.value);
                    if (isNaN(value) || value < -10 || value > 20) {
                      setManualCapRateInput(targetCapRate.toFixed(1));
                    } else {
                      setTargetCapRate(value);
                    }
                  }}
                  className="w-20 text-center font-bold"
                  step="0.1"
                  min="-10"
                  max="20"
                />
                <span className="text-sm text-gray-600">%</span>
              </div>

              {/* Suggested Purchase Price */}
              <div className="mt-4 p-3 bg-white rounded-lg">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Suggested Purchase Price for {targetCapRate.toFixed(1)}% CAP:</span>
                  <span className="text-xl font-bold" style={{ color: navyColor }}>
                    {formatCurrency(calculatePurchasePriceFromCap(targetCapRate))}
                  </span>
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  Based on NOI of {formatCurrency(metrics.net_operating_income)}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Purchase Price
                </label>
                <Input
                  type="number"
                  value={analysis.property_data.purchase_price}
                  onChange={(e) => setAnalysis(prev => ({
                    ...prev,
                    property_data: {
                      ...prev.property_data,
                      purchase_price: parseFloat(e.target.value) || 0
                    }
                  }))}
                  className="w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Monthly Rent
                </label>
                <Input
                  type="number"
                  value={analysis.unit_mix_data[0]?.current_rent || 0}
                  onChange={(e) => {
                    const newRent = parseFloat(e.target.value) || 0;
                    setAnalysis(prev => ({
                      ...prev,
                      unit_mix_data: prev.unit_mix_data.map(unit => ({
                        ...unit,
                        current_rent: newRent
                      }))
                    }));
                  }}
                  className="w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Interest Rate (%)
                </label>
                <Input
                  type="number"
                  step="0.1"
                  value={analysis.financing_data.interest_rate}
                  onChange={(e) => setAnalysis(prev => ({
                    ...prev,
                    financing_data: {
                      ...prev.financing_data,
                      interest_rate: parseFloat(e.target.value) || 0
                    }
                  }))}
                  className="w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Down Payment (%)
                </label>
                <Input
                  type="number"
                  value={analysis.financing_data.down_payment_percent}
                  onChange={(e) => setAnalysis(prev => ({
                    ...prev,
                    financing_data: {
                      ...prev.financing_data,
                      down_payment_percent: parseFloat(e.target.value) || 0
                    }
                  }))}
                  className="w-full"
                />
              </div>
            </div>
          </Card>
        </TabsContent>

        {/* Property Setup Tab */}
        <TabsContent value="property" className="mt-6">
          <div className="space-y-6">
            {/* Property Basics */}
            <Card className="p-6">
              <h3 className="text-xl font-semibold mb-6" style={{ color: navyColor }}>
                Property Basics
              </h3>
              <div id="property-basics-form" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Property Name
                  </label>
                  <Input
                    id="property-name-input"
                    value={analysis.property_data.property_name}
                    onChange={(e) => setAnalysis(prev => ({
                      ...prev,
                      property_data: {
                        ...prev.property_data,
                        property_name: e.target.value
                      }
                    }))}
                    placeholder="Enter property name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Property Address
                  </label>
                  <Input
                    id="property-address-input"
                    value={analysis.property_data.property_address}
                    onChange={(e) => setAnalysis(prev => ({
                      ...prev,
                      property_data: {
                        ...prev.property_data,
                        property_address: e.target.value
                      }
                    }))}
                    placeholder="Enter full address"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Purchase Price ($)
                  </label>
                  <Input
                    id="purchase-price-input"
                    type="number"
                    value={analysis.property_data.purchase_price}
                    onChange={(e) => setAnalysis(prev => ({
                      ...prev,
                      property_data: {
                        ...prev.property_data,
                        purchase_price: parseFloat(e.target.value) || 0
                      }
                    }))}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Year Built
                  </label>
                  <Input
                    id="year-built-input"
                    type="number"
                    value={analysis.property_data.year_built}
                    onChange={(e) => setAnalysis(prev => ({
                      ...prev,
                      property_data: {
                        ...prev.property_data,
                        year_built: parseInt(e.target.value) || 2000
                      }
                    }))}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Total Square Feet
                  </label>
                  <Input
                    id="total-sqft-input"
                    type="number"
                    value={analysis.property_data.total_sqft}
                    onChange={(e) => setAnalysis(prev => ({
                      ...prev,
                      property_data: {
                        ...prev.property_data,
                        total_sqft: parseFloat(e.target.value) || 0
                      }
                    }))}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Lot Size (sq ft)
                  </label>
                  <Input
                    id="lot-size-input"
                    type="number"
                    value={analysis.property_data.lot_size_sqft}
                    onChange={(e) => setAnalysis(prev => ({
                      ...prev,
                      property_data: {
                        ...prev.property_data,
                        lot_size_sqft: parseFloat(e.target.value) || 0
                      }
                    }))}
                  />
                </div>
              </div>
            </Card>

            {/* Unit Mix Configuration */}
            <Card className="p-6">
              <div id="unit-mix-header" className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-semibold" style={{ color: navyColor }}>
                  Unit Mix Configuration
                </h3>
                <Button
                  id="add-unit-type-button"
                  onClick={() => {
                    const newUnit: UnitMixData = {
                      id: `unit-${Date.now()}`,
                      unit_type: 'New Unit Type',
                      unit_count: 1,
                      sqft_per_unit: 800,
                      current_rent: 1200,
                      market_rent: 1250
                    };
                    setAnalysis(prev => ({
                      ...prev,
                      unit_mix_data: [...prev.unit_mix_data, newUnit]
                    }));
                  }}
                  className="flex items-center gap-2"
                  style={{ backgroundColor: goldColor, borderColor: goldColor }}
                >
                  <Plus className="w-4 h-4" />
                  Add Unit Type
                </Button>
              </div>

              <div id="unit-mix-list" className="space-y-4">
                {analysis.unit_mix_data.map((unit, index) => (
                  <div key={unit.id} id={`unit-mix-item-${index}`} className="p-4 border rounded-lg">
                    <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Unit Type
                        </label>
                        <Input
                          id={`unit-type-${index}`}
                          value={unit.unit_type}
                          onChange={(e) => {
                            const updatedUnits = [...analysis.unit_mix_data];
                            updatedUnits[index] = { ...unit, unit_type: e.target.value };
                            setAnalysis(prev => ({ ...prev, unit_mix_data: updatedUnits }));
                          }}
                          placeholder="e.g., 1BR/1BA"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Unit Count
                        </label>
                        <Input
                          id={`unit-count-${index}`}
                          type="number"
                          value={unit.unit_count}
                          onChange={(e) => {
                            const updatedUnits = [...analysis.unit_mix_data];
                            updatedUnits[index] = { ...unit, unit_count: parseInt(e.target.value) || 0 };
                            setAnalysis(prev => ({
                              ...prev,
                              unit_mix_data: updatedUnits,
                              property_data: {
                                ...prev.property_data,
                                number_of_units: updatedUnits.reduce((sum, u) => sum + u.unit_count, 0)
                              }
                            }));
                          }}
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Sq Ft/Unit
                        </label>
                        <Input
                          id={`sqft-per-unit-${index}`}
                          type="number"
                          value={unit.sqft_per_unit}
                          onChange={(e) => {
                            const updatedUnits = [...analysis.unit_mix_data];
                            updatedUnits[index] = { ...unit, sqft_per_unit: parseFloat(e.target.value) || 0 };
                            setAnalysis(prev => ({ ...prev, unit_mix_data: updatedUnits }));
                          }}
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Current Rent
                        </label>
                        <Input
                          id={`current-rent-${index}`}
                          type="number"
                          value={unit.current_rent}
                          onChange={(e) => {
                            const updatedUnits = [...analysis.unit_mix_data];
                            updatedUnits[index] = { ...unit, current_rent: parseFloat(e.target.value) || 0 };
                            setAnalysis(prev => ({ ...prev, unit_mix_data: updatedUnits }));
                          }}
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Market Rent
                        </label>
                        <Input
                          id={`market-rent-${index}`}
                          type="number"
                          value={unit.market_rent}
                          onChange={(e) => {
                            const updatedUnits = [...analysis.unit_mix_data];
                            updatedUnits[index] = { ...unit, market_rent: parseFloat(e.target.value) || 0 };
                            setAnalysis(prev => ({ ...prev, unit_mix_data: updatedUnits }));
                          }}
                        />
                      </div>

                      <div className="flex items-end">
                        <Button
                          id={`remove-unit-${index}`}
                          onClick={() => {
                            if (analysis.unit_mix_data.length > 1) {
                              const updatedUnits = analysis.unit_mix_data.filter((_, i) => i !== index);
                              setAnalysis(prev => ({
                                ...prev,
                                unit_mix_data: updatedUnits,
                                property_data: {
                                  ...prev.property_data,
                                  number_of_units: updatedUnits.reduce((sum, u) => sum + u.unit_count, 0)
                                }
                              }));
                            }
                          }}
                          variant="outline"
                          size="sm"
                          className="text-red-600 border-red-300 hover:bg-red-50"
                          disabled={analysis.unit_mix_data.length === 1}
                        >
                          Remove
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Unit Mix Summary */}
              <div id="unit-mix-summary" className="mt-6 p-4 rounded-lg" style={{ backgroundColor: goldLightColor }}>
                <h4 className="font-semibold mb-3" style={{ color: navyColor }}>Unit Mix Summary</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Total Units:</span>
                    <div className="font-semibold">{analysis.unit_mix_data.reduce((sum, unit) => sum + unit.unit_count, 0)}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">Total Rentable Sq Ft:</span>
                    <div className="font-semibold">{analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.sqft_per_unit), 0).toLocaleString()}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">Total Current Rent:</span>
                    <div className="font-semibold">{formatCurrency(analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0))}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">Total Market Rent:</span>
                    <div className="font-semibold">{formatCurrency(analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.market_rent), 0))}</div>
                  </div>
                </div>
              </div>
            </Card>

            {/* Property Characteristics */}
            <Card className="p-6">
              <h3 className="text-xl font-semibold mb-6" style={{ color: navyColor }}>
                Additional Property Information
              </h3>
              <div id="property-characteristics" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Property Type
                  </label>
                  <select
                    id="property-type-select"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={analysis.property_data.number_of_units > 1 ? 'multifamily' : 'single-family'}
                    onChange={(e) => {
                      // Property type is derived from unit count, but we can add logic here if needed
                    }}
                  >
                    <option value="single-family">Single Family</option>
                    <option value="duplex">Duplex</option>
                    <option value="triplex">Triplex</option>
                    <option value="quadplex">Quadplex</option>
                    <option value="multifamily">Multifamily (5+ units)</option>
                    <option value="commercial">Commercial</option>
                    <option value="mixed-use">Mixed Use</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Property Class
                  </label>
                  <select
                    id="property-class-select"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="A">Class A (Luxury)</option>
                    <option value="B">Class B (Quality)</option>
                    <option value="C">Class C (Average)</option>
                    <option value="D">Class D (Below Average)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Condition
                  </label>
                  <select
                    id="property-condition-select"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="excellent">Excellent</option>
                    <option value="good">Good</option>
                    <option value="fair">Fair</option>
                    <option value="poor">Poor</option>
                    <option value="needs-renovation">Needs Renovation</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Parking Spaces
                  </label>
                  <Input
                    id="parking-spaces-input"
                    type="number"
                    placeholder="0"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Storage Units
                  </label>
                  <Input
                    id="storage-units-input"
                    type="number"
                    placeholder="0"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Laundry Facilities
                  </label>
                  <select
                    id="laundry-facilities-select"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="none">None</option>
                    <option value="hookups">Hookups Only</option>
                    <option value="in-unit">In-Unit</option>
                    <option value="common-area">Common Area</option>
                    <option value="coin-operated">Coin Operated</option>
                  </select>
                </div>
              </div>
            </Card>

            {/* Save Property Setup */}
            <Card className="p-6">
              <div id="property-setup-actions" className="flex justify-between items-center">
                <div>
                  <h4 className="font-semibold text-gray-900">Property Setup Complete</h4>
                  <p className="text-sm text-gray-600">Your property configuration has been saved and will be used for all financial calculations.</p>
                </div>
                <div className="flex gap-3">
                  <Button
                    id="validate-property-button"
                    variant="outline"
                    onClick={() => {
                      // Validation logic can be added here
                      const totalUnits = analysis.unit_mix_data.reduce((sum, unit) => sum + unit.unit_count, 0);
                      if (totalUnits === 0) {
                        setError('Please add at least one unit to the unit mix.');
                        return;
                      }
                      if (!analysis.property_data.property_name.trim()) {
                        setError('Property name is required.');
                        return;
                      }
                      setError(null);
                      alert('Property setup validation passed!');
                    }}
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Validate Setup
                  </Button>
                  <Button
                    id="save-property-setup-button"
                    onClick={saveAnalysis}
                    disabled={saving}
                    style={{ backgroundColor: goldColor, borderColor: goldColor }}
                  >
                    <Save className="w-4 h-4 mr-2" />
                    {saving ? 'Saving...' : 'Save Setup'}
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="calculators" className="mt-6">
          <div className="space-y-6">
            {/* Enhanced Mortgage Calculator */}
            <Card className="p-6">
              <h3 className="text-xl font-semibold mb-6" style={{ color: navyColor }}>
                Enhanced Mortgage Calculator
              </h3>
              <div id="mortgage-calculator" className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Purchase Price ($)
                    </label>
                    <Input
                      id="mortgage-purchase-price"
                      type="number"
                      value={analysis.property_data.purchase_price}
                      onChange={(e) => setAnalysis(prev => ({
                        ...prev,
                        property_data: {
                          ...prev.property_data,
                          purchase_price: parseFloat(e.target.value) || 0
                        }
                      }))}
                      className="w-full"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Down Payment (%)
                    </label>
                    <Input
                      id="mortgage-down-payment"
                      type="number"
                      min="0"
                      max="100"
                      step="5"
                      value={analysis.financing_data.down_payment_percent}
                      onChange={(e) => setAnalysis(prev => ({
                        ...prev,
                        financing_data: {
                          ...prev.financing_data,
                          down_payment_percent: parseFloat(e.target.value) || 25
                        }
                      }))}
                      className="w-full"
                    />
                    <div className="text-sm text-gray-600 mt-1">
                      Amount: {formatCurrency(analysis.property_data.purchase_price * analysis.financing_data.down_payment_percent / 100)}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Loan Amount ($)
                    </label>
                    <div className="p-3 rounded-lg" style={{ backgroundColor: goldLightColor }}>
                      <span className="text-lg font-semibold" style={{ color: navyColor }}>
                        {formatCurrency(analysis.property_data.purchase_price * (100 - analysis.financing_data.down_payment_percent) / 100)}
                      </span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Interest Rate (%)
                    </label>
                    <Input
                      id="mortgage-interest-rate"
                      type="number"
                      min="0"
                      max="20"
                      step="0.125"
                      value={analysis.financing_data.interest_rate}
                      onChange={(e) => setAnalysis(prev => ({
                        ...prev,
                        financing_data: {
                          ...prev.financing_data,
                          interest_rate: parseFloat(e.target.value) || 7.5
                        }
                      }))}
                      className="w-full"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Loan Term (Years)
                    </label>
                    <select
                      id="mortgage-loan-term"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      value={analysis.financing_data.loan_term_years}
                      onChange={(e) => setAnalysis(prev => ({
                        ...prev,
                        financing_data: {
                          ...prev.financing_data,
                          loan_term_years: parseInt(e.target.value) || 30
                        }
                      }))}
                    >
                      <option value={10}>10 Years</option>
                      <option value={15}>15 Years</option>
                      <option value={20}>20 Years</option>
                      <option value={25}>25 Years</option>
                      <option value={30}>30 Years</option>
                      <option value={40}>40 Years</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="p-4 rounded-lg bg-purple-50">
                    <div className="text-sm text-gray-600 mb-1">Monthly Payment (P&I)</div>
                    <div className="text-3xl font-bold text-purple-600">
                      {formatCurrency(calculateMortgagePayment(
                        analysis.property_data.purchase_price * (100 - analysis.financing_data.down_payment_percent) / 100,
                        analysis.financing_data.interest_rate,
                        analysis.financing_data.loan_term_years
                      ))}
                    </div>
                  </div>

                  <div className="p-4 rounded-lg bg-orange-50">
                    <div className="text-sm text-gray-600 mb-1">Total Interest Paid</div>
                    <div className="text-2xl font-bold text-orange-600">
                      {(() => {
                        const monthlyPayment = calculateMortgagePayment(
                          analysis.property_data.purchase_price * (100 - analysis.financing_data.down_payment_percent) / 100,
                          analysis.financing_data.interest_rate,
                          analysis.financing_data.loan_term_years
                        );
                        const totalPaid = monthlyPayment * analysis.financing_data.loan_term_years * 12;
                        const loanAmount = analysis.property_data.purchase_price * (100 - analysis.financing_data.down_payment_percent) / 100;
                        return formatCurrency(totalPaid - loanAmount);
                      })()}
                    </div>
                  </div>

                  <div className="p-4 rounded-lg bg-red-50">
                    <div className="text-sm text-gray-600 mb-1">Total Amount Paid</div>
                    <div className="text-2xl font-bold text-red-600">
                      {formatCurrency(
                        calculateMortgagePayment(
                          analysis.property_data.purchase_price * (100 - analysis.financing_data.down_payment_percent) / 100,
                          analysis.financing_data.interest_rate,
                          analysis.financing_data.loan_term_years
                        ) * analysis.financing_data.loan_term_years * 12
                      )}
                    </div>
                  </div>

                  <div className="p-4 rounded-lg bg-green-50">
                    <div className="text-sm text-gray-600 mb-1">Loan-to-Value (LTV)</div>
                    <div className="text-2xl font-bold text-green-600">
                      {((100 - analysis.financing_data.down_payment_percent)).toFixed(1)}%
                    </div>
                  </div>
                </div>
              </div>
            </Card>

            {/* Full Amortization Schedule */}
            <Card className="p-6">
              <h3 className="text-xl font-semibold mb-6" style={{ color: navyColor }}>
                Complete Amortization Schedule
              </h3>
              <div id="full-amortization-schedule" className="overflow-x-auto max-h-96 overflow-y-auto">
                <table className="w-full text-xs">
                  <thead className="sticky top-0 bg-white">
                    <tr className="border-b">
                      <th className="text-left py-2 px-2">Payment #</th>
                      <th className="text-right py-2 px-2">Payment</th>
                      <th className="text-right py-2 px-2">Principal</th>
                      <th className="text-right py-2 px-2">Interest</th>
                      <th className="text-right py-2 px-2">Balance</th>
                      <th className="text-right py-2 px-2">Cum. Interest</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(() => {
                      const loanAmount = analysis.property_data.purchase_price * (100 - analysis.financing_data.down_payment_percent) / 100;
                      const monthlyRate = analysis.financing_data.interest_rate / 100 / 12;
                      const monthlyPayment = calculateMortgagePayment(loanAmount, analysis.financing_data.interest_rate, analysis.financing_data.loan_term_years);
                      const totalPayments = analysis.financing_data.loan_term_years * 12;
                      let balance = loanAmount;
                      let cumulativeInterest = 0;
                      const rows = [];

                      for (let i = 1; i <= totalPayments; i++) {
                        const interestPayment = balance * monthlyRate;
                        const principalPayment = monthlyPayment - interestPayment;
                        balance -= principalPayment;
                        cumulativeInterest += interestPayment;

                        // Only show every 12th payment to keep table manageable, plus first few payments
                        if (i <= 12 || i % 12 === 0 || i === totalPayments) {
                          rows.push(
                            <tr key={i} className={`border-b hover:bg-gray-50 ${i % 12 === 0 ? 'bg-blue-50' : ''}`}>
                              <td className="py-1 px-2">{i}</td>
                              <td className="text-right py-1 px-2">{formatCurrency(monthlyPayment)}</td>
                              <td className="text-right py-1 px-2">{formatCurrency(principalPayment)}</td>
                              <td className="text-right py-1 px-2">{formatCurrency(interestPayment)}</td>
                              <td className="text-right py-1 px-2 font-semibold">{formatCurrency(Math.max(0, balance))}</td>
                              <td className="text-right py-1 px-2">{formatCurrency(cumulativeInterest)}</td>
                            </tr>
                          );
                        }
                      }
                      return rows;
                    })()}
                  </tbody>
                </table>
                <div className="mt-2 text-xs text-gray-500">
                  Note: Showing first 12 payments and every 12th payment thereafter. Blue rows indicate year-end.
                </div>
              </div>
            </Card>

            {/* IRR & NPV Calculator */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="p-6">
                <h3 className="text-xl font-semibold mb-6" style={{ color: navyColor }}>
                  IRR Calculator
                </h3>
                <div id="irr-calculator" className="space-y-4">
                  <div className="p-4 rounded-lg" style={{ backgroundColor: goldLightColor }}>
                    <div className="text-sm text-gray-600 mb-1">Internal Rate of Return</div>
                    <div className="text-3xl font-bold" style={{ color: navyColor }}>
                      {(() => {
                        // Simplified IRR calculation based on cash flows
                        const initialInvestment = (analysis.property_data.purchase_price * analysis.financing_data.down_payment_percent / 100) + (analysis.property_data.purchase_price * analysis.financing_data.closing_costs_percent / 100) + analysis.financing_data.points_fees;
                        const noi = ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12) * (1 - analysis.income_data.vacancy_rate / 100) + (analysis.income_data.other_income_monthly * 12)) - (analysis.expense_data.property_taxes + analysis.expense_data.insurance + ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12) * (analysis.expense_data.management_fee_percent / 100)) + analysis.expense_data.maintenance_repairs + analysis.expense_data.utilities_electric + analysis.expense_data.utilities_water + analysis.expense_data.landscaping + analysis.expense_data.pest_control + analysis.expense_data.other_expenses + ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12 + analysis.income_data.other_income_monthly * 12) * (analysis.expense_data.capital_reserves_percent / 100)));
                        const loanAmount = analysis.property_data.purchase_price * (100 - analysis.financing_data.down_payment_percent) / 100;
                        const annualDebtService = calculateMortgagePayment(loanAmount, analysis.financing_data.interest_rate, analysis.financing_data.loan_term_years) * 12;
                        const annualCashFlow = noi - annualDebtService;

                        // Simple IRR approximation: (Annual Cash Flow / Initial Investment) + appreciation
                        const simpleIRR = ((annualCashFlow / initialInvestment) + (analysis.analysis_params.annual_appreciation / 100)) * 100;
                        return formatPercent(Math.max(0, simpleIRR) / 100);
                      })()}
                    </div>
                  </div>

                  <div className="text-sm text-gray-600">
                    <div className="mb-2">IRR Calculation Components:</div>
                    <div className="space-y-1">
                      <div>• Initial Investment: {formatCurrency((analysis.property_data.purchase_price * analysis.financing_data.down_payment_percent / 100) + (analysis.property_data.purchase_price * analysis.financing_data.closing_costs_percent / 100) + analysis.financing_data.points_fees)}</div>
                      <div>• Annual Cash Flow: {formatCurrency((() => {
                        const noi = ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12) * (1 - analysis.income_data.vacancy_rate / 100) + (analysis.income_data.other_income_monthly * 12)) - (analysis.expense_data.property_taxes + analysis.expense_data.insurance + ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12) * (analysis.expense_data.management_fee_percent / 100)) + analysis.expense_data.maintenance_repairs + analysis.expense_data.utilities_electric + analysis.expense_data.utilities_water + analysis.expense_data.landscaping + analysis.expense_data.pest_control + analysis.expense_data.other_expenses + ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12 + analysis.income_data.other_income_monthly * 12) * (analysis.expense_data.capital_reserves_percent / 100)));
                        const loanAmount = analysis.property_data.purchase_price * (100 - analysis.financing_data.down_payment_percent) / 100;
                        const annualDebtService = calculateMortgagePayment(loanAmount, analysis.financing_data.interest_rate, analysis.financing_data.loan_term_years) * 12;
                        return noi - annualDebtService;
                      })())}</div>
                      <div>• Expected Appreciation: {analysis.analysis_params.annual_appreciation}% annually</div>
                      <div>• Holding Period: {analysis.analysis_params.holding_period_years} years</div>
                    </div>
                  </div>
                </div>
              </Card>

              <Card className="p-6">
                <h3 className="text-xl font-semibold mb-6" style={{ color: navyColor }}>
                  NPV Calculator
                </h3>
                <div id="npv-calculator" className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Discount Rate (%)
                    </label>
                    <Input
                      id="discount-rate-input"
                      type="number"
                      step="0.1"
                      defaultValue="10"
                      className="w-full"
                      onChange={(e) => {
                        // NPV calculation would update here
                      }}
                    />
                  </div>

                  <div className="p-4 rounded-lg bg-green-50">
                    <div className="text-sm text-gray-600 mb-1">Net Present Value</div>
                    <div className="text-3xl font-bold text-green-600">
                      {(() => {
                        // Simplified NPV calculation
                        const discountRate = 0.10; // 10% default
                        const holdingPeriod = analysis.analysis_params.holding_period_years;
                        const initialInvestment = (analysis.property_data.purchase_price * analysis.financing_data.down_payment_percent / 100) + (analysis.property_data.purchase_price * analysis.financing_data.closing_costs_percent / 100) + analysis.financing_data.points_fees;
                        const noi = ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12) * (1 - analysis.income_data.vacancy_rate / 100) + (analysis.income_data.other_income_monthly * 12)) - (analysis.expense_data.property_taxes + analysis.expense_data.insurance + ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12) * (analysis.expense_data.management_fee_percent / 100)) + analysis.expense_data.maintenance_repairs + analysis.expense_data.utilities_electric + analysis.expense_data.utilities_water + analysis.expense_data.landscaping + analysis.expense_data.pest_control + analysis.expense_data.other_expenses + ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12 + analysis.income_data.other_income_monthly * 12) * (analysis.expense_data.capital_reserves_percent / 100)));
                        const loanAmount = analysis.property_data.purchase_price * (100 - analysis.financing_data.down_payment_percent) / 100;
                        const annualDebtService = calculateMortgagePayment(loanAmount, analysis.financing_data.interest_rate, analysis.financing_data.loan_term_years) * 12;
                        const annualCashFlow = noi - annualDebtService;

                        // Calculate future value and NPV
                        const futureValue = analysis.property_data.purchase_price * Math.pow(1 + analysis.analysis_params.annual_appreciation / 100, holdingPeriod);
                        const netSaleProceeds = futureValue * (1 - analysis.analysis_params.selling_costs_percent / 100);

                        // NPV of cash flows
                        let npv = -initialInvestment;
                        for (let year = 1; year <= holdingPeriod; year++) {
                          const cashFlow = year === holdingPeriod ? annualCashFlow + netSaleProceeds : annualCashFlow;
                          npv += cashFlow / Math.pow(1 + discountRate, year);
                        }

                        return formatCurrency(npv);
                      })()}
                    </div>
                  </div>

                  <div className="text-sm text-gray-600">
                    <div className="mb-2">NPV Calculation Assumptions:</div>
                    <div className="space-y-1">
                      <div>• Discount Rate: 10% (modifiable above)</div>
                      <div>• Holding Period: {analysis.analysis_params.holding_period_years} years</div>
                      <div>• Exit Value: {formatCurrency(analysis.property_data.purchase_price * Math.pow(1 + analysis.analysis_params.annual_appreciation / 100, analysis.analysis_params.holding_period_years))}</div>
                      <div>• Selling Costs: {analysis.analysis_params.selling_costs_percent}%</div>
                    </div>
                  </div>
                </div>
              </Card>
            </div>

            {/* Break-Even Analysis */}
            <Card className="p-6">
              <h3 className="text-xl font-semibold mb-6" style={{ color: navyColor }}>
                Break-Even Analysis
              </h3>
              <div id="break-even-analysis" className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="p-4 rounded-lg bg-yellow-50">
                  <div className="text-sm text-gray-600 mb-1">Break-Even Rent (Monthly)</div>
                  <div className="text-2xl font-bold text-yellow-600">
                    {(() => {
                      const totalExpenses = analysis.expense_data.property_taxes + analysis.expense_data.insurance + analysis.expense_data.maintenance_repairs + analysis.expense_data.utilities_electric + analysis.expense_data.utilities_water + analysis.expense_data.landscaping + analysis.expense_data.pest_control + analysis.expense_data.other_expenses;
                      const loanAmount = analysis.property_data.purchase_price * (100 - analysis.financing_data.down_payment_percent) / 100;
                      const monthlyDebtService = calculateMortgagePayment(loanAmount, analysis.financing_data.interest_rate, analysis.financing_data.loan_term_years);
                      const breakEvenRent = (totalExpenses / 12) + monthlyDebtService;
                      return formatCurrency(breakEvenRent);
                    })()}
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-blue-50">
                  <div className="text-sm text-gray-600 mb-1">Break-Even Occupancy</div>
                  <div className="text-2xl font-bold text-blue-600">
                    {(() => {
                      const currentRent = analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0);
                      const totalExpenses = analysis.expense_data.property_taxes + analysis.expense_data.insurance + analysis.expense_data.maintenance_repairs + analysis.expense_data.utilities_electric + analysis.expense_data.utilities_water + analysis.expense_data.landscaping + analysis.expense_data.pest_control + analysis.expense_data.other_expenses;
                      const loanAmount = analysis.property_data.purchase_price * (100 - analysis.financing_data.down_payment_percent) / 100;
                      const monthlyDebtService = calculateMortgagePayment(loanAmount, analysis.financing_data.interest_rate, analysis.financing_data.loan_term_years);
                      const breakEvenOccupancy = ((totalExpenses / 12) + monthlyDebtService) / currentRent * 100;
                      return formatPercent(Math.min(1, breakEvenOccupancy / 100));
                    })()}
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-purple-50">
                  <div className="text-sm text-gray-600 mb-1">Safety Margin</div>
                  <div className="text-2xl font-bold text-purple-600">
                    {(() => {
                      const currentRent = analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0);
                      const totalExpenses = analysis.expense_data.property_taxes + analysis.expense_data.insurance + analysis.expense_data.maintenance_repairs + analysis.expense_data.utilities_electric + analysis.expense_data.utilities_water + analysis.expense_data.landscaping + analysis.expense_data.pest_control + analysis.expense_data.other_expenses;
                      const loanAmount = analysis.property_data.purchase_price * (100 - analysis.financing_data.down_payment_percent) / 100;
                      const monthlyDebtService = calculateMortgagePayment(loanAmount, analysis.financing_data.interest_rate, analysis.financing_data.loan_term_years);
                      const breakEvenOccupancy = ((totalExpenses / 12) + monthlyDebtService) / currentRent * 100;
                      const safetyMargin = 100 - breakEvenOccupancy;
                      return `${safetyMargin.toFixed(1)}%`;
                    })()}
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </TabsContent>

        {/* Financing Tab */}
        <TabsContent value="financing" className="mt-6">
          <div className="space-y-6">
            {/* Loan Parameters */}
            <Card className="p-6">
              <h3 className="text-xl font-semibold mb-6" style={{ color: navyColor }}>
                Loan Parameters
              </h3>
              <div id="loan-parameters-form" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Purchase Price
                  </label>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <span className="text-lg font-semibold">{formatCurrency(analysis.property_data.purchase_price)}</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Down Payment (%)
                  </label>
                  <Input
                    id="down-payment-percent-input"
                    type="number"
                    step="0.1"
                    value={analysis.financing_data.down_payment_percent}
                    onChange={(e) => setAnalysis(prev => ({
                      ...prev,
                      financing_data: {
                        ...prev.financing_data,
                        down_payment_percent: parseFloat(e.target.value) || 0
                      }
                    }))}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Down Payment Amount
                  </label>
                  <div className="p-3 bg-green-50 rounded-lg">
                    <span className="text-lg font-semibold text-green-600">
                      {formatCurrency(analysis.property_data.purchase_price * analysis.financing_data.down_payment_percent / 100)}
                    </span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Interest Rate (%)
                  </label>
                  <Input
                    id="interest-rate-input"
                    type="number"
                    step="0.01"
                    value={analysis.financing_data.interest_rate}
                    onChange={(e) => setAnalysis(prev => ({
                      ...prev,
                      financing_data: {
                        ...prev.financing_data,
                        interest_rate: parseFloat(e.target.value) || 0
                      }
                    }))}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Loan Term (Years)
                  </label>
                  <select
                    id="loan-term-select"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={analysis.financing_data.loan_term_years}
                    onChange={(e) => setAnalysis(prev => ({
                      ...prev,
                      financing_data: {
                        ...prev.financing_data,
                        loan_term_years: parseInt(e.target.value) || 30
                      }
                    }))}
                  >
                    <option value={15}>15 Years</option>
                    <option value={20}>20 Years</option>
                    <option value={25}>25 Years</option>
                    <option value={30}>30 Years</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Loan Amount
                  </label>
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <span className="text-lg font-semibold text-blue-600">
                      {formatCurrency(analysis.property_data.purchase_price * (100 - analysis.financing_data.down_payment_percent) / 100)}
                    </span>
                  </div>
                </div>
              </div>
            </Card>

            {/* Additional Financing Costs */}
            <Card className="p-6">
              <h3 className="text-xl font-semibold mb-6" style={{ color: navyColor }}>
                Additional Financing Costs
              </h3>
              <div id="financing-costs-form" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Points & Loan Fees ($)
                  </label>
                  <Input
                    id="points-fees-input"
                    type="number"
                    value={analysis.financing_data.points_fees}
                    onChange={(e) => setAnalysis(prev => ({
                      ...prev,
                      financing_data: {
                        ...prev.financing_data,
                        points_fees: parseFloat(e.target.value) || 0
                      }
                    }))}
                    placeholder="Enter dollar amount"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Closing Costs (% of Purchase Price)
                  </label>
                  <Input
                    id="closing-costs-percent-input"
                    type="number"
                    step="0.1"
                    value={analysis.financing_data.closing_costs_percent}
                    onChange={(e) => setAnalysis(prev => ({
                      ...prev,
                      financing_data: {
                        ...prev.financing_data,
                        closing_costs_percent: parseFloat(e.target.value) || 0
                      }
                    }))}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Total Closing Costs
                  </label>
                  <div className="p-3 bg-orange-50 rounded-lg">
                    <span className="text-lg font-semibold text-orange-600">
                      {formatCurrency(analysis.property_data.purchase_price * analysis.financing_data.closing_costs_percent / 100)}
                    </span>
                  </div>
                </div>
              </div>
            </Card>

            {/* Calculated Financing Summary */}
            <Card className="p-6">
              <h3 className="text-xl font-semibold mb-6" style={{ color: navyColor }}>
                Financing Summary
              </h3>
              <div id="financing-summary" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="p-4 rounded-lg" style={{ backgroundColor: goldLightColor }}>
                  <div className="text-sm text-gray-600 mb-1">Monthly P&I Payment</div>
                  <div className="text-2xl font-bold" style={{ color: navyColor }}>
                    {formatCurrency(calculateMortgagePayment(
                      analysis.property_data.purchase_price * (100 - analysis.financing_data.down_payment_percent) / 100,
                      analysis.financing_data.interest_rate,
                      analysis.financing_data.loan_term_years
                    ))}
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-blue-50">
                  <div className="text-sm text-gray-600 mb-1">Annual Debt Service</div>
                  <div className="text-2xl font-bold text-blue-600">
                    {formatCurrency(calculateMortgagePayment(
                      analysis.property_data.purchase_price * (100 - analysis.financing_data.down_payment_percent) / 100,
                      analysis.financing_data.interest_rate,
                      analysis.financing_data.loan_term_years
                    ) * 12)}
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-green-50">
                  <div className="text-sm text-gray-600 mb-1">Loan-to-Value (LTV)</div>
                  <div className="text-2xl font-bold text-green-600">
                    {formatPercent((100 - analysis.financing_data.down_payment_percent) / 100)}
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-purple-50">
                  <div className="text-sm text-gray-600 mb-1">Total Cash Needed</div>
                  <div className="text-2xl font-bold text-purple-600">
                    {formatCurrency(
                      (analysis.property_data.purchase_price * analysis.financing_data.down_payment_percent / 100) +
                      (analysis.property_data.purchase_price * analysis.financing_data.closing_costs_percent / 100) +
                      analysis.financing_data.points_fees
                    )}
                  </div>
                </div>
              </div>
            </Card>

            {/* Amortization Preview */}
            <Card className="p-6">
              <h3 className="text-xl font-semibold mb-6" style={{ color: navyColor }}>
                First Year Amortization Preview
              </h3>
              <div id="amortization-preview" className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2">Payment #</th>
                      <th className="text-right py-2">Payment</th>
                      <th className="text-right py-2">Principal</th>
                      <th className="text-right py-2">Interest</th>
                      <th className="text-right py-2">Balance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(() => {
                      const loanAmount = analysis.property_data.purchase_price * (100 - analysis.financing_data.down_payment_percent) / 100;
                      const monthlyRate = analysis.financing_data.interest_rate / 100 / 12;
                      const monthlyPayment = calculateMortgagePayment(loanAmount, analysis.financing_data.interest_rate, analysis.financing_data.loan_term_years);
                      let balance = loanAmount;
                      const rows = [];

                      for (let i = 1; i <= 12; i++) {
                        const interestPayment = balance * monthlyRate;
                        const principalPayment = monthlyPayment - interestPayment;
                        balance -= principalPayment;

                        rows.push(
                          <tr key={i} className="border-b hover:bg-gray-50">
                            <td className="py-2">{i}</td>
                            <td className="text-right py-2">{formatCurrency(monthlyPayment)}</td>
                            <td className="text-right py-2">{formatCurrency(principalPayment)}</td>
                            <td className="text-right py-2">{formatCurrency(interestPayment)}</td>
                            <td className="text-right py-2">{formatCurrency(balance)}</td>
                          </tr>
                        );
                      }
                      return rows;
                    })()}
                  </tbody>
                </table>
              </div>
            </Card>

            {/* Financing Scenarios */}
            <Card className="p-6">
              <h3 className="text-xl font-semibold mb-6" style={{ color: navyColor }}>
                Compare Financing Scenarios
              </h3>
              <div id="financing-scenarios" className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {[
                  { name: 'Conservative', down: 25, rate: analysis.financing_data.interest_rate + 0.5, term: 30 },
                  { name: 'Current', down: analysis.financing_data.down_payment_percent, rate: analysis.financing_data.interest_rate, term: analysis.financing_data.loan_term_years },
                  { name: 'Aggressive', down: 20, rate: analysis.financing_data.interest_rate - 0.25, term: 30 }
                ].map((scenario, index) => {
                  const loanAmount = analysis.property_data.purchase_price * (100 - scenario.down) / 100;
                  const monthlyPayment = calculateMortgagePayment(loanAmount, scenario.rate, scenario.term);

                  return (
                    <div key={index} className={`p-4 rounded-lg border-2 ${index === 1 ? 'border-blue-300 bg-blue-50' : 'border-gray-200'}`}>
                      <h4 className="font-semibold mb-3">{scenario.name} Scenario</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Down Payment:</span>
                          <span className="font-medium">{scenario.down}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Interest Rate:</span>
                          <span className="font-medium">{scenario.rate.toFixed(2)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Loan Term:</span>
                          <span className="font-medium">{scenario.term} years</span>
                        </div>
                        <div className="flex justify-between border-t pt-2">
                          <span>Monthly Payment:</span>
                          <span className="font-bold">{formatCurrency(monthlyPayment)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Cash Required:</span>
                          <span className="font-bold">{formatCurrency(analysis.property_data.purchase_price * scenario.down / 100)}</span>
                        </div>
                      </div>
                      {index === 1 && (
                        <div className="mt-2 text-xs text-blue-600 text-center">Current Selection</div>
                      )}
                    </div>
                  );
                })}
              </div>
            </Card>
          </div>
        </TabsContent>

        {/* Income Tab */}
        <TabsContent value="income" className="mt-6">
          <div className="space-y-6">
            {/* Rental Income */}
            <Card className="p-6">
              <h3 className="text-xl font-semibold mb-6" style={{ color: navyColor }}>
                Rental Income Analysis
              </h3>
              <div id="rental-income-summary" className="mb-6 p-4 rounded-lg" style={{ backgroundColor: goldLightColor }}>
                <h4 className="font-semibold mb-3" style={{ color: navyColor }}>Current Unit Mix Income</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Monthly Rent (Current):</span>
                    <div className="font-semibold">{formatCurrency(analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0))}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">Monthly Rent (Market):</span>
                    <div className="font-semibold">{formatCurrency(analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.market_rent), 0))}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">Annual Current Rent:</span>
                    <div className="font-semibold">{formatCurrency(analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12)}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">Annual Market Rent:</span>
                    <div className="font-semibold">{formatCurrency(analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.market_rent), 0) * 12)}</div>
                  </div>
                </div>
              </div>

              <div id="income-parameters-form" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Vacancy Rate (%)
                  </label>
                  <Input
                    id="vacancy-rate-input"
                    type="number"
                    step="0.1"
                    value={analysis.income_data.vacancy_rate}
                    onChange={(e) => setAnalysis(prev => ({
                      ...prev,
                      income_data: {
                        ...prev.income_data,
                        vacancy_rate: parseFloat(e.target.value) || 0
                      }
                    }))}
                  />
                  <div className="text-xs text-gray-500 mt-1">Typical range: 3-8%</div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Annual Rent Growth (%)
                  </label>
                  <Input
                    id="rent-growth-input"
                    type="number"
                    step="0.1"
                    value={analysis.income_data.annual_rent_growth}
                    onChange={(e) => setAnalysis(prev => ({
                      ...prev,
                      income_data: {
                        ...prev.income_data,
                        annual_rent_growth: parseFloat(e.target.value) || 0
                      }
                    }))}
                  />
                  <div className="text-xs text-gray-500 mt-1">Historical average: 2-4%</div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Lease-up Period (Months)
                  </label>
                  <Input
                    id="lease-up-input"
                    type="number"
                    value={analysis.income_data.lease_up_months}
                    onChange={(e) => setAnalysis(prev => ({
                      ...prev,
                      income_data: {
                        ...prev.income_data,
                        lease_up_months: parseInt(e.target.value) || 0
                      }
                    }))}
                  />
                  <div className="text-xs text-gray-500 mt-1">For new acquisitions</div>
                </div>
              </div>
            </Card>

            {/* Other Income Sources */}
            <Card className="p-6">
              <h3 className="text-xl font-semibold mb-6" style={{ color: navyColor }}>
                Additional Income Sources
              </h3>
              <div id="other-income-form" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Parking Revenue (Monthly)
                  </label>
                  <Input
                    id="parking-income-input"
                    type="number"
                    placeholder="0"
                    onChange={(e) => {
                      const parkingIncome = parseFloat(e.target.value) || 0;
                      // Update other_income_monthly with parking component
                      // This would need more sophisticated tracking of income components
                    }}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Laundry Revenue (Monthly)
                  </label>
                  <Input
                    id="laundry-income-input"
                    type="number"
                    placeholder="0"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Storage Revenue (Monthly)
                  </label>
                  <Input
                    id="storage-income-input"
                    type="number"
                    placeholder="0"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Pet Fees (Monthly)
                  </label>
                  <Input
                    id="pet-fees-input"
                    type="number"
                    placeholder="0"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Application Fees (Annual)
                  </label>
                  <Input
                    id="application-fees-input"
                    type="number"
                    placeholder="0"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Other Income (Monthly)
                  </label>
                  <Input
                    id="other-income-input"
                    type="number"
                    value={analysis.income_data.other_income_monthly}
                    onChange={(e) => setAnalysis(prev => ({
                      ...prev,
                      income_data: {
                        ...prev.income_data,
                        other_income_monthly: parseFloat(e.target.value) || 0
                      }
                    }))}
                    placeholder="0"
                  />
                </div>
              </div>
            </Card>
          </div>
        </TabsContent>

        {/* Expenses Tab */}
        <TabsContent value="expenses" className="mt-6">
          <div className="space-y-6">
            {/* Quick Actions & Presets */}
            <Card className="p-6" style={{ background: `linear-gradient(135deg, ${goldLightColor} 0%, white 100%)` }}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold" style={{ color: navyColor }}>
                  Operating Expenses Calculator
                </h3>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={() => {
                      // Apply conservative defaults (higher expenses)
                      const purchasePrice = analysis.property_data.purchase_price;
                      const grossRent = analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12;
                      setAnalysis(prev => ({
                        ...prev,
                        expense_data: {
                          ...prev.expense_data,
                          property_taxes: purchasePrice * 0.015, // 1.5% of value
                          insurance: purchasePrice * 0.007, // 0.7% of value
                          management_fee_percent: 10, // 10% of gross rent
                          maintenance_repairs: purchasePrice * 0.02, // 2% of value
                          utilities_electric: grossRent * 0.02, // 2% of gross rent
                          utilities_water: grossRent * 0.03, // 3% of gross rent
                          landscaping: grossRent * 0.015, // 1.5% of gross rent
                          pest_control: 1200, // $100/month
                          other_expenses: grossRent * 0.02, // 2% of gross rent
                          capital_reserves_percent: 7, // 7% reserves
                          expense_growth_rate: 3.5 // 3.5% annual growth
                        }
                      }));
                    }}
                    style={{ backgroundColor: navyColor }}
                  >
                    Apply Conservative Defaults
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      // Apply moderate defaults (average expenses)
                      const purchasePrice = analysis.property_data.purchase_price;
                      const grossRent = analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12;
                      setAnalysis(prev => ({
                        ...prev,
                        expense_data: {
                          ...prev.expense_data,
                          property_taxes: purchasePrice * 0.012, // 1.2% of value
                          insurance: purchasePrice * 0.005, // 0.5% of value
                          management_fee_percent: 8, // 8% of gross rent
                          maintenance_repairs: purchasePrice * 0.015, // 1.5% of value
                          utilities_electric: grossRent * 0.015, // 1.5% of gross rent
                          utilities_water: grossRent * 0.025, // 2.5% of gross rent
                          landscaping: grossRent * 0.01, // 1% of gross rent
                          pest_control: 900, // $75/month
                          other_expenses: grossRent * 0.015, // 1.5% of gross rent
                          capital_reserves_percent: 5, // 5% reserves
                          expense_growth_rate: 3 // 3% annual growth
                        }
                      }));
                    }}
                  >
                    Apply Moderate Defaults
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      // Apply aggressive defaults (lower expenses)
                      const purchasePrice = analysis.property_data.purchase_price;
                      const grossRent = analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12;
                      setAnalysis(prev => ({
                        ...prev,
                        expense_data: {
                          ...prev.expense_data,
                          property_taxes: purchasePrice * 0.01, // 1% of value
                          insurance: purchasePrice * 0.003, // 0.3% of value
                          management_fee_percent: 6, // 6% of gross rent (self-managed)
                          maintenance_repairs: purchasePrice * 0.01, // 1% of value
                          utilities_electric: grossRent * 0.01, // 1% of gross rent
                          utilities_water: grossRent * 0.02, // 2% of gross rent
                          landscaping: grossRent * 0.005, // 0.5% of gross rent
                          pest_control: 600, // $50/month
                          other_expenses: grossRent * 0.01, // 1% of gross rent
                          capital_reserves_percent: 3, // 3% reserves
                          expense_growth_rate: 2.5 // 2.5% annual growth
                        }
                      }));
                    }}
                  >
                    Apply Aggressive Defaults
                  </Button>
                </div>
              </div>
              <div className="text-sm text-gray-600">
                Industry Standard Operating Expense Ratio: <strong>35-50%</strong> for multifamily properties (50% Rule as quick estimate)
              </div>
            </Card>

            {/* Fixed Operating Expenses */}
            <Card className="p-6">
              <h3 className="text-xl font-semibold mb-6" style={{ color: navyColor }}>
                Fixed Operating Expenses
              </h3>
              <div id="fixed-expenses-form" className="space-y-4">
                {/* Property Taxes with toggle */}
                <div className="border rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-gray-700">
                      Property Taxes
                    </label>
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant={analysis.expense_data.use_percent_for_taxes ? "default" : "outline"}
                        onClick={() => {
                          const usePercent = !analysis.expense_data.use_percent_for_taxes;
                          const purchasePrice = analysis.property_data.purchase_price;
                          setAnalysis(prev => ({
                            ...prev,
                            expense_data: {
                              ...prev.expense_data,
                              use_percent_for_taxes: usePercent,
                              property_taxes: usePercent ? purchasePrice * 0.012 : prev.expense_data.property_taxes
                            }
                          }));
                        }}
                      >
                        Use %
                      </Button>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <Input
                      id="property-taxes-input"
                      type="number"
                      value={analysis.expense_data.property_taxes}
                      onChange={(e) => setAnalysis(prev => ({
                        ...prev,
                        expense_data: {
                          ...prev.expense_data,
                          property_taxes: parseFloat(e.target.value) || 0
                        }
                      }))}
                    />
                    <div className="flex items-center">
                      <span className="text-sm text-gray-500">
                        = {((analysis.expense_data.property_taxes / analysis.property_data.purchase_price) * 100).toFixed(2)}% of value
                      </span>
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">Industry standard: 1-1.5% of property value (FL avg: 1.2%)</div>
                </div>

                {/* Insurance with toggle */}
                <div className="border rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-gray-700">
                      Property Insurance
                    </label>
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant={analysis.expense_data.use_percent_for_insurance ? "default" : "outline"}
                        onClick={() => {
                          const usePercent = !analysis.expense_data.use_percent_for_insurance;
                          const purchasePrice = analysis.property_data.purchase_price;
                          setAnalysis(prev => ({
                            ...prev,
                            expense_data: {
                              ...prev.expense_data,
                              use_percent_for_insurance: usePercent,
                              insurance: usePercent ? purchasePrice * 0.005 : prev.expense_data.insurance
                            }
                          }));
                        }}
                      >
                        Use %
                      </Button>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <Input
                      id="insurance-input"
                      type="number"
                      value={analysis.expense_data.insurance}
                      onChange={(e) => setAnalysis(prev => ({
                        ...prev,
                        expense_data: {
                          ...prev.expense_data,
                          insurance: parseFloat(e.target.value) || 0
                        }
                      }))}
                    />
                    <div className="flex items-center">
                      <span className="text-sm text-gray-500">
                        = {((analysis.expense_data.insurance / analysis.property_data.purchase_price) * 100).toFixed(2)}% of value
                      </span>
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">Industry standard: 0.3-0.7% of property value (FL higher due to hurricanes)</div>
                </div>

                {/* Management Fee */}
                <div className="border rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-gray-700">
                      Property Management Fee
                    </label>
                    <span className="text-sm text-gray-500">
                      Annual: {formatCurrency((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12) * (analysis.expense_data.management_fee_percent / 100))}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="flex items-center gap-2">
                      <Input
                        id="management-fee-input"
                        type="number"
                        step="0.1"
                        value={analysis.expense_data.management_fee_percent}
                        onChange={(e) => setAnalysis(prev => ({
                          ...prev,
                          expense_data: {
                            ...prev.expense_data,
                            management_fee_percent: parseFloat(e.target.value) || 0
                          }
                        }))}
                      />
                      <span className="text-sm">%</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-sm text-gray-500">of gross rental income</span>
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">Industry standard: 6-10% (professional), 0% (self-managed)</div>
                </div>

                {/* HOA Fees */}
                <div className="border rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-gray-700">
                      HOA/Condo Fees
                    </label>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <Input
                      id="hoa-fees-input"
                      type="number"
                      value={analysis.expense_data.hoa_fees || 0}
                      onChange={(e) => setAnalysis(prev => ({
                        ...prev,
                        expense_data: {
                          ...prev.expense_data,
                          hoa_fees: parseFloat(e.target.value) || 0
                        }
                      }))}
                      placeholder="Annual HOA fees"
                    />
                    <div className="flex items-center">
                      <span className="text-sm text-gray-500">
                        Monthly: {formatCurrency((analysis.expense_data.hoa_fees || 0) / 12)}
                      </span>
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">Typical: $200-500/month for condos, $100-300 for SFH in HOA</div>
                </div>
              </div>
            </Card>

            {/* Variable Operating Expenses */}
            <Card className="p-6">
              <h3 className="text-xl font-semibold mb-6" style={{ color: navyColor }}>
                Variable Operating Expenses
              </h3>
              <div id="variable-expenses-form" className="space-y-4">
                {/* Maintenance & Repairs */}
                <div className="border rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-gray-700">
                      Maintenance & Repairs
                    </label>
                    <Button
                      size="sm"
                      variant={analysis.expense_data.use_percent_for_maintenance ? "default" : "outline"}
                      onClick={() => {
                        const usePercent = !analysis.expense_data.use_percent_for_maintenance;
                        const purchasePrice = analysis.property_data.purchase_price;
                        setAnalysis(prev => ({
                          ...prev,
                          expense_data: {
                            ...prev.expense_data,
                            use_percent_for_maintenance: usePercent,
                            maintenance_repairs: usePercent ? purchasePrice * 0.015 : prev.expense_data.maintenance_repairs
                          }
                        }));
                      }}
                    >
                      Use %
                    </Button>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <Input
                      id="maintenance-input"
                      type="number"
                      value={analysis.expense_data.maintenance_repairs}
                      onChange={(e) => setAnalysis(prev => ({
                        ...prev,
                        expense_data: {
                          ...prev.expense_data,
                          maintenance_repairs: parseFloat(e.target.value) || 0
                        }
                      }))}
                    />
                    <div className="flex items-center">
                      <span className="text-sm text-gray-500">
                        = {((analysis.expense_data.maintenance_repairs / analysis.property_data.purchase_price) * 100).toFixed(2)}% of value
                      </span>
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">Rule of 1%: Newer properties 1%, Older 2-3% of value annually</div>
                </div>

                {/* Utilities Section */}
                <div className="border rounded-lg p-4">
                  <h4 className="font-medium mb-3">Utilities (Landlord-Paid)</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm text-gray-600">Electric (Annual)</label>
                      <Input
                        type="number"
                        value={analysis.expense_data.utilities_electric}
                        onChange={(e) => setAnalysis(prev => ({
                          ...prev,
                          expense_data: {
                            ...prev.expense_data,
                            utilities_electric: parseFloat(e.target.value) || 0
                          }
                        }))}
                      />
                      <div className="text-xs text-gray-500 mt-1">Common areas: $50-150/month</div>
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">Water/Sewer (Annual)</label>
                      <Input
                        type="number"
                        value={analysis.expense_data.utilities_water}
                        onChange={(e) => setAnalysis(prev => ({
                          ...prev,
                          expense_data: {
                            ...prev.expense_data,
                            utilities_water: parseFloat(e.target.value) || 0
                          }
                        }))}
                      />
                      <div className="text-xs text-gray-500 mt-1">$30-100/unit/month if included</div>
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">Trash/Recycling (Annual)</label>
                      <Input
                        type="number"
                        value={analysis.expense_data.utilities_trash || 0}
                        onChange={(e) => setAnalysis(prev => ({
                          ...prev,
                          expense_data: {
                            ...prev.expense_data,
                            utilities_trash: parseFloat(e.target.value) || 0
                          }
                        }))}
                      />
                      <div className="text-xs text-gray-500 mt-1">$15-30/unit/month</div>
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">Gas (Annual)</label>
                      <Input
                        type="number"
                        value={analysis.expense_data.utilities_gas || 0}
                        onChange={(e) => setAnalysis(prev => ({
                          ...prev,
                          expense_data: {
                            ...prev.expense_data,
                            utilities_gas: parseFloat(e.target.value) || 0
                          }
                        }))}
                      />
                      <div className="text-xs text-gray-500 mt-1">If applicable</div>
                    </div>
                  </div>
                </div>

                {/* Professional Services */}
                <div className="border rounded-lg p-4">
                  <h4 className="font-medium mb-3">Professional Services</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="text-sm text-gray-600">Landscaping (Annual)</label>
                      <Input
                        type="number"
                        value={analysis.expense_data.landscaping}
                        onChange={(e) => setAnalysis(prev => ({
                          ...prev,
                          expense_data: {
                            ...prev.expense_data,
                            landscaping: parseFloat(e.target.value) || 0
                          }
                        }))}
                      />
                      <div className="text-xs text-gray-500 mt-1">$50-200/month typical</div>
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">Pest Control (Annual)</label>
                      <Input
                        type="number"
                        value={analysis.expense_data.pest_control}
                        onChange={(e) => setAnalysis(prev => ({
                          ...prev,
                          expense_data: {
                            ...prev.expense_data,
                            pest_control: parseFloat(e.target.value) || 0
                          }
                        }))}
                      />
                      <div className="text-xs text-gray-500 mt-1">$50-100/month</div>
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">Pool/Spa Maint. (Annual)</label>
                      <Input
                        type="number"
                        value={analysis.expense_data.pool_maintenance || 0}
                        onChange={(e) => setAnalysis(prev => ({
                          ...prev,
                          expense_data: {
                            ...prev.expense_data,
                            pool_maintenance: parseFloat(e.target.value) || 0
                          }
                        }))}
                      />
                      <div className="text-xs text-gray-500 mt-1">$100-300/month if applicable</div>
                    </div>
                  </div>
                </div>

                {/* Administrative Expenses */}
                <div className="border rounded-lg p-4">
                  <h4 className="font-medium mb-3">Administrative Expenses</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="text-sm text-gray-600">Accounting/Legal (Annual)</label>
                      <Input
                        type="number"
                        value={analysis.expense_data.accounting_legal || 0}
                        onChange={(e) => setAnalysis(prev => ({
                          ...prev,
                          expense_data: {
                            ...prev.expense_data,
                            accounting_legal: parseFloat(e.target.value) || 0
                          }
                        }))}
                      />
                      <div className="text-xs text-gray-500 mt-1">$500-2000/year</div>
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">Advertising/Marketing (Annual)</label>
                      <Input
                        type="number"
                        value={analysis.expense_data.advertising || 0}
                        onChange={(e) => setAnalysis(prev => ({
                          ...prev,
                          expense_data: {
                            ...prev.expense_data,
                            advertising: parseFloat(e.target.value) || 0
                          }
                        }))}
                      />
                      <div className="text-xs text-gray-500 mt-1">2-3% of gross rent</div>
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">Office/Supplies (Annual)</label>
                      <Input
                        type="number"
                        value={analysis.expense_data.office_supplies || 0}
                        onChange={(e) => setAnalysis(prev => ({
                          ...prev,
                          expense_data: {
                            ...prev.expense_data,
                            office_supplies: parseFloat(e.target.value) || 0
                          }
                        }))}
                      />
                      <div className="text-xs text-gray-500 mt-1">$50-200/month</div>
                    </div>
                  </div>
                </div>

                {/* Turnover Costs */}
                <div className="border rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-gray-700">
                      Turnover & Vacancy Costs
                    </label>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <Input
                      id="turnover-costs-input"
                      type="number"
                      value={analysis.expense_data.turnover_costs || 0}
                      onChange={(e) => setAnalysis(prev => ({
                        ...prev,
                        expense_data: {
                          ...prev.expense_data,
                          turnover_costs: parseFloat(e.target.value) || 0
                        }
                      }))}
                      placeholder="Annual turnover costs"
                    />
                    <div className="flex items-center">
                      <span className="text-sm text-gray-500">
                        Per turnover: {formatCurrency((analysis.expense_data.turnover_costs || 0) / Math.max(1, analysis.income_data.vacancy_rate / 10))}
                      </span>
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">Painting, cleaning, minor repairs: $500-2000 per unit turnover</div>
                </div>

                {/* Other Expenses */}
                <div className="border rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-gray-700">
                      Other/Miscellaneous Expenses
                    </label>
                  </div>
                  <Input
                    id="other-expenses-input"
                    type="number"
                    value={analysis.expense_data.other_expenses}
                    onChange={(e) => setAnalysis(prev => ({
                      ...prev,
                      expense_data: {
                        ...prev.expense_data,
                        other_expenses: parseFloat(e.target.value) || 0
                      }
                    }))}
                  />
                  <div className="text-xs text-gray-500 mt-1">Security, permits, licenses, miscellaneous</div>
                </div>
              </div>
            </Card>

            {/* Capital Reserves & Growth */}
            <Card className="p-6">
              <h3 className="text-xl font-semibold mb-6" style={{ color: navyColor }}>
                Capital Reserves & Growth Assumptions
              </h3>
              <div id="reserves-growth-form" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Capital Reserves (% of Gross Income)
                  </label>
                  <Input
                    id="capital-reserves-input"
                    type="number"
                    step="0.1"
                    value={analysis.expense_data.capital_reserves_percent}
                    onChange={(e) => setAnalysis(prev => ({
                      ...prev,
                      expense_data: {
                        ...prev.expense_data,
                        capital_reserves_percent: parseFloat(e.target.value) || 0
                      }
                    }))}
                  />
                  <div className="text-xs text-gray-500 mt-1">Industry standard: 5-10% for major repairs/replacements</div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Annual Expense Growth (%)
                  </label>
                  <Input
                    id="expense-growth-input"
                    type="number"
                    step="0.1"
                    value={analysis.expense_data.expense_growth_rate}
                    onChange={(e) => setAnalysis(prev => ({
                      ...prev,
                      expense_data: {
                        ...prev.expense_data,
                        expense_growth_rate: parseFloat(e.target.value) || 0
                      }
                    }))}
                  />
                  <div className="text-xs text-gray-500 mt-1">Historical inflation: 2-4% annually</div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Capital Reserves (Annual Amount)
                  </label>
                  <div className="p-3 bg-purple-50 rounded-lg">
                    <span className="text-lg font-semibold text-purple-600">
                      {formatCurrency(
                        (analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12 +
                         analysis.income_data.other_income_monthly * 12) *
                        (analysis.expense_data.capital_reserves_percent / 100)
                      )}
                    </span>
                  </div>
                </div>
              </div>

              {/* Replacement Schedule */}
              <div className="mt-6">
                <h4 className="font-medium mb-3">Major Replacement Schedule (Reference)</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                  <div className="p-2 bg-gray-50 rounded">
                    <div className="font-medium">Roof</div>
                    <div className="text-xs text-gray-500">20-30 years</div>
                    <div className="text-xs">$5-10k per 1000 sqft</div>
                  </div>
                  <div className="p-2 bg-gray-50 rounded">
                    <div className="font-medium">HVAC</div>
                    <div className="text-xs text-gray-500">15-20 years</div>
                    <div className="text-xs">$3-7k per unit</div>
                  </div>
                  <div className="p-2 bg-gray-50 rounded">
                    <div className="font-medium">Flooring</div>
                    <div className="text-xs text-gray-500">5-10 years</div>
                    <div className="text-xs">$3-8 per sqft</div>
                  </div>
                  <div className="p-2 bg-gray-50 rounded">
                    <div className="font-medium">Appliances</div>
                    <div className="text-xs text-gray-500">10-15 years</div>
                    <div className="text-xs">$2-3k per unit</div>
                  </div>
                  <div className="p-2 bg-gray-50 rounded">
                    <div className="font-medium">Water Heater</div>
                    <div className="text-xs text-gray-500">8-12 years</div>
                    <div className="text-xs">$800-1500 each</div>
                  </div>
                  <div className="p-2 bg-gray-50 rounded">
                    <div className="font-medium">Paint (Ext)</div>
                    <div className="text-xs text-gray-500">7-10 years</div>
                    <div className="text-xs">$3-5k per unit</div>
                  </div>
                  <div className="p-2 bg-gray-50 rounded">
                    <div className="font-medium">Paint (Int)</div>
                    <div className="text-xs text-gray-500">3-5 years</div>
                    <div className="text-xs">$1-2k per unit</div>
                  </div>
                  <div className="p-2 bg-gray-50 rounded">
                    <div className="font-medium">Windows</div>
                    <div className="text-xs text-gray-500">15-20 years</div>
                    <div className="text-xs">$300-800 each</div>
                  </div>
                </div>
              </div>
            </Card>

            {/* Expense Summary */}
            <Card className="p-6">
              <h3 className="text-xl font-semibold mb-6" style={{ color: navyColor }}>
                Total Operating Expenses Summary
              </h3>
              <div id="expense-summary" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="p-4 rounded-lg bg-red-50">
                  <div className="text-sm text-gray-600 mb-1">Total Fixed Expenses</div>
                  <div className="text-2xl font-bold text-red-600">
                    {formatCurrency(
                      analysis.expense_data.property_taxes +
                      analysis.expense_data.insurance +
                      ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12) *
                       (analysis.expense_data.management_fee_percent / 100)) +
                      (analysis.expense_data.hoa_fees || 0)
                    )}
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-orange-50">
                  <div className="text-sm text-gray-600 mb-1">Total Variable Expenses</div>
                  <div className="text-2xl font-bold text-orange-600">
                    {formatCurrency(
                      analysis.expense_data.maintenance_repairs +
                      analysis.expense_data.utilities_electric +
                      analysis.expense_data.utilities_water +
                      (analysis.expense_data.utilities_trash || 0) +
                      (analysis.expense_data.utilities_gas || 0) +
                      analysis.expense_data.landscaping +
                      analysis.expense_data.pest_control +
                      (analysis.expense_data.pool_maintenance || 0) +
                      (analysis.expense_data.accounting_legal || 0) +
                      (analysis.expense_data.advertising || 0) +
                      (analysis.expense_data.office_supplies || 0) +
                      (analysis.expense_data.turnover_costs || 0) +
                      analysis.expense_data.other_expenses
                    )}
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-purple-50">
                  <div className="text-sm text-gray-600 mb-1">Capital Reserves</div>
                  <div className="text-2xl font-bold text-purple-600">
                    {formatCurrency(
                      (analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12 +
                       analysis.income_data.other_income_monthly * 12) *
                      (analysis.expense_data.capital_reserves_percent / 100)
                    )}
                  </div>
                </div>

                <div className="p-4 rounded-lg" style={{ backgroundColor: goldLightColor }}>
                  <div className="text-sm text-gray-600 mb-1">Total Operating Expenses</div>
                  <div className="text-2xl font-bold" style={{ color: navyColor }}>
                    {formatCurrency(
                      analysis.expense_data.property_taxes +
                      analysis.expense_data.insurance +
                      ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12) *
                       (analysis.expense_data.management_fee_percent / 100)) +
                      (analysis.expense_data.hoa_fees || 0) +
                      analysis.expense_data.maintenance_repairs +
                      analysis.expense_data.utilities_electric +
                      analysis.expense_data.utilities_water +
                      (analysis.expense_data.utilities_trash || 0) +
                      (analysis.expense_data.utilities_gas || 0) +
                      analysis.expense_data.landscaping +
                      analysis.expense_data.pest_control +
                      (analysis.expense_data.pool_maintenance || 0) +
                      (analysis.expense_data.accounting_legal || 0) +
                      (analysis.expense_data.advertising || 0) +
                      (analysis.expense_data.office_supplies || 0) +
                      (analysis.expense_data.turnover_costs || 0) +
                      analysis.expense_data.other_expenses +
                      ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12 +
                        analysis.income_data.other_income_monthly * 12) *
                       (analysis.expense_data.capital_reserves_percent / 100))
                    )}
                  </div>
                </div>
              </div>

              {/* Operating Expense Ratio */}
              <div className="mt-6 p-4 border-2 border-gray-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-semibold text-gray-700">Operating Expense Ratio (OER)</h4>
                    <div className="text-sm text-gray-500">Total Expenses ÷ Gross Rental Income</div>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-bold" style={{
                      color: (() => {
                        const oer = ((analysis.expense_data.property_taxes +
                          analysis.expense_data.insurance +
                          ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12) *
                           (analysis.expense_data.management_fee_percent / 100)) +
                          (analysis.expense_data.hoa_fees || 0) +
                          analysis.expense_data.maintenance_repairs +
                          analysis.expense_data.utilities_electric +
                          analysis.expense_data.utilities_water +
                          (analysis.expense_data.utilities_trash || 0) +
                          (analysis.expense_data.utilities_gas || 0) +
                          analysis.expense_data.landscaping +
                          analysis.expense_data.pest_control +
                          (analysis.expense_data.pool_maintenance || 0) +
                          (analysis.expense_data.accounting_legal || 0) +
                          (analysis.expense_data.advertising || 0) +
                          (analysis.expense_data.office_supplies || 0) +
                          (analysis.expense_data.turnover_costs || 0) +
                          analysis.expense_data.other_expenses) /
                          (analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12)) * 100;
                        return oer < 35 ? '#10b981' : oer < 50 ? '#f59e0b' : '#ef4444';
                      })()
                    }}>
                      {((
                        (analysis.expense_data.property_taxes +
                         analysis.expense_data.insurance +
                         ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12) *
                          (analysis.expense_data.management_fee_percent / 100)) +
                         (analysis.expense_data.hoa_fees || 0) +
                         analysis.expense_data.maintenance_repairs +
                         analysis.expense_data.utilities_electric +
                         analysis.expense_data.utilities_water +
                         (analysis.expense_data.utilities_trash || 0) +
                         (analysis.expense_data.utilities_gas || 0) +
                         analysis.expense_data.landscaping +
                         analysis.expense_data.pest_control +
                         (analysis.expense_data.pool_maintenance || 0) +
                         (analysis.expense_data.accounting_legal || 0) +
                         (analysis.expense_data.advertising || 0) +
                         (analysis.expense_data.office_supplies || 0) +
                         (analysis.expense_data.turnover_costs || 0) +
                         analysis.expense_data.other_expenses) /
                        (analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12)
                      ) * 100).toFixed(1)}%
                    </div>
                    <div className="text-sm text-gray-500">
                      {(() => {
                        const oer = ((analysis.expense_data.property_taxes +
                          analysis.expense_data.insurance +
                          ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12) *
                           (analysis.expense_data.management_fee_percent / 100)) +
                          (analysis.expense_data.hoa_fees || 0) +
                          analysis.expense_data.maintenance_repairs +
                          analysis.expense_data.utilities_electric +
                          analysis.expense_data.utilities_water +
                          (analysis.expense_data.utilities_trash || 0) +
                          (analysis.expense_data.utilities_gas || 0) +
                          analysis.expense_data.landscaping +
                          analysis.expense_data.pest_control +
                          (analysis.expense_data.pool_maintenance || 0) +
                          (analysis.expense_data.accounting_legal || 0) +
                          (analysis.expense_data.advertising || 0) +
                          (analysis.expense_data.office_supplies || 0) +
                          (analysis.expense_data.turnover_costs || 0) +
                          analysis.expense_data.other_expenses) /
                          (analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12)) * 100;
                        return oer < 35 ? 'Excellent' : oer < 50 ? 'Good' : 'Review Needed';
                      })()}
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </TabsContent>

        {/* Returns/Cash Flow Analysis Tab */}
        <TabsContent value="returns" className="mt-6">
          <div className="space-y-6">
            {/* Cash Flow Summary */}
            <Card className="p-6">
              <h3 className="text-xl font-semibold mb-6" style={{ color: navyColor }}>
                Cash Flow Analysis Summary
              </h3>
              <div id="cash-flow-summary" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="p-4 rounded-lg bg-green-50">
                  <div className="text-sm text-gray-600 mb-1">Gross Potential Rent</div>
                  <div className="text-2xl font-bold text-green-600">
                    {formatCurrency(analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12)}
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-blue-50">
                  <div className="text-sm text-gray-600 mb-1">Effective Gross Income</div>
                  <div className="text-2xl font-bold text-blue-600">
                    {formatCurrency(
                      (analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12) *
                      (1 - analysis.income_data.vacancy_rate / 100) +
                      (analysis.income_data.other_income_monthly * 12)
                    )}
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-red-50">
                  <div className="text-sm text-gray-600 mb-1">Total Operating Expenses</div>
                  <div className="text-2xl font-bold text-red-600">
                    -{formatCurrency(
                      analysis.expense_data.property_taxes +
                      analysis.expense_data.insurance +
                      ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12) *
                       (analysis.expense_data.management_fee_percent / 100)) +
                      analysis.expense_data.maintenance_repairs +
                      analysis.expense_data.utilities_electric +
                      analysis.expense_data.utilities_water +
                      analysis.expense_data.landscaping +
                      analysis.expense_data.pest_control +
                      analysis.expense_data.other_expenses +
                      ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12 +
                        analysis.income_data.other_income_monthly * 12) *
                       (analysis.expense_data.capital_reserves_percent / 100))
                    )}
                  </div>
                </div>

                <div className="p-4 rounded-lg" style={{ backgroundColor: goldLightColor }}>
                  <div className="text-sm text-gray-600 mb-1">Net Operating Income</div>
                  <div className="text-2xl font-bold" style={{ color: navyColor }}>
                    {(() => {
                      const egi = (analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12) * (1 - analysis.income_data.vacancy_rate / 100) + (analysis.income_data.other_income_monthly * 12);
                      const totalExpenses = analysis.expense_data.property_taxes + analysis.expense_data.insurance + ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12) * (analysis.expense_data.management_fee_percent / 100)) + analysis.expense_data.maintenance_repairs + analysis.expense_data.utilities_electric + analysis.expense_data.utilities_water + analysis.expense_data.landscaping + analysis.expense_data.pest_control + analysis.expense_data.other_expenses + ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12 + analysis.income_data.other_income_monthly * 12) * (analysis.expense_data.capital_reserves_percent / 100));
                      return formatCurrency(egi - totalExpenses);
                    })()}
                  </div>
                </div>
              </div>
            </Card>

            {/* Key Return Metrics */}
            <Card className="p-6">
              <h3 className="text-xl font-semibold mb-6" style={{ color: navyColor }}>
                Key Investment Returns
              </h3>
              <div id="return-metrics" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="p-4 rounded-lg" style={{ backgroundColor: goldLightColor }}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">Cap Rate</span>
                    <Target className="w-4 h-4" style={{ color: goldColor }} />
                  </div>
                  <div className="text-3xl font-bold" style={{ color: navyColor }}>
                    {(() => {
                      const noi = ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12) * (1 - analysis.income_data.vacancy_rate / 100) + (analysis.income_data.other_income_monthly * 12)) - (analysis.expense_data.property_taxes + analysis.expense_data.insurance + ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12) * (analysis.expense_data.management_fee_percent / 100)) + analysis.expense_data.maintenance_repairs + analysis.expense_data.utilities_electric + analysis.expense_data.utilities_water + analysis.expense_data.landscaping + analysis.expense_data.pest_control + analysis.expense_data.other_expenses + ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12 + analysis.income_data.other_income_monthly * 12) * (analysis.expense_data.capital_reserves_percent / 100)));
                      const capRate = (noi / analysis.property_data.purchase_price) * 100;
                      return formatPercent(capRate / 100);
                    })()}
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-blue-50">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">Cash-on-Cash Return</span>
                    <Percent className="w-4 h-4 text-blue-600" />
                  </div>
                  <div className="text-3xl font-bold text-blue-600">
                    {(() => {
                      const noi = ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12) * (1 - analysis.income_data.vacancy_rate / 100) + (analysis.income_data.other_income_monthly * 12)) - (analysis.expense_data.property_taxes + analysis.expense_data.insurance + ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12) * (analysis.expense_data.management_fee_percent / 100)) + analysis.expense_data.maintenance_repairs + analysis.expense_data.utilities_electric + analysis.expense_data.utilities_water + analysis.expense_data.landscaping + analysis.expense_data.pest_control + analysis.expense_data.other_expenses + ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12 + analysis.income_data.other_income_monthly * 12) * (analysis.expense_data.capital_reserves_percent / 100)));
                      const loanAmount = analysis.property_data.purchase_price * (100 - analysis.financing_data.down_payment_percent) / 100;
                      const annualDebtService = calculateMortgagePayment(loanAmount, analysis.financing_data.interest_rate, analysis.financing_data.loan_term_years) * 12;
                      const beforeTaxCashFlow = noi - annualDebtService;
                      const cashInvested = (analysis.property_data.purchase_price * analysis.financing_data.down_payment_percent / 100) + (analysis.property_data.purchase_price * analysis.financing_data.closing_costs_percent / 100) + analysis.financing_data.points_fees;
                      const cochReturn = (beforeTaxCashFlow / cashInvested) * 100;
                      return formatPercent(cochReturn / 100);
                    })()}
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-green-50">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">DSCR</span>
                    <CheckCircle className="w-4 h-4 text-green-600" />
                  </div>
                  <div className="text-3xl font-bold text-green-600">
                    {(() => {
                      const noi = ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12) * (1 - analysis.income_data.vacancy_rate / 100) + (analysis.income_data.other_income_monthly * 12)) - (analysis.expense_data.property_taxes + analysis.expense_data.insurance + ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12) * (analysis.expense_data.management_fee_percent / 100)) + analysis.expense_data.maintenance_repairs + analysis.expense_data.utilities_electric + analysis.expense_data.utilities_water + analysis.expense_data.landscaping + analysis.expense_data.pest_control + analysis.expense_data.other_expenses + ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12 + analysis.income_data.other_income_monthly * 12) * (analysis.expense_data.capital_reserves_percent / 100)));
                      const loanAmount = analysis.property_data.purchase_price * (100 - analysis.financing_data.down_payment_percent) / 100;
                      const annualDebtService = calculateMortgagePayment(loanAmount, analysis.financing_data.interest_rate, analysis.financing_data.loan_term_years) * 12;
                      const dscr = noi / annualDebtService;
                      return dscr.toFixed(2);
                    })()}
                  </div>
                </div>

                <div className="p-4 rounded-lg" style={{ backgroundColor: navyColor }}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-white/90">Investment Grade</span>
                    <div className="text-center">
                      <div className={`text-2xl font-bold ${investmentGrade.color === 'text-green-600' ? 'text-green-400' : investmentGrade.color === 'text-blue-600' ? 'text-blue-400' : investmentGrade.color === 'text-yellow-600' ? 'text-yellow-400' : 'text-red-400'}`}>
                        {investmentGrade.grade}
                      </div>
                    </div>
                  </div>
                  <div className="text-sm text-white/80 mt-3">
                    Monthly Cash Flow:
                  </div>
                  <div className="text-2xl font-bold text-white">
                    {(() => {
                      const noi = ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12) * (1 - analysis.income_data.vacancy_rate / 100) + (analysis.income_data.other_income_monthly * 12)) - (analysis.expense_data.property_taxes + analysis.expense_data.insurance + ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12) * (analysis.expense_data.management_fee_percent / 100)) + analysis.expense_data.maintenance_repairs + analysis.expense_data.utilities_electric + analysis.expense_data.utilities_water + analysis.expense_data.landscaping + analysis.expense_data.pest_control + analysis.expense_data.other_expenses + ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12 + analysis.income_data.other_income_monthly * 12) * (analysis.expense_data.capital_reserves_percent / 100)));
                      const loanAmount = analysis.property_data.purchase_price * (100 - analysis.financing_data.down_payment_percent) / 100;
                      const monthlyPayment = calculateMortgagePayment(loanAmount, analysis.financing_data.interest_rate, analysis.financing_data.loan_term_years);
                      const monthlyCashFlow = (noi / 12) - monthlyPayment;
                      return formatCurrency(monthlyCashFlow);
                    })()}
                  </div>
                </div>
              </div>
            </Card>

            {/* 10-Year Cash Flow Projection */}
            <Card className="p-6">
              <h3 className="text-xl font-semibold mb-6" style={{ color: navyColor }}>
                10-Year Cash Flow Projection
              </h3>
              <div id="cash-flow-projection" className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2">Year</th>
                      <th className="text-right py-2">Gross Rent</th>
                      <th className="text-right py-2">Effective Gross</th>
                      <th className="text-right py-2">Operating Expenses</th>
                      <th className="text-right py-2">NOI</th>
                      <th className="text-right py-2">Debt Service</th>
                      <th className="text-right py-2">Before Tax CF</th>
                      <th className="text-right py-2">Cumulative CF</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(() => {
                      const rows = [];
                      let cumulativeCF = 0;
                      const baseRent = analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12;
                      const loanAmount = analysis.property_data.purchase_price * (100 - analysis.financing_data.down_payment_percent) / 100;
                      const annualDebtService = calculateMortgagePayment(loanAmount, analysis.financing_data.interest_rate, analysis.financing_data.loan_term_years) * 12;

                      for (let year = 1; year <= 10; year++) {
                        const grossRent = baseRent * Math.pow(1 + analysis.income_data.annual_rent_growth / 100, year - 1);
                        const effectiveGross = grossRent * (1 - analysis.income_data.vacancy_rate / 100) + (analysis.income_data.other_income_monthly * 12);
                        const baseExpenses = analysis.expense_data.property_taxes + analysis.expense_data.insurance + (grossRent * (analysis.expense_data.management_fee_percent / 100)) + analysis.expense_data.maintenance_repairs + analysis.expense_data.utilities_electric + analysis.expense_data.utilities_water + analysis.expense_data.landscaping + analysis.expense_data.pest_control + analysis.expense_data.other_expenses + (effectiveGross * (analysis.expense_data.capital_reserves_percent / 100));
                        const operatingExpenses = baseExpenses * Math.pow(1 + analysis.expense_data.expense_growth_rate / 100, year - 1);
                        const noi = effectiveGross - operatingExpenses;
                        const beforeTaxCF = noi - annualDebtService;
                        cumulativeCF += beforeTaxCF;

                        rows.push(
                          <tr key={year} className="border-b hover:bg-gray-50">
                            <td className="py-2">{year}</td>
                            <td className="text-right py-2">{formatCurrency(grossRent)}</td>
                            <td className="text-right py-2">{formatCurrency(effectiveGross)}</td>
                            <td className="text-right py-2">{formatCurrency(operatingExpenses)}</td>
                            <td className="text-right py-2 font-semibold">{formatCurrency(noi)}</td>
                            <td className="text-right py-2">{formatCurrency(annualDebtService)}</td>
                            <td className={`text-right py-2 font-semibold ${beforeTaxCF >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {formatCurrency(beforeTaxCF)}
                            </td>
                            <td className={`text-right py-2 font-semibold ${cumulativeCF >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {formatCurrency(cumulativeCF)}
                            </td>
                          </tr>
                        );
                      }
                      return rows;
                    })()}
                  </tbody>
                </table>
              </div>
            </Card>

            {/* Investment Grading & Analysis Parameters */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Investment Grade */}
              <Card className="p-6">
                <h3 className="text-xl font-semibold mb-6" style={{ color: navyColor }}>
                  Investment Grade Analysis
                </h3>
                <div id="investment-grade" className="space-y-4">
                  {(() => {
                    const noi = ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12) * (1 - analysis.income_data.vacancy_rate / 100) + (analysis.income_data.other_income_monthly * 12)) - (analysis.expense_data.property_taxes + analysis.expense_data.insurance + ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12) * (analysis.expense_data.management_fee_percent / 100)) + analysis.expense_data.maintenance_repairs + analysis.expense_data.utilities_electric + analysis.expense_data.utilities_water + analysis.expense_data.landscaping + analysis.expense_data.pest_control + analysis.expense_data.other_expenses + ((analysis.unit_mix_data.reduce((sum, unit) => sum + (unit.unit_count * unit.current_rent), 0) * 12 + analysis.income_data.other_income_monthly * 12) * (analysis.expense_data.capital_reserves_percent / 100)));
                    const capRate = (noi / analysis.property_data.purchase_price) * 100;
                    const loanAmount = analysis.property_data.purchase_price * (100 - analysis.financing_data.down_payment_percent) / 100;
                    const annualDebtService = calculateMortgagePayment(loanAmount, analysis.financing_data.interest_rate, analysis.financing_data.loan_term_years) * 12;
                    const dscr = noi / annualDebtService;
                    const beforeTaxCashFlow = noi - annualDebtService;
                    const cashInvested = (analysis.property_data.purchase_price * analysis.financing_data.down_payment_percent / 100) + (analysis.property_data.purchase_price * analysis.financing_data.closing_costs_percent / 100) + analysis.financing_data.points_fees;
                    const cochReturn = (beforeTaxCashFlow / cashInvested) * 100;

                    let grade = 'D';
                    let gradeColor = 'text-red-600';
                    let gradeBg = 'bg-red-50';

                    if (capRate >= 8 && cochReturn >= 12 && dscr >= 1.5) {
                      grade = 'A+';
                      gradeColor = 'text-green-600';
                      gradeBg = 'bg-green-50';
                    } else if (capRate >= 6 && cochReturn >= 8 && dscr >= 1.3) {
                      grade = 'A';
                      gradeColor = 'text-green-600';
                      gradeBg = 'bg-green-50';
                    } else if (capRate >= 5 && cochReturn >= 6 && dscr >= 1.2) {
                      grade = 'B+';
                      gradeColor = 'text-blue-600';
                      gradeBg = 'bg-blue-50';
                    } else if (capRate >= 4 && cochReturn >= 4 && dscr >= 1.1) {
                      grade = 'B';
                      gradeColor = 'text-blue-600';
                      gradeBg = 'bg-blue-50';
                    } else if (capRate >= 3 && cochReturn >= 2 && dscr >= 1.0) {
                      grade = 'C';
                      gradeColor = 'text-yellow-600';
                      gradeBg = 'bg-yellow-50';
                    }

                    return (
                      <div className={`p-6 rounded-lg text-center ${gradeBg}`}>
                        <div className="text-6xl font-bold mb-2" style={{ color: navyColor }}>
                          {grade}
                        </div>
                        <div className={`text-xl font-semibold ${gradeColor}`}>
                          Investment Grade
                        </div>
                        <div className="mt-4 text-sm text-gray-600">
                          <div>Cap Rate: {formatPercent(capRate / 100)}</div>
                          <div>Cash-on-Cash: {formatPercent(cochReturn / 100)}</div>
                          <div>DSCR: {dscr.toFixed(2)}</div>
                        </div>
                      </div>
                    );
                  })()}
                </div>
              </Card>

              {/* Analysis Parameters */}
              <Card className="p-6">
                <h3 className="text-xl font-semibold mb-6" style={{ color: navyColor }}>
                  Analysis Parameters
                </h3>
                <div id="analysis-parameters-form" className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Holding Period (Years)
                    </label>
                    <Input
                      id="holding-period-input"
                      type="number"
                      value={analysis.analysis_params.holding_period_years}
                      onChange={(e) => setAnalysis(prev => ({
                        ...prev,
                        analysis_params: {
                          ...prev.analysis_params,
                          holding_period_years: parseInt(e.target.value) || 0
                        }
                      }))}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Annual Appreciation (%)
                    </label>
                    <Input
                      id="appreciation-input"
                      type="number"
                      step="0.1"
                      value={analysis.analysis_params.annual_appreciation}
                      onChange={(e) => setAnalysis(prev => ({
                        ...prev,
                        analysis_params: {
                          ...prev.analysis_params,
                          annual_appreciation: parseFloat(e.target.value) || 0
                        }
                      }))}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Exit Cap Rate (%)
                    </label>
                    <Input
                      id="exit-cap-rate-input"
                      type="number"
                      step="0.1"
                      value={analysis.analysis_params.exit_cap_rate}
                      onChange={(e) => setAnalysis(prev => ({
                        ...prev,
                        analysis_params: {
                          ...prev.analysis_params,
                          exit_cap_rate: parseFloat(e.target.value) || 0
                        }
                      }))}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Selling Costs (%)
                    </label>
                    <Input
                      id="selling-costs-input"
                      type="number"
                      step="0.1"
                      value={analysis.analysis_params.selling_costs_percent}
                      onChange={(e) => setAnalysis(prev => ({
                        ...prev,
                        analysis_params: {
                          ...prev.analysis_params,
                          selling_costs_percent: parseFloat(e.target.value) || 0
                        }
                      }))}
                    />
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}