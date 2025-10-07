import React, { useState } from 'react';
import { RefreshCw, TrendingDown, AlertCircle } from 'lucide-react';
import { mortgageService } from '@/services/mortgageService';

const RefinanceAnalyzer: React.FC = () => {
  const [currentBalance, setCurrentBalance] = useState(350000);
  const [currentRate, setCurrentRate] = useState(7.5);
  const [monthsRemaining, setMonthsRemaining] = useState(300);
  const [newRate, setNewRate] = useState(6.5);
  const [newTerm, setNewTerm] = useState(30);
  const [closingCosts, setClosingCosts] = useState(5000);

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center mb-4">
        <RefreshCw className="w-6 h-6 mr-2 text-blue-600" />
        <h3 className="text-xl font-bold">Refinance Analysis Coming Soon</h3>
      </div>
      <p className="text-gray-600">Compare your current mortgage with refinancing options.</p>
    </div>
  );
};

export default RefinanceAnalyzer;