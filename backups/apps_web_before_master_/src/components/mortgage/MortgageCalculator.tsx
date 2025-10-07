import React, { useState, useEffect } from 'react';
import { Calculator, TrendingUp, DollarSign, Calendar, Percent, Info } from 'lucide-react';
import { mortgageService, MortgageCalculation } from '@/services/mortgageService';

interface MortgageCalculatorProps {
  initialAmount?: number;
  className?: string;
  onCalculation?: (result: MortgageCalculation) => void;
}

export const MortgageCalculator: React.FC<MortgageCalculatorProps> = ({
  initialAmount = 400000,
  className = '',
  onCalculation,
}) => {
  const [loanAmount, setLoanAmount] = useState(initialAmount);
  const [interestRate, setInterestRate] = useState(6.5);
  const [loanTerm, setLoanTerm] = useState(30);
  const [result, setResult] = useState<MortgageCalculation | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [error, setError] = useState('');

  // Calculate on input changes
  useEffect(() => {
    const timer = setTimeout(() => {
      if (loanAmount > 0 && interestRate >= 0 && loanTerm > 0) {
        calculateMortgage();
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [loanAmount, interestRate, loanTerm]);

  const calculateMortgage = async () => {
    setIsCalculating(true);
    setError('');

    try {
      const calculation = await mortgageService.calculateMortgage(
        loanAmount,
        interestRate,
        loanTerm
      );
      setResult(calculation);
      onCalculation?.(calculation);
    } catch (err) {
      setError('Failed to calculate mortgage. Please try again.');
      console.error('Mortgage calculation error:', err);
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

  const formatCurrencyDetailed = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  return (
    <div className={`mortgage-calculator ${className}`} id="mortgage-calculator-main">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center mb-6">
          <Calculator className="w-6 h-6 mr-2 text-blue-600" />
          <h2 className="text-2xl font-bold text-gray-800">Mortgage Calculator</h2>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Input Section */}
          <div className="space-y-4">
            {/* Loan Amount */}
            <div id="loan-amount-input">
              <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                <DollarSign className="w-4 h-4 mr-1" />
                Loan Amount
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">
                  $
                </span>
                <input
                  type="number"
                  value={loanAmount}
                  onChange={(e) => setLoanAmount(Number(e.target.value))}
                  className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="400000"
                  min="0"
                  step="1000"
                />
              </div>
            </div>

            {/* Interest Rate */}
            <div id="interest-rate-input">
              <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                <Percent className="w-4 h-4 mr-1" />
                Interest Rate (%)
              </label>
              <input
                type="number"
                value={interestRate}
                onChange={(e) => setInterestRate(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="6.5"
                min="0"
                max="30"
                step="0.1"
              />
            </div>

            {/* Loan Term */}
            <div id="loan-term-input">
              <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                <Calendar className="w-4 h-4 mr-1" />
                Loan Term (Years)
              </label>
              <select
                value={loanTerm}
                onChange={(e) => setLoanTerm(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value={10}>10 years</option>
                <option value={15}>15 years</option>
                <option value={20}>20 years</option>
                <option value={25}>25 years</option>
                <option value={30}>30 years</option>
              </select>
            </div>

            {/* Calculate Button */}
            <button
              onClick={calculateMortgage}
              disabled={isCalculating}
              className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition duration-200 disabled:bg-gray-400 font-semibold"
            >
              {isCalculating ? 'Calculating...' : 'Calculate Payment'}
            </button>

            {error && (
              <div className="text-red-500 text-sm mt-2">{error}</div>
            )}
          </div>

          {/* Results Section */}
          <div className="space-y-4">
            {result && (
              <>
                {/* Monthly Payment */}
                <div className="bg-blue-50 rounded-lg p-4" id="monthly-payment-result">
                  <div className="text-sm text-gray-600 mb-1">Monthly Payment</div>
                  <div className="text-3xl font-bold text-blue-600">
                    {formatCurrencyDetailed(result.monthly_payment)}
                  </div>
                </div>

                {/* Key Metrics */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-gray-50 rounded-lg p-3" id="total-interest-result">
                    <div className="text-xs text-gray-600 mb-1">Total Interest</div>
                    <div className="text-lg font-semibold text-gray-800">
                      {formatCurrency(result.total_interest)}
                    </div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3" id="total-paid-result">
                    <div className="text-xs text-gray-600 mb-1">Total Paid</div>
                    <div className="text-lg font-semibold text-gray-800">
                      {formatCurrency(result.total_paid)}
                    </div>
                  </div>
                </div>

                {/* Payment Breakdown */}
                <div className="bg-white border border-gray-200 rounded-lg p-4" id="payment-breakdown">
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                    <Info className="w-4 h-4 mr-1" />
                    Payment Breakdown
                  </h3>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Principal & Interest:</span>
                      <span className="font-medium">{formatCurrencyDetailed(result.monthly_payment)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Loan Amount:</span>
                      <span className="font-medium">{formatCurrency(result.loan_amount)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Interest/Principal Ratio:</span>
                      <span className="font-medium">
                        {(result.interest_to_principal_ratio * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Total Payments:</span>
                      <span className="font-medium">{result.term_months} months</span>
                    </div>
                  </div>
                </div>

                {/* Monthly Budget Impact */}
                <div className="bg-green-50 border border-green-200 rounded-lg p-4" id="budget-impact">
                  <h3 className="text-sm font-semibold text-green-800 mb-2">
                    Budget Recommendations
                  </h3>
                  <div className="text-sm text-green-700">
                    <div>• Recommended income: {formatCurrency(result.monthly_payment * 3.5)}/mo</div>
                    <div>• Max debt ratio: 28% of gross income</div>
                    <div>• Emergency fund: {formatCurrency(result.monthly_payment * 6)}</div>
                  </div>
                </div>
              </>
            )}

            {!result && !isCalculating && (
              <div className="bg-gray-50 rounded-lg p-8 text-center text-gray-500">
                <Calculator className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                <p>Enter loan details to calculate your monthly payment</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MortgageCalculator;