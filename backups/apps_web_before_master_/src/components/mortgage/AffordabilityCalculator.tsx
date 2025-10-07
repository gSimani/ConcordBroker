import React, { useState } from 'react';
import { Home, DollarSign, AlertCircle, CheckCircle, TrendingUp } from 'lucide-react';
import { mortgageService, AffordabilityResult } from '@/services/mortgageService';

const AffordabilityCalculator: React.FC = () => {
  const [monthlyIncome, setMonthlyIncome] = useState(8000);
  const [monthlyDebts, setMonthlyDebts] = useState(500);
  const [downPayment, setDownPayment] = useState(80000);
  const [interestRate, setInterestRate] = useState(6.5);
  const [loanTerm, setLoanTerm] = useState(30);
  const [propertyTax, setPropertyTax] = useState(5000);
  const [insurance, setInsurance] = useState(1200);
  const [pmi, setPmi] = useState(0);
  const [result, setResult] = useState<AffordabilityResult | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);

  const calculateAffordability = async () => {
    setIsCalculating(true);
    try {
      const affordability = await mortgageService.calculateAffordability(
        monthlyIncome,
        monthlyDebts,
        downPayment,
        interestRate,
        loanTerm,
        propertyTax,
        insurance,
        pmi
      );
      setResult(affordability);
    } catch (error) {
      console.error('Affordability calculation error:', error);
    } finally {
      setIsCalculating(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6" id="affordability-calculator">
      <div className="grid md:grid-cols-2 gap-6">
        {/* Input Section */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Your Financial Information</h3>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Monthly Gross Income
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
              <input
                type="number"
                value={monthlyIncome}
                onChange={(e) => setMonthlyIncome(Number(e.target.value))}
                className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                min="0"
                step="100"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Monthly Debt Payments
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
              <input
                type="number"
                value={monthlyDebts}
                onChange={(e) => setMonthlyDebts(Number(e.target.value))}
                className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                min="0"
                step="50"
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">Include car loans, credit cards, student loans</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Available Down Payment
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
              <input
                type="number"
                value={downPayment}
                onChange={(e) => setDownPayment(Number(e.target.value))}
                className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                min="0"
                step="5000"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Interest Rate (%)
            </label>
            <input
              type="number"
              value={interestRate}
              onChange={(e) => setInterestRate(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              min="0"
              max="20"
              step="0.1"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Annual Property Tax
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
              <input
                type="number"
                value={propertyTax}
                onChange={(e) => setPropertyTax(Number(e.target.value))}
                className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                min="0"
                step="100"
              />
            </div>
          </div>

          <button
            onClick={calculateAffordability}
            disabled={isCalculating}
            className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition duration-200 disabled:bg-gray-400 font-semibold"
          >
            {isCalculating ? 'Calculating...' : 'Calculate Affordability'}
          </button>
        </div>

        {/* Results Section */}
        <div className="space-y-4">
          {result ? (
            <>
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Your Home Buying Power</h3>

              {/* Maximum Home Price */}
              <div className={`rounded-lg p-4 ${result.affordable ? 'bg-green-50' : 'bg-red-50'}`}>
                <div className="flex items-center mb-2">
                  {result.affordable ? (
                    <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                  ) : (
                    <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
                  )}
                  <span className="font-semibold text-gray-800">Maximum Home Price</span>
                </div>
                <div className="text-3xl font-bold text-gray-900">
                  {formatCurrency(result.max_home_price)}
                </div>
                <div className="text-sm text-gray-600 mt-2">
                  Max Loan: {formatCurrency(result.max_loan_amount)}
                </div>
              </div>

              {/* Monthly Payment Breakdown */}
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h4 className="font-semibold text-gray-700 mb-3">Monthly Payment Breakdown</h4>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Principal & Interest:</span>
                    <span className="font-medium">
                      {formatCurrency(result.monthly_payment_breakdown.principal_interest)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Property Tax:</span>
                    <span className="font-medium">
                      {formatCurrency(result.monthly_payment_breakdown.property_tax)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Insurance:</span>
                    <span className="font-medium">
                      {formatCurrency(result.monthly_payment_breakdown.insurance)}
                    </span>
                  </div>
                  {result.monthly_payment_breakdown.pmi > 0 && (
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">PMI:</span>
                      <span className="font-medium">
                        {formatCurrency(result.monthly_payment_breakdown.pmi)}
                      </span>
                    </div>
                  )}
                  <div className="flex justify-between text-sm font-semibold pt-2 border-t">
                    <span>Total Monthly Payment:</span>
                    <span>{formatCurrency(result.monthly_payment_breakdown.total)}</span>
                  </div>
                </div>
              </div>

              {/* Debt Ratios */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-semibold text-gray-700 mb-3">Debt-to-Income Ratios</h4>
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600">Housing Ratio:</span>
                      <span className="font-medium">{result.debt_ratios.housing_ratio.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          result.debt_ratios.housing_ratio <= 28 ? 'bg-green-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${Math.min(result.debt_ratios.housing_ratio, 100)}%` }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600">Total Debt Ratio:</span>
                      <span className="font-medium">
                        {result.debt_ratios.projected_total_ratio.toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          result.debt_ratios.projected_total_ratio <= 36 ? 'bg-green-500' : 'bg-orange-500'
                        }`}
                        style={{ width: `${Math.min(result.debt_ratios.projected_total_ratio, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {!result.affordable && result.reason && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-start">
                    <AlertCircle className="w-5 h-5 text-red-600 mr-2 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-red-800 mb-1">Affordability Warning</h4>
                      <p className="text-sm text-red-700">{result.reason}</p>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="bg-gray-50 rounded-lg p-8 text-center text-gray-500">
              <Home className="w-12 h-12 mx-auto mb-3 text-gray-400" />
              <p>Enter your financial information to see how much home you can afford</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AffordabilityCalculator;