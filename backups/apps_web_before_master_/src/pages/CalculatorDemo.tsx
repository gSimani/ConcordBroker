import React from 'react';
import { InteractiveIRRCalculator } from '../components/calculators';

const CalculatorDemo: React.FC = () => {
  // Example property data (can be passed from property details)
  const exampleProperty = {
    initialInvestment: 133370,
    monthlyRent: 1500,
    propertyValue: 150000
  };

  return (
    <div id="calculator-demo-page-1" className="min-h-screen bg-gray-50 py-8">
      <div id="calculator-demo-container-1" className="container mx-auto px-4 max-w-6xl">
        <div id="calculator-demo-header-1" className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Investment Analysis Calculator
          </h1>
          <p className="text-gray-600">
            Analyze your real estate investment with customizable parameters for IRR, NPV, and total return calculations.
          </p>
        </div>

        {/* Main Calculator */}
        <InteractiveIRRCalculator
          initialInvestment={exampleProperty.initialInvestment}
          monthlyRent={exampleProperty.monthlyRent}
          propertyValue={exampleProperty.propertyValue}
          className="mb-8"
        />

        {/* Additional Information */}
        <div id="calculator-info-section-1" className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
          <div id="calculator-glossary-1" className="bg-white rounded-lg shadow p-6">
            <h3 className="text-xl font-semibold mb-4 text-gray-800">Key Terms</h3>
            <dl className="space-y-3">
              <div id="irr-definition-1">
                <dt className="font-semibold text-gray-700">IRR (Internal Rate of Return)</dt>
                <dd className="text-sm text-gray-600">
                  The discount rate at which the NPV of all cash flows equals zero. Higher IRR indicates better investment performance.
                </dd>
              </div>
              <div id="npv-definition-1">
                <dt className="font-semibold text-gray-700">NPV (Net Present Value)</dt>
                <dd className="text-sm text-gray-600">
                  The present value of all future cash flows minus initial investment. Positive NPV indicates a profitable investment.
                </dd>
              </div>
              <div id="cap-rate-definition-1">
                <dt className="font-semibold text-gray-700">Cap Rate (Capitalization Rate)</dt>
                <dd className="text-sm text-gray-600">
                  The ratio of Net Operating Income to property value, used to estimate potential return.
                </dd>
              </div>
              <div id="discount-rate-definition-1">
                <dt className="font-semibold text-gray-700">Discount Rate</dt>
                <dd className="text-sm text-gray-600">
                  The rate used to discount future cash flows to present value, reflecting risk and opportunity cost.
                </dd>
              </div>
            </dl>
          </div>

          <div id="calculator-tips-1" className="bg-white rounded-lg shadow p-6">
            <h3 className="text-xl font-semibold mb-4 text-gray-800">Usage Tips</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li id="tip-1" className="flex items-start">
                <span className="text-blue-500 mr-2">•</span>
                <span>Adjust the holding period to see how investment duration affects returns</span>
              </li>
              <li id="tip-2" className="flex items-start">
                <span className="text-blue-500 mr-2">•</span>
                <span>Use local market data for appreciation and rent growth rates</span>
              </li>
              <li id="tip-3" className="flex items-start">
                <span className="text-blue-500 mr-2">•</span>
                <span>Include all costs: taxes, insurance, maintenance, and vacancy</span>
              </li>
              <li id="tip-4" className="flex items-start">
                <span className="text-blue-500 mr-2">•</span>
                <span>Compare IRR to your required rate of return (hurdle rate)</span>
              </li>
              <li id="tip-5" className="flex items-start">
                <span className="text-blue-500 mr-2">•</span>
                <span>Consider multiple scenarios with conservative and optimistic assumptions</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Default Values Reference */}
        <div id="calculator-defaults-1" className="bg-blue-50 border border-blue-200 rounded-lg p-6 mt-8">
          <h3 className="text-lg font-semibold mb-3 text-blue-900">Default Assumptions</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div id="default-1">
              <span className="text-gray-600">Holding Period:</span>
              <span className="font-semibold ml-2">10 years</span>
            </div>
            <div id="default-2">
              <span className="text-gray-600">Appreciation:</span>
              <span className="font-semibold ml-2">3.5% annually</span>
            </div>
            <div id="default-3">
              <span className="text-gray-600">Rent Growth:</span>
              <span className="font-semibold ml-2">2.5% annually</span>
            </div>
            <div id="default-4">
              <span className="text-gray-600">Discount Rate:</span>
              <span className="font-semibold ml-2">8%</span>
            </div>
            <div id="default-5">
              <span className="text-gray-600">Vacancy Rate:</span>
              <span className="font-semibold ml-2">5%</span>
            </div>
            <div id="default-6">
              <span className="text-gray-600">Maintenance:</span>
              <span className="font-semibold ml-2">10% of rent</span>
            </div>
            <div id="default-7">
              <span className="text-gray-600">Property Tax:</span>
              <span className="font-semibold ml-2">1.2%</span>
            </div>
            <div id="default-8">
              <span className="text-gray-600">Exit Cap Rate:</span>
              <span className="font-semibold ml-2">6%</span>
            </div>
          </div>
          <p className="text-xs text-gray-600 mt-3">
            These defaults represent typical market conditions. Adjust based on your specific property and local market.
          </p>
        </div>
      </div>
    </div>
  );
};

export default CalculatorDemo;