import React, { useState } from 'react';
import { BarChart3, TrendingUp, TrendingDown } from 'lucide-react';
import { mortgageService } from '@/services/mortgageService';

const RateComparison: React.FC = () => {
  const [loanAmount, setLoanAmount] = useState(400000);
  const [baseRate, setBaseRate] = useState(6.5);

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center mb-4">
        <BarChart3 className="w-6 h-6 mr-2 text-purple-600" />
        <h3 className="text-xl font-bold">Rate Comparison Tool Coming Soon</h3>
      </div>
      <p className="text-gray-600">Compare how different interest rates affect your payments.</p>
    </div>
  );
};

export default RateComparison;