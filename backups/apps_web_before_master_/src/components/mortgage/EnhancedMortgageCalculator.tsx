import React, { useState, useEffect, useCallback } from 'react';
import {
  Calculator,
  TrendingUp,
  DollarSign,
  Calendar,
  Percent,
  Info,
  ChevronDown,
  ChevronUp,
  Home,
  FileText
} from 'lucide-react';
import { mortgageService, MortgageCalculation } from '@/services/mortgageService';

interface AmortizationRow {
  payment_number: number;
  payment_date: string;
  payment_amount: number;
  principal_payment: number;
  interest_payment: number;
  remaining_balance: number;
}

interface FinancingScenario {
  name: string;
  downPaymentPct: number;
  interestRate: number;
  loanTerm: number;
  monthlyPayment?: number;
  loanAmount?: number;
  cashRequired?: number;
  isCurrent?: boolean;
}

interface EnhancedMortgageCalculatorProps {
  propertyPrice?: number;
  className?: string;
  onCalculation?: (result: MortgageCalculation) => void;
}

export const EnhancedMortgageCalculator: React.FC<EnhancedMortgageCalculatorProps> = ({
  propertyPrice: initialPropertyPrice = 628040,
  className = '',
  onCalculation,
}) => {
  // Main inputs
  const [propertyPrice, setPropertyPrice] = useState(initialPropertyPrice);
  const [downPaymentPct, setDownPaymentPct] = useState(25);
  const [interestRate, setInterestRate] = useState(7.5);
  const [loanTerm, setLoanTerm] = useState(30);

  // Calculated values
  const [downPaymentAmount, setDownPaymentAmount] = useState(0);
  const [loanAmount, setLoanAmount] = useState(0);
  const [result, setResult] = useState<MortgageCalculation | null>(null);
  const [amortizationSchedule, setAmortizationSchedule] = useState<AmortizationRow[]>([]);
  const [scenarios, setScenarios] = useState<FinancingScenario[]>([]);

  // UI state
  const [isCalculating, setIsCalculating] = useState(false);
  const [showFullSchedule, setShowFullSchedule] = useState(false);
  const [error, setError] = useState('');

  // Format currency with proper locale
  const formatCurrency = (amount: number, decimals: number = 0) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(amount);
  };

  // Format number input value
  const formatInputValue = (value: string): string => {
    // Remove non-numeric characters except decimal
    const numericValue = value.replace(/[^0-9.]/g, '');
    // Add thousand separators
    const parts = numericValue.split('.');
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    return parts.join('.');
  };

  // Parse formatted input value
  const parseInputValue = (value: string): number => {
    return Number(value.replace(/,/g, ''));
  };

  // Calculate loan details
  useEffect(() => {
    const downPayment = propertyPrice * (downPaymentPct / 100);
    const loan = propertyPrice - downPayment;
    setDownPaymentAmount(downPayment);
    setLoanAmount(loan);
  }, [propertyPrice, downPaymentPct]);

  // Generate amortization schedule
  const generateAmortizationSchedule = useCallback((
    principal: number,
    rate: number,
    months: number,
    monthlyPayment: number
  ): AmortizationRow[] => {
    const schedule: AmortizationRow[] = [];
    let balance = principal;
    const monthlyRate = rate / 100 / 12;
    const startDate = new Date();

    for (let i = 1; i <= months; i++) {
      const paymentDate = new Date(startDate);
      paymentDate.setMonth(paymentDate.getMonth() + i);

      const interestPayment = balance * monthlyRate;
      const principalPayment = monthlyPayment - interestPayment;
      balance = Math.max(0, balance - principalPayment);

      schedule.push({
        payment_number: i,
        payment_date: paymentDate.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short'
        }),
        payment_amount: monthlyPayment,
        principal_payment: principalPayment,
        interest_payment: interestPayment,
        remaining_balance: balance
      });

      if (balance <= 0) break;
    }

    return schedule;
  }, []);

  // Calculate mortgage with debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      if (loanAmount > 0 && interestRate >= 0 && loanTerm > 0) {
        calculateMortgage();
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [loanAmount, interestRate, loanTerm]);

  // Generate financing scenarios
  useEffect(() => {
    const calculateScenario = async (
      name: string,
      downPct: number,
      rate: number,
      term: number,
      isCurrent: boolean = false
    ): Promise<FinancingScenario> => {
      const down = propertyPrice * (downPct / 100);
      const loan = propertyPrice - down;

      try {
        const calc = await mortgageService.calculateMortgage(loan, rate, term);
        return {
          name,
          downPaymentPct: downPct,
          interestRate: rate,
          loanTerm: term,
          monthlyPayment: calc.monthly_payment,
          loanAmount: loan,
          cashRequired: down,
          isCurrent
        };
      } catch {
        return {
          name,
          downPaymentPct: downPct,
          interestRate: rate,
          loanTerm: term,
          isCurrent
        };
      }
    };

    const loadScenarios = async () => {
      const [conservative, current, aggressive] = await Promise.all([
        calculateScenario('Conservative', 25, 8.0, 30),
        calculateScenario('Current', downPaymentPct, interestRate, loanTerm, true),
        calculateScenario('Aggressive', 20, 7.25, 30)
      ]);

      setScenarios([conservative, current, aggressive]);
    };

    loadScenarios();
  }, [propertyPrice, downPaymentPct, interestRate, loanTerm]);

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

      // Generate amortization schedule
      const schedule = generateAmortizationSchedule(
        loanAmount,
        interestRate,
        loanTerm * 12,
        calculation.monthly_payment
      );
      setAmortizationSchedule(schedule);

      onCalculation?.(calculation);
    } catch (err) {
      setError('Failed to calculate mortgage. Please try again.');
      console.error('Mortgage calculation error:', err);
    } finally {
      setIsCalculating(false);
    }
  };

  // Apply scenario settings
  const applyScenario = (scenario: FinancingScenario) => {
    setDownPaymentPct(scenario.downPaymentPct);
    setInterestRate(scenario.interestRate);
    setLoanTerm(scenario.loanTerm);
  };

  return (
    <div className={`enhanced-mortgage-calculator ${className}`} id="mortgage-calculator-main">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <Calculator className="w-6 h-6 mr-2 text-blue-600" />
            <h2 className="text-2xl font-bold text-gray-800">Enhanced Mortgage Calculator</h2>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Input Section */}
          <div className="lg:col-span-1 space-y-4">
            {/* Property Price */}
            <div id="property-price-input">
              <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                <Home className="w-4 h-4 mr-1" />
                Property Price
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
                <input
                  type="text"
                  value={formatInputValue(propertyPrice.toString())}
                  onChange={(e) => setPropertyPrice(parseInputValue(e.target.value) || 0)}
                  className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg font-medium"
                  placeholder="628,040"
                  data-testid="property-price-input"
                />
              </div>
            </div>

            {/* Down Payment Percentage */}
            <div id="down-payment-input">
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                Down Payment
              </label>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <input
                    type="range"
                    min="5"
                    max="50"
                    step="5"
                    value={downPaymentPct}
                    onChange={(e) => setDownPaymentPct(Number(e.target.value))}
                    className="flex-1"
                    data-testid="down-payment-slider"
                  />
                  <div className="w-16 text-right">
                    <input
                      type="number"
                      value={downPaymentPct}
                      onChange={(e) => setDownPaymentPct(Number(e.target.value))}
                      className="w-full px-2 py-1 border border-gray-300 rounded text-sm text-center"
                      min="5"
                      max="50"
                      step="5"
                      data-testid="down-payment-input"
                    />
                    <span className="text-xs text-gray-500">%</span>
                  </div>
                </div>
                <div className="flex justify-between text-sm text-gray-600">
                  <span>Amount: {formatCurrency(downPaymentAmount)}</span>
                  <span>Loan: {formatCurrency(loanAmount)}</span>
                </div>
              </div>
            </div>

            {/* Interest Rate */}
            <div id="interest-rate-input-container">
              <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                <Percent className="w-4 h-4 mr-1" />
                Interest Rate
              </label>
              <div className="flex items-center space-x-2">
                <input
                  type="number"
                  id="interest-rate-input"
                  value={interestRate}
                  onChange={(e) => setInterestRate(Number(e.target.value))}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="7.5"
                  min="0"
                  max="30"
                  step="0.01"
                  data-testid="interest-rate-input"
                />
                <span className="text-gray-500">%</span>
              </div>
              <div className="mt-1 flex space-x-2">
                {[6.5, 7.0, 7.5, 8.0].map(rate => (
                  <button
                    key={rate}
                    onClick={() => setInterestRate(rate)}
                    className={`px-2 py-1 text-xs rounded ${
                      interestRate === rate
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {rate}%
                  </button>
                ))}
              </div>
            </div>

            {/* Loan Term */}
            <div id="loan-term-input">
              <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                <Calendar className="w-4 h-4 mr-1" />
                Loan Term
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[15, 20, 30].map(term => (
                  <button
                    key={term}
                    onClick={() => setLoanTerm(term)}
                    className={`px-3 py-2 text-sm rounded-lg font-medium transition ${
                      loanTerm === term
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                    data-testid={`term-${term}`}
                  >
                    {term} years
                  </button>
                ))}
              </div>
            </div>

            {error && (
              <div className="text-red-500 text-sm mt-2 p-2 bg-red-50 rounded">{error}</div>
            )}
          </div>

          {/* Results Section */}
          <div className="lg:col-span-2 space-y-6">
            {/* Monthly Payment Hero */}
            {result && (
              <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white">
                <div className="text-sm opacity-90 mb-1">Monthly Payment</div>
                <div className="text-4xl font-bold mb-4">
                  {formatCurrency(result.monthly_payment, 2)}
                </div>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="opacity-75">Total Interest</div>
                    <div className="font-semibold">{formatCurrency(result.total_interest)}</div>
                  </div>
                  <div>
                    <div className="opacity-75">Total Paid</div>
                    <div className="font-semibold">{formatCurrency(result.total_paid)}</div>
                  </div>
                  <div>
                    <div className="opacity-75">Interest Rate</div>
                    <div className="font-semibold">{interestRate.toFixed(2)}%</div>
                  </div>
                </div>
              </div>
            )}

            {/* Financing Scenarios */}
            <div id="financing-scenarios" className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {scenarios.map((scenario) => (
                <div
                  key={scenario.name}
                  className={`p-4 rounded-lg border-2 cursor-pointer transition ${
                    scenario.isCurrent
                      ? 'border-blue-400 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => applyScenario(scenario)}
                >
                  <h4 className="font-semibold mb-3">{scenario.name} Scenario</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Down Payment:</span>
                      <span className="font-medium">{scenario.downPaymentPct}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Interest Rate:</span>
                      <span className="font-medium">{scenario.interestRate.toFixed(2)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Loan Term:</span>
                      <span className="font-medium">{scenario.loanTerm} years</span>
                    </div>
                    <div className="flex justify-between border-t pt-2 mt-2">
                      <span>Monthly Payment:</span>
                      <span className="font-bold">
                        {scenario.monthlyPayment ? formatCurrency(scenario.monthlyPayment) : '-'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Cash Required:</span>
                      <span className="font-bold">
                        {scenario.cashRequired ? formatCurrency(scenario.cashRequired) : '-'}
                      </span>
                    </div>
                  </div>
                  {scenario.isCurrent && (
                    <div className="mt-2 text-xs text-blue-600 text-center font-medium">
                      Current Selection
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Amortization Schedule */}
            {amortizationSchedule.length > 0 && (
              <div className="bg-white rounded-lg border border-gray-200">
                <div className="p-4 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold flex items-center">
                      <FileText className="w-5 h-5 mr-2 text-gray-600" />
                      Amortization Schedule
                    </h3>
                    <button
                      onClick={() => setShowFullSchedule(!showFullSchedule)}
                      className="flex items-center text-sm text-blue-600 hover:text-blue-700"
                    >
                      {showFullSchedule ? 'Show First Year' : 'Show Full Schedule'}
                      {showFullSchedule ? <ChevronUp className="w-4 h-4 ml-1" /> : <ChevronDown className="w-4 h-4 ml-1" />}
                    </button>
                  </div>
                </div>

                <div className={`overflow-auto ${showFullSchedule ? 'max-h-96' : 'max-h-64'}`}>
                  <table className="w-full text-sm">
                    <thead className="sticky top-0 bg-gray-50">
                      <tr className="border-b">
                        <th className="text-left py-2 px-4">#</th>
                        <th className="text-left py-2 px-4">Date</th>
                        <th className="text-right py-2 px-4">Payment</th>
                        <th className="text-right py-2 px-4">Principal</th>
                        <th className="text-right py-2 px-4">Interest</th>
                        <th className="text-right py-2 px-4">Balance</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(showFullSchedule ? amortizationSchedule : amortizationSchedule.slice(0, 12)).map((row, index) => (
                        <tr key={row.payment_number} className={`border-b hover:bg-gray-50 ${
                          index % 12 === 11 ? 'bg-blue-50' : ''
                        }`}>
                          <td className="py-2 px-4">{row.payment_number}</td>
                          <td className="py-2 px-4">{row.payment_date}</td>
                          <td className="text-right py-2 px-4">{formatCurrency(row.payment_amount)}</td>
                          <td className="text-right py-2 px-4">{formatCurrency(row.principal_payment)}</td>
                          <td className="text-right py-2 px-4">{formatCurrency(row.interest_payment)}</td>
                          <td className="text-right py-2 px-4 font-medium">{formatCurrency(row.remaining_balance)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Schedule Summary */}
                <div className="p-4 bg-gray-50 border-t">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">First Year Principal:</span>
                      <span className="ml-2 font-semibold">
                        {formatCurrency(
                          amortizationSchedule
                            .slice(0, 12)
                            .reduce((sum, row) => sum + row.principal_payment, 0)
                        )}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">First Year Interest:</span>
                      <span className="ml-2 font-semibold">
                        {formatCurrency(
                          amortizationSchedule
                            .slice(0, 12)
                            .reduce((sum, row) => sum + row.interest_payment, 0)
                        )}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedMortgageCalculator;