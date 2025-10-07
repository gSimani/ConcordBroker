import React, { useState } from 'react';
import { FileText, Calendar, TrendingDown } from 'lucide-react';
import { mortgageService } from '@/services/mortgageService';

const AmortizationSchedule: React.FC = () => {
  const [loanAmount, setLoanAmount] = useState(400000);
  const [rate, setRate] = useState(6.5);
  const [years, setYears] = useState(30);

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center mb-4">
        <FileText className="w-6 h-6 mr-2 text-indigo-600" />
        <h3 className="text-xl font-bold">Amortization Schedule Coming Soon</h3>
      </div>
      <p className="text-gray-600">View detailed payment breakdown showing principal vs interest over time.</p>
    </div>
  );
};

export default AmortizationSchedule;