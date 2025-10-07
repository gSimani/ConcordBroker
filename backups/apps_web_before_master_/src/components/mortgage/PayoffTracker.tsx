import React, { useState } from 'react';
import { TrendingUp, Calendar, DollarSign } from 'lucide-react';
import { mortgageService } from '@/services/mortgageService';

const PayoffTracker: React.FC = () => {
  const [originalAmount, setOriginalAmount] = useState(400000);
  const [rate, setRate] = useState(6.5);
  const [monthsElapsed, setMonthsElapsed] = useState(60);

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center mb-4">
        <TrendingUp className="w-6 h-6 mr-2 text-green-600" />
        <h3 className="text-xl font-bold">Loan Payoff Tracker Coming Soon</h3>
      </div>
      <p className="text-gray-600">Track your loan payoff progress and see the impact of extra payments.</p>
    </div>
  );
};

export default PayoffTracker;