import React, { useState, useEffect } from 'react';

interface PropertyScore {
  parcel_id: string;
  county: string;
  score_v1: number;
  reasons: {
    ownership: { type: string; score: number; explanation: string };
    hold_period: { category: string; score: number; explanation: string };
    tax_status: { status: string; score: number; explanation: string };
    equity_proxy: { category: string; score: number; explanation: string };
    total_score: number;
  };
  owner_name: string;
  phy_addr1?: string;
  phy_city?: string;
  assessed_value?: number;
  sale_price?: number;
  sale_date?: string;
}

const TopScores: React.FC = () => {
  const [properties, setProperties] = useState<PropertyScore[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTopProperties();
  }, []);

  const fetchTopProperties = async () => {
    try {
      setLoading(true);
      // Mock data for demonstration - replace with actual API call
      const mockData: PropertyScore[] = [
        {
          parcel_id: "12345",
          county: "COLUMBIA",
          score_v1: 85.0,
          reasons: {
            ownership: { type: "llc_corp", score: 25, explanation: "LLC ownership indicates investment potential" },
            hold_period: { category: "3-7", score: 30, explanation: "Optimal hold period for appreciation" },
            tax_status: { status: "current", score: 20, explanation: "Taxes are current" },
            equity_proxy: { category: "ratio_1.3-1.5", score: 20, explanation: "30-50% appreciation since purchase" },
            total_score: 85
          },
          owner_name: "PREMIUM INVESTMENTS LLC",
          phy_addr1: "548 SW HAWAII TER",
          phy_city: "FORT WHITE",
          assessed_value: 114605,
          sale_price: 89000,
          sale_date: "2020-03-15"
        },
        // Add more mock properties...
      ];

      // Simulate API delay
      setTimeout(() => {
        setProperties(mockData);
        setLoading(false);
      }, 1000);

    } catch (err) {
      setError('Failed to fetch property scores');
      setLoading(false);
    }
  };

  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'text-green-600 bg-green-50';
    if (score >= 60) return 'text-orange-600 bg-orange-50';
    return 'text-red-600 bg-red-50';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading top investment properties...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-6xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <p className="text-red-800">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Top 20 Investment Properties
          </h1>
          <p className="text-gray-600">
            Properties ranked by Stage 3 Scoring v1 - Simple, Transparent Investment Analysis
          </p>
        </div>

        <div className="space-y-6">
          {properties.map((property, index) => (
            <div key={`${property.parcel_id}-${property.county}`}
                 className="bg-white rounded-lg shadow-md p-6 border border-gray-200">

              {/* Header */}
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center space-x-4">
                  <span className="text-2xl font-bold text-gray-400">#{index + 1}</span>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {property.phy_addr1}, {property.phy_city}
                    </h3>
                    <p className="text-gray-600">
                      Parcel: {property.parcel_id} | {property.county} County
                    </p>
                  </div>
                </div>
                <div className={`px-4 py-2 rounded-lg font-bold text-2xl ${getScoreColor(property.score_v1)}`}>
                  {property.score_v1}
                </div>
              </div>

              {/* Property Details */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="text-sm font-medium text-gray-500">Owner</p>
                  <p className="text-gray-900">{property.owner_name}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="text-sm font-medium text-gray-500">Assessed Value</p>
                  <p className="text-gray-900 font-semibold">
                    ${property.assessed_value?.toLocaleString() || 'N/A'}
                  </p>
                </div>
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="text-sm font-medium text-gray-500">Last Sale</p>
                  <p className="text-gray-900">
                    {property.sale_price ? `$${property.sale_price.toLocaleString()}` : 'N/A'}
                    {property.sale_date && (
                      <span className="text-sm text-gray-500 ml-2">
                        ({new Date(property.sale_date).getFullYear()})
                      </span>
                    )}
                  </p>
                </div>
              </div>

              {/* Scoring Breakdown */}
              <div className="border-t pt-4">
                <h4 className="font-medium text-gray-900 mb-3">Score Breakdown</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">

                  <div className="bg-blue-50 p-3 rounded-lg">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm font-medium text-blue-700">Ownership</span>
                      <span className="font-semibold text-blue-900">
                        {property.reasons.ownership.score}/25
                      </span>
                    </div>
                    <p className="text-xs text-blue-600">
                      {property.reasons.ownership.explanation}
                    </p>
                  </div>

                  <div className="bg-green-50 p-3 rounded-lg">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm font-medium text-green-700">Hold Period</span>
                      <span className="font-semibold text-green-900">
                        {property.reasons.hold_period.score}/30
                      </span>
                    </div>
                    <p className="text-xs text-green-600">
                      {property.reasons.hold_period.explanation}
                    </p>
                  </div>

                  <div className="bg-orange-50 p-3 rounded-lg">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm font-medium text-orange-700">Tax Status</span>
                      <span className="font-semibold text-orange-900">
                        {property.reasons.tax_status.score}/20
                      </span>
                    </div>
                    <p className="text-xs text-orange-600">
                      {property.reasons.tax_status.explanation}
                    </p>
                  </div>

                  <div className="bg-purple-50 p-3 rounded-lg">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm font-medium text-purple-700">Equity Proxy</span>
                      <span className="font-semibold text-purple-900">
                        {property.reasons.equity_proxy.score}/25
                      </span>
                    </div>
                    <p className="text-xs text-purple-600">
                      {property.reasons.equity_proxy.explanation}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="mt-8 bg-white rounded-lg shadow-md p-6 border border-gray-200">
          <h3 className="font-semibold text-gray-900 mb-2">About Stage 3 Scoring v1</h3>
          <p className="text-gray-600 text-sm">
            This transparent scoring system evaluates investment potential based on four key factors:
            Ownership Type (25 pts), Hold Period (30 pts), Tax Status (20 pts), and Equity Proxy (25 pts).
            All scoring logic is explainable and deterministic, with weights defined in config/scoring_v1.yaml.
          </p>
        </div>
      </div>
    </div>
  );
};

export default TopScores;