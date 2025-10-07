import React, { useState } from 'react';
import {
  Calculator,
  TrendingUp,
  Home,
  RefreshCw,
  DollarSign,
  BarChart3,
  PieChart,
  FileText
} from 'lucide-react';
import EnhancedMortgageCalculator from '@/components/mortgage/EnhancedMortgageCalculator';
import AffordabilityCalculator from '@/components/mortgage/AffordabilityCalculator';
import RefinanceAnalyzer from '@/components/mortgage/RefinanceAnalyzer';
import PayoffTracker from '@/components/mortgage/PayoffTracker';
import RateComparison from '@/components/mortgage/RateComparison';
import AmortizationSchedule from '@/components/mortgage/AmortizationSchedule';

const MortgageTools: React.FC = () => {
  const [activeTab, setActiveTab] = useState('calculator');

  const tabs = [
    { id: 'calculator', label: 'Payment Calculator', icon: Calculator },
    { id: 'affordability', label: 'Affordability', icon: Home },
    { id: 'refinance', label: 'Refinance Analysis', icon: RefreshCw },
    { id: 'payoff', label: 'Payoff Tracker', icon: TrendingUp },
    { id: 'rates', label: 'Rate Comparison', icon: BarChart3 },
    { id: 'amortization', label: 'Amortization', icon: FileText },
  ];

  return (
    <div className="min-h-screen bg-gray-50" id="mortgage-tools-page">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Mortgage Tools</h1>
              <p className="mt-2 text-gray-600">
                Professional mortgage calculators and analysis tools
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <div className="text-sm text-gray-500">Powered by</div>
                <div className="text-lg font-semibold text-blue-600">ConcordBroker Analytics</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-1 overflow-x-auto" id="mortgage-tools-nav">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex items-center px-4 py-3 text-sm font-medium whitespace-nowrap
                    border-b-2 transition-colors duration-200
                    ${
                      activeTab === tab.id
                        ? 'text-blue-600 border-blue-600'
                        : 'text-gray-500 border-transparent hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                  data-testid={`tab-${tab.id}`}
                >
                  <Icon className="w-4 h-4 mr-2" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Content Area */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-fadeIn" id={`mortgage-tool-${activeTab}`}>
          {activeTab === 'calculator' && (
            <div>
              <div className="mb-6">
                <h2 className="text-2xl font-bold text-gray-800 mb-2">
                  Mortgage Payment Calculator
                </h2>
                <p className="text-gray-600">
                  Calculate your monthly mortgage payment, total interest, and payment breakdown
                </p>
              </div>
              <EnhancedMortgageCalculator />
            </div>
          )}

          {activeTab === 'affordability' && (
            <div>
              <div className="mb-6">
                <h2 className="text-2xl font-bold text-gray-800 mb-2">
                  Home Affordability Calculator
                </h2>
                <p className="text-gray-600">
                  Determine how much home you can afford based on your income and debts
                </p>
              </div>
              <AffordabilityCalculator />
            </div>
          )}

          {activeTab === 'refinance' && (
            <div>
              <div className="mb-6">
                <h2 className="text-2xl font-bold text-gray-800 mb-2">
                  Refinance Analysis
                </h2>
                <p className="text-gray-600">
                  Compare your current mortgage with refinancing options and calculate savings
                </p>
              </div>
              <RefinanceAnalyzer />
            </div>
          )}

          {activeTab === 'payoff' && (
            <div>
              <div className="mb-6">
                <h2 className="text-2xl font-bold text-gray-800 mb-2">
                  Loan Payoff Tracker
                </h2>
                <p className="text-gray-600">
                  Track your loan payoff progress and see how extra payments affect your timeline
                </p>
              </div>
              <PayoffTracker />
            </div>
          )}

          {activeTab === 'rates' && (
            <div>
              <div className="mb-6">
                <h2 className="text-2xl font-bold text-gray-800 mb-2">
                  Interest Rate Comparison
                </h2>
                <p className="text-gray-600">
                  Compare how different interest rates affect your monthly payment and total cost
                </p>
              </div>
              <RateComparison />
            </div>
          )}

          {activeTab === 'amortization' && (
            <div>
              <div className="mb-6">
                <h2 className="text-2xl font-bold text-gray-800 mb-2">
                  Amortization Schedule
                </h2>
                <p className="text-gray-600">
                  View a detailed breakdown of principal and interest for each payment
                </p>
              </div>
              <AmortizationSchedule />
            </div>
          )}
        </div>

        {/* Quick Stats */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-4 gap-4" id="mortgage-stats">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center">
              <DollarSign className="w-8 h-8 text-green-500 mr-3" />
              <div>
                <div className="text-sm text-gray-600">Current Avg Rate</div>
                <div className="text-xl font-bold">6.75%</div>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center">
              <PieChart className="w-8 h-8 text-blue-500 mr-3" />
              <div>
                <div className="text-sm text-gray-600">Median Home Price</div>
                <div className="text-xl font-bold">$425,000</div>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center">
              <BarChart3 className="w-8 h-8 text-purple-500 mr-3" />
              <div>
                <div className="text-sm text-gray-600">Avg Down Payment</div>
                <div className="text-xl font-bold">13%</div>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center">
              <Calculator className="w-8 h-8 text-orange-500 mr-3" />
              <div>
                <div className="text-sm text-gray-600">Calculations Today</div>
                <div className="text-xl font-bold">1,247</div>
              </div>
            </div>
          </div>
        </div>

        {/* Tips Section */}
        <div className="mt-12 bg-blue-50 rounded-lg p-6" id="mortgage-tips">
          <h3 className="text-lg font-bold text-blue-900 mb-4">Mortgage Tips</h3>
          <div className="grid md:grid-cols-2 gap-4 text-sm text-blue-800">
            <div>
              <strong>• 20% Down Payment:</strong> Avoid PMI by putting down at least 20%
            </div>
            <div>
              <strong>• Shop Around:</strong> Compare rates from multiple lenders
            </div>
            <div>
              <strong>• Credit Score:</strong> Improve your score for better rates
            </div>
            <div>
              <strong>• Extra Payments:</strong> Pay principal early to save thousands
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MortgageTools;