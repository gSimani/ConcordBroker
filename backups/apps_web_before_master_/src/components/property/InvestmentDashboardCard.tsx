import React from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  TrendingUp,
  TrendingDown,
  Target,
  Percent,
  DollarSign,
  Calculator,
  BarChart3,
  PieChart,
  AlertTriangle,
  CheckCircle,
  Star,
  Eye,
  Zap,
  Award,
  Activity,
  Home,
  Building,
  MapPin
} from 'lucide-react';
import { motion } from 'framer-motion';
import { useCompletePropertyData } from '@/hooks/useCompletePropertyData';

interface InvestmentDashboardCardProps {
  property: {
    parcel_id: string;
    phy_addr1?: string;
    phy_city?: string;
    owner_name?: string;
    market_value?: number;
    just_value?: number;
    sale_prc1?: number;
    year_built?: number;
    building_sqft?: number;
    property_use?: string;
    homestead?: boolean;
  };
  variant?: 'detailed' | 'compact';
  onClick?: () => void;
  showFullAnalysis?: boolean;
}

export function InvestmentDashboardCard({
  property,
  variant = 'detailed',
  onClick,
  showFullAnalysis = true
}: InvestmentDashboardCardProps) {
  // Get complete property data for advanced investment analysis
  const propertyData = useCompletePropertyData(property.parcel_id);

  // Format currency
  const formatCurrency = (value?: number) => {
    if (!value || value === 0) return 'N/A';
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `$${Math.round(value / 1000)}K`;
    }
    return `$${Math.round(value).toLocaleString()}`;
  };

  // Get investment score from API or calculate locally
  const getInvestmentScore = () => {
    if (propertyData.investmentAnalysis?.investment_score?.overall_score) {
      return propertyData.investmentAnalysis.investment_score.overall_score;
    }

    // Local calculation
    let score = 50;
    const marketValue = property.market_value || property.just_value || 0;
    const yearBuilt = property.year_built || 1950;
    const propertyAge = new Date().getFullYear() - yearBuilt;

    // Age scoring
    if (propertyAge < 20) score += 15;
    else if (propertyAge < 40) score += 5;
    else if (propertyAge > 60) score -= 10;

    // Value range scoring
    if (marketValue > 0 && marketValue < 300000) score += 10;
    else if (marketValue > 800000) score -= 5;

    // Investment property bonus
    if (!property.homestead) score += 15;

    // Size bonus
    if (property.building_sqft && property.building_sqft > 1200) score += 5;

    // Property type scoring
    const propertyUse = property.property_use?.toString() || '';
    if (['1', '2', '3'].includes(propertyUse)) score += 5; // Residential

    return Math.max(0, Math.min(100, Math.round(score)));
  };

  // Calculate key investment metrics
  const calculateMetrics = () => {
    const marketValue = property.market_value || property.just_value || 0;
    const lastSalePrice = property.sale_prc1 || 0;
    const buildingSqft = property.building_sqft || 0;

    // Estimated monthly rent (rough calculation)
    const estimatedRent = marketValue * 0.008; // 0.8% of value monthly

    // Cap rate estimate (very rough)
    const annualRent = estimatedRent * 12;
    const expenses = annualRent * 0.35; // 35% expense ratio
    const noi = annualRent - expenses;
    const capRate = marketValue > 0 ? (noi / marketValue) * 100 : 0;

    // Price per sqft
    const pricePerSqft = buildingSqft > 0 && marketValue > 0 ? marketValue / buildingSqft : 0;

    // Appreciation potential
    const appreciationPotential = lastSalePrice > 0 && marketValue > lastSalePrice ?
      ((marketValue - lastSalePrice) / lastSalePrice) * 100 : 0;

    return {
      estimatedRent: Math.round(estimatedRent),
      capRate: Number(capRate.toFixed(1)),
      pricePerSqft: Math.round(pricePerSqft),
      appreciationPotential: Number(appreciationPotential.toFixed(1)),
      noi: Math.round(noi)
    };
  };

  // Get investment opportunities from API or generate locally
  const getOpportunities = () => {
    if (propertyData.investmentAnalysis?.opportunities?.primary_opportunities) {
      return propertyData.investmentAnalysis.opportunities.primary_opportunities.slice(0, 3);
    }

    // Local opportunity detection
    const opportunities = [];
    const metrics = calculateMetrics();

    if (!property.homestead) opportunities.push('Non-homestead investment property');
    if (metrics.capRate > 6) opportunities.push(`Strong ${metrics.capRate}% cap rate potential`);
    if (metrics.appreciationPotential > 20) opportunities.push(`${metrics.appreciationPotential}% appreciation since last sale`);
    if (property.year_built && (new Date().getFullYear() - property.year_built) > 25 &&
        (new Date().getFullYear() - property.year_built) < 60) {
      opportunities.push('Renovation and modernization potential');
    }
    if (metrics.pricePerSqft < 200) opportunities.push('Below-market price per square foot');

    return opportunities.slice(0, 3);
  };

  // Get risk factors
  const getRiskFactors = () => {
    if (propertyData.investmentAnalysis?.risk_assessment?.risk_factors) {
      return propertyData.investmentAnalysis.risk_assessment.risk_factors.slice(0, 2);
    }

    const risks = [];
    const yearBuilt = property.year_built || 1950;
    const propertyAge = new Date().getFullYear() - yearBuilt;

    if (propertyAge > 50) risks.push('Older property may require significant maintenance');
    if (property.market_value && property.market_value > 500000) {
      risks.push('Higher price point may limit rental demand');
    }

    return risks.slice(0, 2);
  };

  const investmentScore = getInvestmentScore();
  const metrics = calculateMetrics();
  const opportunities = getOpportunities();
  const riskFactors = getRiskFactors();

  // Score styling
  const getScoreStyle = (score: number) => {
    if (score >= 80) return { color: 'green', bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' };
    if (score >= 70) return { color: 'blue', bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' };
    if (score >= 60) return { color: 'yellow', bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200' };
    if (score >= 40) return { color: 'orange', bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' };
    return { color: 'red', bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' };
  };

  const scoreStyle = getScoreStyle(investmentScore);

  // Compact variant
  if (variant === 'compact') {
    return (
      <motion.div
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={onClick}
        className="cursor-pointer"
      >
        <Card className="p-4 border-l-4 border-l-blue-500 hover:shadow-lg transition-all duration-300">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className={`w-8 h-8 ${scoreStyle.bg} rounded-lg flex items-center justify-center`}>
                <Target className={`w-4 h-4 ${scoreStyle.text}`} />
              </div>
              <div>
                <p className="font-semibold text-gray-900 text-sm">
                  {property.phy_addr1 || 'No Address'}
                </p>
                <p className="text-xs text-gray-500">{property.owner_name}</p>
              </div>
            </div>
            <div className="text-right">
              <div className={`text-2xl font-bold ${scoreStyle.text}`}>{investmentScore}</div>
              <div className="text-xs text-gray-500">Score</div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <span className="text-gray-500">Value:</span>
              <span className="font-semibold ml-1">
                {formatCurrency(property.market_value || property.just_value)}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Est. Rent:</span>
              <span className="font-semibold ml-1">{formatCurrency(metrics.estimatedRent)}/mo</span>
            </div>
            <div>
              <span className="text-gray-500">Cap Rate:</span>
              <span className="font-semibold ml-1">{metrics.capRate}%</span>
            </div>
            <div>
              <span className="text-gray-500">$/SqFt:</span>
              <span className="font-semibold ml-1">${metrics.pricePerSqft}</span>
            </div>
          </div>
        </Card>
      </motion.div>
    );
  }

  // Detailed variant
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="overflow-hidden hover:shadow-xl transition-all duration-500 cursor-pointer" onClick={onClick}>
        {/* Header with gradient */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mt-16 -mr-16"></div>
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                  <Target className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="font-bold text-lg">Investment Analysis</h3>
                  <p className="text-blue-100 text-sm">{property.phy_city}, FL</p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold">{investmentScore}</div>
                <div className="text-sm text-blue-100">Investment Score</div>
              </div>
            </div>

            <div className="bg-white/20 rounded-lg p-3">
              <p className="font-semibold truncate">{property.phy_addr1 || 'No Street Address'}</p>
              <p className="text-sm text-blue-100">{property.owner_name || 'Unknown Owner'}</p>
            </div>
          </div>
        </div>

        {/* Investment Metrics */}
        <div className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            {/* Market Value */}
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <DollarSign className="w-5 h-5 text-gray-600 mx-auto mb-1" />
              <p className="text-xs font-medium text-gray-600 mb-1">Market Value</p>
              <p className="text-lg font-bold text-gray-900">
                {formatCurrency(property.market_value || property.just_value)}
              </p>
            </div>

            {/* Estimated Rent */}
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <Home className="w-5 h-5 text-green-600 mx-auto mb-1" />
              <p className="text-xs font-medium text-green-600 mb-1">Est. Monthly Rent</p>
              <p className="text-lg font-bold text-green-800">
                {formatCurrency(metrics.estimatedRent)}
              </p>
            </div>

            {/* Cap Rate */}
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <Percent className="w-5 h-5 text-blue-600 mx-auto mb-1" />
              <p className="text-xs font-medium text-blue-600 mb-1">Est. Cap Rate</p>
              <p className="text-lg font-bold text-blue-800">{metrics.capRate}%</p>
            </div>

            {/* Price per SqFt */}
            <div className="text-center p-3 bg-purple-50 rounded-lg">
              <Calculator className="w-5 h-5 text-purple-600 mx-auto mb-1" />
              <p className="text-xs font-medium text-purple-600 mb-1">Price/SqFt</p>
              <p className="text-lg font-bold text-purple-800">${metrics.pricePerSqft}</p>
            </div>
          </div>

          {/* Investment Score Breakdown */}
          <div className={`p-4 rounded-lg ${scoreStyle.bg} ${scoreStyle.border} border mb-6`}>
            <div className="flex items-center justify-between mb-3">
              <h4 className={`font-semibold ${scoreStyle.text} flex items-center gap-2`}>
                <Award className="w-4 h-4" />
                Investment Rating
              </h4>
              <Badge className={`${scoreStyle.bg} ${scoreStyle.text} border-0`}>
                {investmentScore >= 80 ? 'Excellent' :
                 investmentScore >= 70 ? 'Very Good' :
                 investmentScore >= 60 ? 'Good' :
                 investmentScore >= 40 ? 'Fair' : 'Poor'}
              </Badge>
            </div>
            <div className={`w-full bg-gray-200 rounded-full h-2`}>
              <div
                className={`h-2 rounded-full transition-all duration-1000 ${
                  scoreStyle.color === 'green' ? 'bg-green-500' :
                  scoreStyle.color === 'blue' ? 'bg-blue-500' :
                  scoreStyle.color === 'yellow' ? 'bg-yellow-500' :
                  scoreStyle.color === 'orange' ? 'bg-orange-500' : 'bg-red-500'
                }`}
                style={{ width: `${investmentScore}%` }}
              ></div>
            </div>
          </div>

          {showFullAnalysis && (
            <>
              {/* Opportunities */}
              {opportunities.length > 0 && (
                <div className="mb-6">
                  <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    Investment Opportunities
                  </h4>
                  <div className="space-y-2">
                    {opportunities.map((opportunity, index) => (
                      <div key={index} className="flex items-center gap-2 text-sm text-green-700 bg-green-50 px-3 py-2 rounded-lg">
                        <Zap className="w-3 h-3" />
                        <span>{opportunity}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Risk Factors */}
              {riskFactors.length > 0 && (
                <div className="mb-6">
                  <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-orange-600" />
                    Risk Considerations
                  </h4>
                  <div className="space-y-2">
                    {riskFactors.map((risk, index) => (
                      <div key={index} className="flex items-center gap-2 text-sm text-orange-700 bg-orange-50 px-3 py-2 rounded-lg">
                        <AlertTriangle className="w-3 h-3" />
                        <span>{risk}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Actions */}
          <div className="flex items-center justify-between pt-4 border-t border-gray-200">
            <div className="text-xs text-gray-500 font-mono">
              Parcel: {property.parcel_id}
            </div>
            <div className="flex items-center gap-2">
              <Button size="sm" variant="outline">
                <Star className="w-3 h-3 mr-2" />
                Watch
              </Button>
              <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
                <Eye className="w-3 h-3 mr-2" />
                Analyze
              </Button>
            </div>
          </div>

          {/* Loading overlay */}
          {propertyData.isLoading && (
            <div className="absolute inset-0 bg-white/80 flex items-center justify-center">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                <p className="text-sm text-gray-600">Loading analysis...</p>
              </div>
            </div>
          )}
        </div>
      </Card>
    </motion.div>
  );
}

export default InvestmentDashboardCard;