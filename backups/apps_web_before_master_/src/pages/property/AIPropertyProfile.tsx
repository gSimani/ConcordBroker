import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  MapPin,
  DollarSign,
  TrendingUp,
  TrendingDown,
  Calendar,
  Activity,
  Brain,
  Star,
  Home,
  Building,
  Eye,
  ExternalLink,
  BarChart3,
  Loader2,
  AlertCircle,
  CheckCircle,
  Receipt
} from 'lucide-react';
import { useAISalesHistory, formatCurrency, formatDate, getAppreciationColor, getInvestmentGradeColor } from '@/hooks/useAISalesHistory';
import NAVAssessments from '@/components/property/NAVAssessments';

interface PropertyData {
  parcel_id: string;
  phy_addr1: string;
  phy_addr2?: string;
  phy_city: string;
  phy_zipcd: string;
  owner_name: string;
  just_value: number;
  tot_lvg_area?: number;
  lnd_sqfoot?: number;
  act_yr_blt?: number;
  property_use?: string;
  propertyUseDesc?: string;
}

export function AIPropertyProfile() {
  const { parcelId } = useParams<{ parcelId: string }>();
  const [propertyData, setPropertyData] = useState<PropertyData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // AI Sales History Integration
  const { salesData, aiAnalysis, isLoading: salesLoading, error: salesError } = useAISalesHistory(parcelId || '', true);

  // Fetch property data
  useEffect(() => {
    const fetchPropertyData = async () => {
      if (!parcelId) return;

      try {
        setLoading(true);
        const response = await fetch(`http://localhost:8003/api/autocomplete?q=${parcelId}&limit=1`);

        if (response.ok) {
          const result = await response.json();
          if (result.success && result.data.length > 0) {
            setPropertyData(result.data[0]);
          } else {
            setError('Property not found');
          }
        } else {
          setError('Failed to fetch property data');
        }
      } catch (err) {
        setError('Error loading property data');
        console.error('Error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchPropertyData();
  }, [parcelId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !propertyData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">Property Not Found</h2>
          <p className="text-muted-foreground">{error || 'Unable to load property data'}</p>
        </div>
      </div>
    );
  }

  const displayAddress = propertyData.phy_addr2
    ? `${propertyData.phy_addr1} ${propertyData.phy_addr2}`
    : propertyData.phy_addr1;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header Section */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Home className="w-6 h-6 text-blue-600" />
              <h1 className="text-3xl font-bold text-gray-900">{displayAddress}</h1>
            </div>
            <div className="flex items-center gap-4 text-muted-foreground mb-4">
              <div className="flex items-center gap-1">
                <MapPin className="w-4 h-4" />
                <span>{propertyData.phy_city}, FL {propertyData.phy_zipcd}</span>
              </div>
              <span>•</span>
              <span>Parcel: {propertyData.parcel_id}</span>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">
                  {formatCurrency(propertyData.just_value)}
                </p>
                <p className="text-sm text-muted-foreground">Appraised Value</p>
              </div>
              {propertyData.tot_lvg_area && (
                <div className="text-center">
                  <p className="text-xl font-semibold">{propertyData.tot_lvg_area.toLocaleString()} sq ft</p>
                  <p className="text-sm text-muted-foreground">Building</p>
                </div>
              )}
              {propertyData.act_yr_blt && (
                <div className="text-center">
                  <p className="text-xl font-semibold">{propertyData.act_yr_blt}</p>
                  <p className="text-sm text-muted-foreground">Year Built</p>
                </div>
              )}
            </div>
          </div>

          {/* AI Investment Grade */}
          {aiAnalysis?.investment_grade && (
            <div className="text-center">
              <Badge
                className={`text-lg px-4 py-2 text-white ${getInvestmentGradeColor(aiAnalysis.investment_grade)}`}
              >
                <Brain className="w-5 h-5 mr-2" />
                {aiAnalysis.investment_grade}
              </Badge>
              {aiAnalysis.investment_score && (
                <div className="mt-2 flex items-center justify-center gap-1">
                  <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                  <span className="font-semibold">{aiAnalysis.investment_score}/100</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Tabs for Different Sections */}
      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="sales-history">Sales History</TabsTrigger>
          <TabsTrigger value="ai-analysis">AI Analysis</TabsTrigger>
          <TabsTrigger value="nav-assessments">NAV Assessments</TabsTrigger>
          <TabsTrigger value="investment">Investment</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Property Details */}
            <Card className="p-6">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <Building className="w-5 h-5" />
                Property Details
              </h3>
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-muted-foreground">Property Type</p>
                  <p className="font-medium">{propertyData.propertyUseDesc || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Owner</p>
                  <p className="font-medium">{propertyData.owner_name}</p>
                </div>
                {propertyData.lnd_sqfoot && (
                  <div>
                    <p className="text-sm text-muted-foreground">Land Size</p>
                    <p className="font-medium">{propertyData.lnd_sqfoot.toLocaleString()} sq ft</p>
                  </div>
                )}
              </div>
            </Card>

            {/* Sales Summary */}
            <Card className="p-6">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5" />
                Sales Activity
              </h3>
              {salesLoading ? (
                <div className="flex items-center justify-center py-4">
                  <Loader2 className="w-6 h-6 animate-spin" />
                </div>
              ) : salesData?.has_sales ? (
                <div className="space-y-3">
                  <div>
                    <p className="text-sm text-muted-foreground">Last Sale</p>
                    <p className="font-bold text-lg text-green-600">
                      {formatCurrency(salesData.last_sale_price)}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {formatDate(salesData.last_sale_date)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Total Sales</p>
                    <p className="font-medium">{salesData.total_sales} transactions</p>
                  </div>
                  {salesData.appreciation !== 0 && (
                    <div>
                      <p className="text-sm text-muted-foreground">Appreciation</p>
                      <div className="flex items-center gap-2">
                        <TrendingUp className={`w-4 h-4 ${getAppreciationColor(salesData.appreciation)}`} />
                        <span className={`font-medium ${getAppreciationColor(salesData.appreciation)}`}>
                          {salesData.appreciation > 0 ? '+' : ''}{salesData.appreciation.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-muted-foreground">No sales history available</p>
              )}
            </Card>

            {/* AI Quick Insights */}
            <Card className="p-6">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <Brain className="w-5 h-5 text-purple-600" />
                AI Insights
              </h3>
              {salesLoading ? (
                <div className="flex items-center justify-center py-4">
                  <Loader2 className="w-6 h-6 animate-spin" />
                </div>
              ) : (
                <div className="space-y-3">
                  {salesData?.quick_insight && (
                    <p className="text-sm">{salesData.quick_insight}</p>
                  )}

                  {aiAnalysis?.market_activity && (
                    <div>
                      <p className="text-sm text-muted-foreground">Market Activity</p>
                      <Badge variant="outline" className="mt-1">
                        {aiAnalysis.market_activity.activity_emoji} {aiAnalysis.market_activity.activity_level}
                      </Badge>
                    </div>
                  )}

                  {aiAnalysis?.investment_insights?.ai_summary && (
                    <p className="text-sm text-purple-700 bg-purple-50 p-3 rounded">
                      {aiAnalysis.investment_insights.ai_summary}
                    </p>
                  )}
                </div>
              )}
            </Card>
          </div>
        </TabsContent>

        {/* Sales History Tab */}
        <TabsContent value="sales-history" className="space-y-6">
          <Card className="p-6">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Complete Sales History
            </h3>
            {salesLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-8 h-8 animate-spin" />
              </div>
            ) : salesData?.has_sales ? (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <p className="text-2xl font-bold text-blue-600">{salesData.total_sales}</p>
                    <p className="text-sm text-muted-foreground">Total Sales</p>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <p className="text-2xl font-bold text-green-600">
                      {formatCurrency(salesData.last_sale_price)}
                    </p>
                    <p className="text-sm text-muted-foreground">Last Sale Price</p>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <p className="text-2xl font-bold text-purple-600">
                      {salesData.appreciation > 0 ? '+' : ''}{salesData.appreciation.toFixed(1)}%
                    </p>
                    <p className="text-sm text-muted-foreground">Total Appreciation</p>
                  </div>
                </div>

                <p className="text-muted-foreground">
                  Detailed sales history will be displayed here with chart visualization.
                </p>
              </div>
            ) : (
              <div className="text-center py-8">
                <Activity className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">No sales history available for this property</p>
              </div>
            )}
          </Card>
        </TabsContent>

        {/* AI Analysis Tab */}
        <TabsContent value="ai-analysis" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Price Trends */}
            <Card className="p-6">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                Price Trend Analysis
              </h3>
              {aiAnalysis?.price_trend ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{aiAnalysis.price_trend.trend_emoji}</span>
                    <div>
                      <p className="font-medium capitalize">
                        {aiAnalysis.price_trend.trend?.replace('_', ' ')}
                      </p>
                      <p className="text-sm text-muted-foreground">Market Trend</p>
                    </div>
                  </div>

                  {aiAnalysis.price_trend.total_appreciation !== undefined && (
                    <div>
                      <p className="text-sm text-muted-foreground">Total Appreciation</p>
                      <p className={`text-xl font-bold ${getAppreciationColor(aiAnalysis.price_trend.total_appreciation)}`}>
                        {aiAnalysis.price_trend.total_appreciation > 0 ? '+' : ''}
                        {aiAnalysis.price_trend.total_appreciation}%
                      </p>
                    </div>
                  )}

                  {aiAnalysis.price_trend.annual_appreciation !== undefined && (
                    <div>
                      <p className="text-sm text-muted-foreground">Annual Appreciation Rate</p>
                      <p className={`text-lg font-semibold ${getAppreciationColor(aiAnalysis.price_trend.annual_appreciation)}`}>
                        {aiAnalysis.price_trend.annual_appreciation > 0 ? '+' : ''}
                        {aiAnalysis.price_trend.annual_appreciation}% per year
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-muted-foreground">Insufficient data for price trend analysis</p>
              )}
            </Card>

            {/* Market Activity */}
            <Card className="p-6">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5" />
                Market Activity
              </h3>
              {aiAnalysis?.market_activity ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{aiAnalysis.market_activity.activity_emoji}</span>
                    <div>
                      <p className="font-medium capitalize">
                        {aiAnalysis.market_activity.activity_level?.replace('_', ' ')} Activity
                      </p>
                      <p className="text-sm text-muted-foreground">Activity Level</p>
                    </div>
                  </div>

                  {aiAnalysis.market_activity.total_transactions !== undefined && (
                    <div>
                      <p className="text-sm text-muted-foreground">Total Transactions</p>
                      <p className="text-xl font-bold">{aiAnalysis.market_activity.total_transactions}</p>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-muted-foreground">No market activity data available</p>
              )}
            </Card>
          </div>

          {/* Investment Insights */}
          {aiAnalysis?.investment_insights && (
            <Card className="p-6">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <Brain className="w-5 h-5 text-purple-600" />
                AI Investment Analysis
              </h3>
              <div className="space-y-6">
                {/* Insights */}
                {aiAnalysis.investment_insights.insights && aiAnalysis.investment_insights.insights.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-3 text-green-700 flex items-center gap-2">
                      <CheckCircle className="w-4 h-4" />
                      Key Insights
                    </h4>
                    <ul className="space-y-2">
                      {aiAnalysis.investment_insights.insights.map((insight, index) => (
                        <li key={index} className="flex items-start gap-2">
                          <span className="text-green-500 mt-1">•</span>
                          <span className="text-sm">{insight}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Recommendations */}
                {aiAnalysis.investment_insights.recommendations && aiAnalysis.investment_insights.recommendations.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-3 text-blue-700 flex items-center gap-2">
                      <CheckCircle className="w-4 h-4" />
                      Recommendations
                    </h4>
                    <ul className="space-y-2">
                      {aiAnalysis.investment_insights.recommendations.map((rec, index) => (
                        <li key={index} className="flex items-start gap-2">
                          <span className="text-blue-500 mt-1">•</span>
                          <span className="text-sm">{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Risk Factors */}
                {aiAnalysis.investment_insights.risk_factors && aiAnalysis.investment_insights.risk_factors.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-3 text-red-700 flex items-center gap-2">
                      <AlertCircle className="w-4 h-4" />
                      Risk Factors
                    </h4>
                    <ul className="space-y-2">
                      {aiAnalysis.investment_insights.risk_factors.map((risk, index) => (
                        <li key={index} className="flex items-start gap-2">
                          <span className="text-red-500 mt-1">•</span>
                          <span className="text-sm">{risk}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </Card>
          )}
        </TabsContent>

        {/* NAV Assessments Tab */}
        <TabsContent value="nav-assessments" className="space-y-6">
          <NAVAssessments
            parcelId={parcelId || ''}
            showHeader={false}
          />
        </TabsContent>

        {/* Investment Tab */}
        <TabsContent value="investment" className="space-y-6">
          <Card className="p-6">
            <h3 className="font-semibold mb-6 flex items-center gap-2">
              <Star className="w-5 h-5 text-yellow-500" />
              Investment Summary
            </h3>

            {aiAnalysis?.investment_insights ? (
              <div className="space-y-6">
                {/* Investment Score */}
                <div className="text-center p-6 bg-gradient-to-r from-yellow-50 to-orange-50 rounded-lg">
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <Star className="w-8 h-8 text-yellow-500 fill-yellow-500" />
                    <span className="text-4xl font-bold">{aiAnalysis.investment_score}</span>
                    <span className="text-2xl text-muted-foreground">/100</span>
                  </div>
                  <p className="text-lg font-medium">Investment Score</p>
                  <Badge
                    className={`mt-2 text-white ${getInvestmentGradeColor(aiAnalysis.investment_grade)}`}
                  >
                    Grade: {aiAnalysis.investment_grade}
                  </Badge>
                </div>

                {/* AI Summary */}
                {aiAnalysis.investment_insights.ai_summary && (
                  <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                    <h4 className="font-medium mb-2 text-purple-700">AI Summary</h4>
                    <p className="text-purple-800">{aiAnalysis.investment_insights.ai_summary}</p>
                  </div>
                )}

                {/* Quick Actions */}
                <div className="flex gap-4">
                  <Button className="flex-1" variant="default">
                    <Eye className="w-4 h-4 mr-2" />
                    Schedule Viewing
                  </Button>
                  <Button className="flex-1" variant="outline">
                    <ExternalLink className="w-4 h-4 mr-2" />
                    View on Map
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <Brain className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">AI analysis is being processed...</p>
              </div>
            )}
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}