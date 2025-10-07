import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  TrendingUp, TrendingDown, DollarSign, Calculator, PieChart,
  BarChart3, Activity, Target, AlertTriangle, CheckCircle2,
  MapPin, Building, Calendar, Star, Brain, Lightbulb,
  ArrowUpRight, ArrowDownRight, Minus, Info
} from 'lucide-react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart as RechartsPieChart, Cell,
         XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface EnhancedAnalysisTabProps {
  data: any;
}

export function EnhancedAnalysisTab({ data }: EnhancedAnalysisTabProps) {
  const [activeAnalysis, setActiveAnalysis] = useState('investment');

  // Extract comprehensive data
  const {
    investmentScore = 0,
    marketAnalysis = {},
    calculations = {},
    opportunities = [],
    riskFactors = [],
    salesTrends = [],
    similar_properties = [],
    neighborhood_stats = null,
    growth_projections = []
  } = data || {};

  const formatCurrency = (value: number | undefined) => {
    if (!value) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatPercentage = (value: number | undefined) => {
    if (value === undefined || value === null) return 'N/A';
    return `${value.toFixed(1)}%`;
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 60) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp className="w-4 h-4 text-green-600" />;
      case 'down': return <TrendingDown className="w-4 h-4 text-red-600" />;
      default: return <Minus className="w-4 h-4 text-gray-600" />;
    }
  };

  // Prepare chart data
  const investmentMetricsData = [
    {
      name: 'Investment Score',
      value: investmentScore,
      max: 100,
      color: investmentScore >= 80 ? '#10b981' : investmentScore >= 60 ? '#f59e0b' : '#ef4444'
    },
    {
      name: 'Value Percentile',
      value: marketAnalysis.valuePercentile || 50,
      max: 100,
      color: '#6366f1'
    },
    {
      name: 'Data Quality',
      value: data?.dataQuality?.completeness || 0,
      max: 100,
      color: '#8b5cf6'
    }
  ];

  const salesTrendData = salesTrends.map((trend: any, index: number) => ({
    period: `Sale ${index + 1}`,
    price: trend.to_price,
    change: trend.percent_change,
    date: new Date(trend.to_date).getFullYear()
  }));

  const marketComparisonData = similar_properties.slice(0, 5).map((prop: any, index: number) => ({
    property: `Comp ${index + 1}`,
    value: parseFloat(prop.just_value || '0'),
    pricePerSqft: prop.total_living_area ? parseFloat(prop.just_value || '0') / prop.total_living_area : 0,
    address: prop.phy_addr1?.substring(0, 20) + '...'
  }));

  const projectionData = growth_projections.map((proj: any) => ({
    year: proj.year,
    growth: proj.projected_growth,
    projectedValue: marketAnalysis.countyMedianValue * Math.pow(1 + proj.projected_growth/100, proj.year - 2024)
  }));

  return (
    <div className="space-y-6">
      {/* Analysis Overview Header */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className={`border-l-4 ${getScoreColor(investmentScore)}`}>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center text-lg">
              <Target className="w-5 h-5 mr-2" />
              Investment Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between mb-2">
              <span className="text-3xl font-bold">{investmentScore}</span>
              <span className="text-sm text-gray-500">/100</span>
            </div>
            <Progress value={investmentScore} className="mb-2" />
            <p className="text-sm text-gray-600">
              {investmentScore >= 80 ? 'Excellent' : investmentScore >= 60 ? 'Good' : 'Fair'} investment potential
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center text-lg">
              <BarChart3 className="w-5 h-5 mr-2" />
              Market Position
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm">Value Percentile:</span>
                <span className="font-medium">{marketAnalysis.valuePercentile?.toFixed(0) || 'N/A'}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Market Trend:</span>
                <div className="flex items-center">
                  {getTrendIcon(marketAnalysis.marketTrend)}
                  <span className="ml-1 font-medium capitalize">{marketAnalysis.marketTrend || 'stable'}</span>
                </div>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Appreciation:</span>
                <span className="font-medium">{formatPercentage(marketAnalysis.appreciation)}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center text-lg">
              <Calculator className="w-5 h-5 mr-2" />
              Financial Metrics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm">Cap Rate:</span>
                <span className="font-medium">{formatPercentage(calculations.capRate)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Cash Flow:</span>
                <span className="font-medium">{formatCurrency(calculations.cashFlow)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">ROI:</span>
                <span className="font-medium">{formatPercentage(calculations.roi)}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Analysis Tabs */}
      <Tabs value={activeAnalysis} onValueChange={setActiveAnalysis}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="investment">Investment</TabsTrigger>
          <TabsTrigger value="market">Market</TabsTrigger>
          <TabsTrigger value="financial">Financial</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
          <TabsTrigger value="ai-insights">AI Insights</TabsTrigger>
        </TabsList>

        {/* Investment Analysis */}
        <TabsContent value="investment" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Investment Score Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <PieChart className="w-5 h-5 mr-2" />
                  Investment Score Breakdown
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={investmentMetricsData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis domain={[0, 100]} />
                    <Tooltip />
                    <Bar dataKey="value" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Opportunities & Risks */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Lightbulb className="w-5 h-5 mr-2" />
                  Opportunities & Risks
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Opportunities */}
                <div>
                  <h4 className="flex items-center text-sm font-medium text-green-700 mb-2">
                    <CheckCircle2 className="w-4 h-4 mr-1" />
                    Opportunities ({opportunities.length})
                  </h4>
                  <div className="space-y-2">
                    {opportunities.length > 0 ? opportunities.map((opp: string, index: number) => (
                      <Alert key={index} className="border-green-200 bg-green-50">
                        <AlertDescription className="text-sm text-green-700">
                          {opp}
                        </AlertDescription>
                      </Alert>
                    )) : (
                      <p className="text-sm text-gray-500">No significant opportunities identified</p>
                    )}
                  </div>
                </div>

                {/* Risk Factors */}
                <div>
                  <h4 className="flex items-center text-sm font-medium text-red-700 mb-2">
                    <AlertTriangle className="w-4 h-4 mr-1" />
                    Risk Factors ({riskFactors.length})
                  </h4>
                  <div className="space-y-2">
                    {riskFactors.length > 0 ? riskFactors.map((risk: string, index: number) => (
                      <Alert key={index} className="border-red-200 bg-red-50">
                        <AlertDescription className="text-sm text-red-700">
                          {risk}
                        </AlertDescription>
                      </Alert>
                    )) : (
                      <p className="text-sm text-gray-500">No significant risks identified</p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Market Analysis */}
        <TabsContent value="market" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Comparable Properties */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Building className="w-5 h-5 mr-2" />
                  Comparable Properties
                </CardTitle>
              </CardHeader>
              <CardContent>
                {marketComparisonData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={marketComparisonData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="property" />
                      <YAxis />
                      <Tooltip
                        formatter={(value: any, name: string) => [
                          name === 'value' ? formatCurrency(value) : value,
                          name === 'value' ? 'Property Value' : 'Price/SqFt'
                        ]}
                      />
                      <Bar dataKey="value" fill="#3b82f6" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="text-center py-8">
                    <Building className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                    <p className="text-gray-500">No comparable properties found</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Market Statistics */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <MapPin className="w-5 h-5 mr-2" />
                  Market Statistics
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <p className="text-xs text-blue-600 uppercase tracking-wide">County Median</p>
                    <p className="text-xl font-semibold text-blue-900">
                      {formatCurrency(marketAnalysis.countyMedianValue)}
                    </p>
                  </div>
                  <div className="p-3 bg-green-50 rounded-lg">
                    <p className="text-xs text-green-600 uppercase tracking-wide">City Median</p>
                    <p className="text-xl font-semibold text-green-900">
                      {formatCurrency(marketAnalysis.cityMedianValue)}
                    </p>
                  </div>
                  <div className="p-3 bg-purple-50 rounded-lg">
                    <p className="text-xs text-purple-600 uppercase tracking-wide">Price/SqFt</p>
                    <p className="text-xl font-semibold text-purple-900">
                      ${marketAnalysis.pricePerSqft?.toFixed(0) || 'N/A'}
                    </p>
                  </div>
                  <div className="p-3 bg-orange-50 rounded-lg">
                    <p className="text-xs text-orange-600 uppercase tracking-wide">Appreciation</p>
                    <p className="text-xl font-semibold text-orange-900">
                      {formatPercentage(marketAnalysis.appreciation)}
                    </p>
                  </div>
                </div>

                {neighborhood_stats && (
                  <div className="border-t pt-4">
                    <h4 className="text-sm font-medium mb-3">Neighborhood Statistics</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>Total Properties:</span>
                        <span className="font-medium">{neighborhood_stats.total_properties?.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Avg Property Value:</span>
                        <span className="font-medium">{formatCurrency(neighborhood_stats.avg_value)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Homestead Rate:</span>
                        <span className="font-medium">{formatPercentage(neighborhood_stats.homestead_rate)}</span>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Financial Analysis */}
        <TabsContent value="financial" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Investment Returns</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm">Cap Rate:</span>
                    <span className="font-medium text-lg">{formatPercentage(calculations.capRate)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">ROI:</span>
                    <span className="font-medium text-lg">{formatPercentage(calculations.roi)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Payback Period:</span>
                    <span className="font-medium text-lg">
                      {calculations.paybackPeriod ? `${calculations.paybackPeriod.toFixed(1)} years` : 'N/A'}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Cash Flow Analysis</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm">Monthly Cash Flow:</span>
                    <span className="font-medium text-lg">
                      {calculations.cashFlow ? formatCurrency(calculations.cashFlow / 12) : 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Annual Cash Flow:</span>
                    <span className="font-medium text-lg">{formatCurrency(calculations.cashFlow)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Tax Rate:</span>
                    <span className="font-medium text-lg">{formatPercentage(calculations.taxRate)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Property Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm">Property Age:</span>
                    <span className="font-medium text-lg">{calculations.propertyAge || 'N/A'} years</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Land/Value Ratio:</span>
                    <span className="font-medium text-lg">
                      {calculations.landToValueRatio ? (calculations.landToValueRatio * 100).toFixed(1) + '%' : 'N/A'}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Trends Analysis */}
        <TabsContent value="trends" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Sales Trends */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Activity className="w-5 h-5 mr-2" />
                  Sales History Trends
                </CardTitle>
              </CardHeader>
              <CardContent>
                {salesTrendData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={salesTrendData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="period" />
                      <YAxis />
                      <Tooltip formatter={(value: any) => [formatCurrency(value), 'Sale Price']} />
                      <Area type="monotone" dataKey="price" stroke="#8884d8" fill="#8884d8" />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="text-center py-8">
                    <Activity className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                    <p className="text-gray-500">No sales history available</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Growth Projections */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <TrendingUp className="w-5 h-5 mr-2" />
                  Growth Projections
                </CardTitle>
              </CardHeader>
              <CardContent>
                {projectionData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={projectionData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="year" />
                      <YAxis />
                      <Tooltip
                        formatter={(value: any, name: string) => [
                          name === 'growth' ? formatPercentage(value) : formatCurrency(value),
                          name === 'growth' ? 'Growth Rate' : 'Projected Value'
                        ]}
                      />
                      <Line type="monotone" dataKey="growth" stroke="#10b981" strokeWidth={2} />
                      <Line type="monotone" dataKey="projectedValue" stroke="#6366f1" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="text-center py-8">
                    <TrendingUp className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                    <p className="text-gray-500">No growth projections available</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* AI Insights */}
        <TabsContent value="ai-insights" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Brain className="w-5 h-5 mr-2" />
                AI-Powered Property Insights
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Investment Recommendation */}
              <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border">
                <h4 className="font-semibold text-blue-900 mb-2">Investment Recommendation</h4>
                <p className="text-blue-800">
                  {investmentScore >= 80
                    ? "🌟 Excellent investment opportunity with strong fundamentals and growth potential."
                    : investmentScore >= 60
                    ? "👍 Good investment potential with manageable risks and decent returns."
                    : "⚠️ Consider carefully - this property has mixed indicators and may require additional analysis."
                  }
                </p>
              </div>

              {/* Key Insights */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                  <h5 className="font-medium text-green-800 mb-2">Market Position</h5>
                  <p className="text-sm text-green-700">
                    Property is in the {marketAnalysis.valuePercentile?.toFixed(0) || 'N/A'}th percentile for the area,
                    indicating {marketAnalysis.valuePercentile > 75 ? 'premium' : marketAnalysis.valuePercentile > 50 ? 'above average' : 'below average'} pricing.
                  </p>
                </div>

                <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                  <h5 className="font-medium text-purple-800 mb-2">Financial Health</h5>
                  <p className="text-sm text-purple-700">
                    {calculations.capRate
                      ? `Cap rate of ${formatPercentage(calculations.capRate)} suggests ${calculations.capRate > 8 ? 'excellent' : calculations.capRate > 6 ? 'good' : 'modest'} cash flow potential.`
                      : 'Limited financial data available for comprehensive analysis.'
                    }
                  </p>
                </div>
              </div>

              {/* Action Items */}
              <div className="border-t pt-4">
                <h4 className="font-semibold mb-3">Recommended Next Steps</h4>
                <div className="space-y-2">
                  {investmentScore < 60 && (
                    <Alert className="border-orange-200 bg-orange-50">
                      <Info className="w-4 h-4" />
                      <AlertDescription className="text-orange-700">
                        Consider conducting additional due diligence before investing
                      </AlertDescription>
                    </Alert>
                  )}

                  {!data?.lastSale && (
                    <Alert className="border-blue-200 bg-blue-50">
                      <Info className="w-4 h-4" />
                      <AlertDescription className="text-blue-700">
                        Research recent sales activity in the area for better market validation
                      </AlertDescription>
                    </Alert>
                  )}

                  {calculations.taxRate > 3 && (
                    <Alert className="border-red-200 bg-red-50">
                      <Info className="w-4 h-4" />
                      <AlertDescription className="text-red-700">
                        High tax burden identified - factor into cash flow projections
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}