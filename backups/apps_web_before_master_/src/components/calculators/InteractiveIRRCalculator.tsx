import React, { useState, useEffect } from 'react';
import { Calculator, TrendingUp, DollarSign, Calendar, Percent } from 'lucide-react';

interface IRRCalculatorProps {
  initialInvestment?: number;
  monthlyRent?: number;
  propertyValue?: number;
  className?: string;
}

const InteractiveIRRCalculator: React.FC<IRRCalculatorProps> = ({
  initialInvestment: defaultInitial = 0,
  monthlyRent: defaultRent = 0,
  propertyValue: defaultValue = 0,
  className = ''
}) => {
  // State for adjustable variables
  const [holdingPeriod, setHoldingPeriod] = useState(10); // years
  const [appreciationRate, setAppreciationRate] = useState(3.5); // %
  const [rentGrowthRate, setRentGrowthRate] = useState(2.5); // %
  const [discountRate, setDiscountRate] = useState(8); // % for NPV
  const [vacancyRate, setVacancyRate] = useState(5); // %
  const [maintenanceRate, setMaintenanceRate] = useState(10); // % of rent
  const [propertyTaxRate, setPropertyTaxRate] = useState(1.2); // %
  const [insuranceAnnual, setInsuranceAnnual] = useState(1200); // $
  const [initialInvestment, setInitialInvestment] = useState(defaultInitial);
  const [monthlyRent, setMonthlyRent] = useState(defaultRent);
  const [exitCapRate, setExitCapRate] = useState(6); // %

  // Calculated values
  const [irr, setIrr] = useState(0);
  const [npv, setNpv] = useState(0);
  const [cashFlows, setCashFlows] = useState<number[]>([]);
  const [totalReturn, setTotalReturn] = useState(0);

  // Calculate annual net operating income
  const calculateNOI = (year: number) => {
    const annualRent = monthlyRent * 12 * Math.pow(1 + rentGrowthRate / 100, year);
    const effectiveRent = annualRent * (1 - vacancyRate / 100);
    const maintenance = effectiveRent * (maintenanceRate / 100);
    const propertyTax = (defaultValue || initialInvestment) * (propertyTaxRate / 100);

    return effectiveRent - maintenance - propertyTax - insuranceAnnual;
  };

  // Calculate property value at exit
  const calculateExitValue = () => {
    const futureValue = (defaultValue || initialInvestment) *
      Math.pow(1 + appreciationRate / 100, holdingPeriod);

    // Alternative: Use exit cap rate method
    const finalYearNOI = calculateNOI(holdingPeriod - 1);
    const capRateValue = finalYearNOI / (exitCapRate / 100);

    // Use the higher of the two methods
    return Math.max(futureValue, capRateValue);
  };

  // Calculate IRR using Newton's method
  const calculateIRR = (cashflows: number[]) => {
    let rate = 0.1; // Initial guess 10%
    const maxIterations = 100;
    const tolerance = 0.0001;

    for (let i = 0; i < maxIterations; i++) {
      let npv = 0;
      let dnpv = 0;

      for (let j = 0; j < cashflows.length; j++) {
        npv += cashflows[j] / Math.pow(1 + rate, j);
        dnpv -= j * cashflows[j] / Math.pow(1 + rate, j + 1);
      }

      const newRate = rate - npv / dnpv;

      if (Math.abs(newRate - rate) < tolerance) {
        return newRate * 100;
      }

      rate = newRate;
    }

    return rate * 100;
  };

  // Calculate NPV
  const calculateNPV = (cashflows: number[], discount: number) => {
    return cashflows.reduce((acc, cf, i) => {
      return acc + cf / Math.pow(1 + discount / 100, i);
    }, 0);
  };

  // Update calculations when inputs change
  useEffect(() => {
    if (initialInvestment <= 0) return;

    // Generate cash flows
    const flows = [-initialInvestment]; // Year 0: Initial investment

    // Years 1 to n-1: Annual NOI
    for (let year = 1; year < holdingPeriod; year++) {
      flows.push(calculateNOI(year - 1));
    }

    // Final year: NOI + Sale proceeds
    const exitValue = calculateExitValue();
    const finalYearNOI = calculateNOI(holdingPeriod - 1);
    flows.push(finalYearNOI + exitValue);

    setCashFlows(flows);

    // Calculate IRR
    const irrValue = calculateIRR(flows);
    setIrr(irrValue);

    // Calculate NPV
    const npvValue = calculateNPV(flows, discountRate);
    setNpv(npvValue);

    // Calculate total return
    const totalCashFlow = flows.slice(1).reduce((a, b) => a + b, 0);
    const totalReturnValue = ((totalCashFlow - initialInvestment) / initialInvestment) * 100;
    setTotalReturn(totalReturnValue);

  }, [
    holdingPeriod, appreciationRate, rentGrowthRate, discountRate,
    vacancyRate, maintenanceRate, propertyTaxRate, insuranceAnnual,
    initialInvestment, monthlyRent, exitCapRate
  ]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value.toFixed(2)}%`;
  };

  return (
    <div id="interactive-irr-calculator-1" className={`bg-white rounded-lg shadow-lg p-6 ${className}`}>
      <div id="irr-header-1" className="flex items-center mb-6">
        <Calculator className="w-6 h-6 mr-2 text-blue-600" />
        <h2 className="text-2xl font-bold text-gray-800">Advanced IRR/NPV Calculator</h2>
      </div>

      {/* Results Display */}
      <div id="irr-results-grid-1" className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div id="irr-result-1" className="bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Internal Rate of Return</p>
              <p className="text-2xl font-bold text-blue-700">{formatPercent(irr)}</p>
            </div>
            <TrendingUp className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div id="npv-result-1" className="bg-gradient-to-r from-green-50 to-green-100 p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Net Present Value</p>
              <p className="text-2xl font-bold text-green-700">{formatCurrency(npv)}</p>
            </div>
            <DollarSign className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div id="total-return-result-1" className="bg-gradient-to-r from-purple-50 to-purple-100 p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Return</p>
              <p className="text-2xl font-bold text-purple-700">{formatPercent(totalReturn)}</p>
            </div>
            <Percent className="w-8 h-8 text-purple-500" />
          </div>
        </div>
      </div>

      {/* Input Controls */}
      <div id="irr-inputs-container-1" className="space-y-6">
        <div id="irr-basic-inputs-1" className="border-t pt-4">
          <h3 className="text-lg font-semibold mb-4 text-gray-700">Investment Parameters</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div id="initial-investment-input-1">
              <label className="block text-sm font-medium text-gray-600 mb-1">
                Initial Investment
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
                <input
                  type="number"
                  value={initialInvestment}
                  onChange={(e) => setInitialInvestment(Number(e.target.value))}
                  className="w-full pl-8 pr-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div id="monthly-rent-input-1">
              <label className="block text-sm font-medium text-gray-600 mb-1">
                Monthly Rent
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
                <input
                  type="number"
                  value={monthlyRent}
                  onChange={(e) => setMonthlyRent(Number(e.target.value))}
                  className="w-full pl-8 pr-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div id="holding-period-input-1">
              <label className="block text-sm font-medium text-gray-600 mb-1">
                Holding Period (Years)
              </label>
              <input
                type="number"
                value={holdingPeriod}
                onChange={(e) => setHoldingPeriod(Number(e.target.value))}
                min="1"
                max="30"
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div id="discount-rate-input-1">
              <label className="block text-sm font-medium text-gray-600 mb-1">
                Discount Rate (% for NPV)
              </label>
              <input
                type="number"
                value={discountRate}
                onChange={(e) => setDiscountRate(Number(e.target.value))}
                step="0.1"
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        <div id="irr-growth-inputs-1" className="border-t pt-4">
          <h3 className="text-lg font-semibold mb-4 text-gray-700">Growth Assumptions</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div id="appreciation-rate-input-1">
              <label className="block text-sm font-medium text-gray-600 mb-1">
                Property Appreciation (%/year)
              </label>
              <input
                type="number"
                value={appreciationRate}
                onChange={(e) => setAppreciationRate(Number(e.target.value))}
                step="0.1"
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div id="rent-growth-input-1">
              <label className="block text-sm font-medium text-gray-600 mb-1">
                Rent Growth (%/year)
              </label>
              <input
                type="number"
                value={rentGrowthRate}
                onChange={(e) => setRentGrowthRate(Number(e.target.value))}
                step="0.1"
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div id="exit-cap-rate-input-1">
              <label className="block text-sm font-medium text-gray-600 mb-1">
                Exit Cap Rate (%)
              </label>
              <input
                type="number"
                value={exitCapRate}
                onChange={(e) => setExitCapRate(Number(e.target.value))}
                step="0.1"
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        <div id="irr-expense-inputs-1" className="border-t pt-4">
          <h3 className="text-lg font-semibold mb-4 text-gray-700">Operating Expenses</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div id="vacancy-rate-input-1">
              <label className="block text-sm font-medium text-gray-600 mb-1">
                Vacancy Rate (%)
              </label>
              <input
                type="number"
                value={vacancyRate}
                onChange={(e) => setVacancyRate(Number(e.target.value))}
                step="0.1"
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div id="maintenance-rate-input-1">
              <label className="block text-sm font-medium text-gray-600 mb-1">
                Maintenance (% of rent)
              </label>
              <input
                type="number"
                value={maintenanceRate}
                onChange={(e) => setMaintenanceRate(Number(e.target.value))}
                step="0.1"
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div id="property-tax-rate-input-1">
              <label className="block text-sm font-medium text-gray-600 mb-1">
                Property Tax Rate (%)
              </label>
              <input
                type="number"
                value={propertyTaxRate}
                onChange={(e) => setPropertyTaxRate(Number(e.target.value))}
                step="0.1"
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div id="insurance-input-1">
              <label className="block text-sm font-medium text-gray-600 mb-1">
                Annual Insurance
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
                <input
                  type="number"
                  value={insuranceAnnual}
                  onChange={(e) => setInsuranceAnnual(Number(e.target.value))}
                  className="w-full pl-8 pr-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Cash Flow Breakdown */}
        <div id="irr-cashflow-breakdown-1" className="border-t pt-4">
          <h3 className="text-lg font-semibold mb-4 text-gray-700">Projected Cash Flows</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-3 py-2 text-left">Year</th>
                  <th className="px-3 py-2 text-right">Cash Flow</th>
                  <th className="px-3 py-2 text-right">Present Value</th>
                </tr>
              </thead>
              <tbody>
                {cashFlows.map((cf, i) => (
                  <tr key={i} className={i === 0 ? 'font-semibold' : ''}>
                    <td className="px-3 py-2">{i === 0 ? 'Initial' : i}</td>
                    <td className="px-3 py-2 text-right">{formatCurrency(cf)}</td>
                    <td className="px-3 py-2 text-right">
                      {formatCurrency(cf / Math.pow(1 + discountRate / 100, i))}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InteractiveIRRCalculator;