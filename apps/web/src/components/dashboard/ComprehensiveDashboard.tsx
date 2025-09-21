import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  TrendingUp, TrendingDown, DollarSign, Home, Building, Users,
  MapPin, Calendar, BarChart3, PieChart, Activity, Target,
  Zap, Bell, Filter, Download, RefreshCw, Star, Eye,
  ArrowUpRight, ArrowDownRight, Plus, Search, Map
} from 'lucide-react';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart as RechartsPieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter
} from 'recharts';
import { supabase } from '@/lib/supabase';

interface ComprehensiveDashboardProps {
  county?: string;
  city?: string;
}

interface DashboardData {
  overview: {
    totalProperties: number;
    totalValue: number;
    avgValue: number;
    medianValue: number;
    recentSales: number;
    activeInvestments: number;
  };
  marketTrends: any[];
  topPerformers: any[];
  riskAlerts: any[];
  countyStats: any[];
  cityBreakdown: any[];
  investmentOpportunities: any[];
  priceDistribution: any[];
  salesVelocity: any[];
  growthProjections: any[];
}

export function ComprehensiveDashboard({ county = 'BROWARD', city }: ComprehensiveDashboardProps) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [timeRange, setTimeRange] = useState('1y');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, [county, city, timeRange]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const dashboardData = await fetchComprehensiveDashboardData(county, city, timeRange);
      setData(dashboardData);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadDashboardData();
    setRefreshing(false);
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('en-US').format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-6">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-1/2"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-12">
        <BarChart3 className="w-16 h-16 mx-auto text-gray-400 mb-4" />
        <p className="text-gray-500">Failed to load dashboard data</p>
        <Button onClick={loadDashboardData} className="mt-4">
          <RefreshCw className="w-4 h-4 mr-2" />
          Retry
        </Button>
      </div>
    );
  }

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Market Analytics Dashboard</h1>
          <p className="text-gray-600">
            Comprehensive real estate analytics for {city ? `${city}, ` : ''}{county} County
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-2 border rounded-lg"
          >
            <option value="1m">Last Month</option>
            <option value="3m">Last 3 Months</option>
            <option value="6m">Last 6 Months</option>
            <option value="1y">Last Year</option>
            <option value="all">All Time</option>
          </select>
          <Button onClick={handleRefresh} disabled={refreshing} variant="outline">
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Key Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="border-l-4 border-blue-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Properties</p>
                <p className="text-3xl font-bold text-gray-900">
                  {formatNumber(data.overview.totalProperties)}
                </p>
                <p className="text-sm text-blue-600">+2.3% from last month</p>
              </div>
              <Home className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-green-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Market Value</p>
                <p className="text-3xl font-bold text-gray-900">
                  {formatCurrency(data.overview.totalValue)}
                </p>
                <p className="text-sm text-green-600">+5.7% from last month</p>
              </div>
              <DollarSign className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-purple-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Average Value</p>
                <p className="text-3xl font-bold text-gray-900">
                  {formatCurrency(data.overview.avgValue)}
                </p>
                <p className="text-sm text-purple-600">Median: {formatCurrency(data.overview.medianValue)}</p>
              </div>
              <BarChart3 className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-orange-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Recent Sales</p>
                <p className="text-3xl font-bold text-gray-900">
                  {formatNumber(data.overview.recentSales)}
                </p>
                <p className="text-sm text-orange-600">Last 30 days</p>
              </div>
              <TrendingUp className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Dashboard Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="market-trends">Market Trends</TabsTrigger>
          <TabsTrigger value="investments">Investments</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
          <TabsTrigger value="projections">Projections</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Market Trends Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Activity className="w-5 h-5 mr-2" />
                  Market Value Trends
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={data.marketTrends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip formatter={(value: any) => [formatCurrency(value), 'Avg Value']} />
                    <Area type="monotone" dataKey="avgValue" stroke="#8884d8" fill="#8884d8" />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Sales Velocity */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Zap className="w-5 h-5 mr-2" />
                  Sales Velocity
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={data.salesVelocity}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="salesCount" fill="#00C49F" />
                    <Bar dataKey="avgDaysOnMarket" fill="#FF8042" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* County Breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <MapPin className="w-5 h-5 mr-2" />
                  City Performance Breakdown
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={data.cityBreakdown} layout="horizontal">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis type="category" dataKey="city" width={100} />
                    <Tooltip formatter={(value: any) => [formatCurrency(value), 'Avg Value']} />
                    <Bar dataKey="avgValue" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <PieChart className="w-5 h-5 mr-2" />
                  Price Distribution
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <RechartsPieChart>
                    <Pie
                      data={data.priceDistribution}
                      cx="50%"
                      cy="50%"
                      outerRadius={120}
                      fill="#8884d8"
                      dataKey="count"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {data.priceDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </RechartsPieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Top Performers and Risk Alerts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Star className="w-5 h-5 mr-2" />
                  Top Performing Areas
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {data.topPerformers.map((performer, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                      <div>
                        <p className="font-medium">{performer.area}</p>
                        <p className="text-sm text-gray-600">{formatNumber(performer.properties)} properties</p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-green-600">+{formatPercentage(performer.growth)}</p>
                        <p className="text-sm text-gray-600">{formatCurrency(performer.avgValue)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Bell className="w-5 h-5 mr-2" />
                  Risk Alerts
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {data.riskAlerts.map((alert, index) => (
                    <Alert key={index} className="border-orange-200 bg-orange-50">
                      <AlertDescription className="text-orange-700">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium">{alert.area}</p>
                            <p className="text-sm">{alert.description}</p>
                          </div>
                          <Badge variant="outline" className="border-orange-300 text-orange-700">
                            {alert.severity}
                          </Badge>
                        </div>
                      </AlertDescription>
                    </Alert>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Market Trends Tab */}
        <TabsContent value="market-trends" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Property Value Trends</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart data={data.marketTrends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="avgValue" stroke="#8884d8" strokeWidth={2} />
                    <Line type="monotone" dataKey="medianValue" stroke="#82ca9d" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Sales Volume Trends</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <AreaChart data={data.salesVelocity}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Area type="monotone" dataKey="salesCount" stroke="#ff7300" fill="#ff7300" />
                    <Area type="monotone" dataKey="totalVolume" stroke="#0088fe" fill="#0088fe" />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Investment Opportunities Tab */}
        <TabsContent value="investments" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Target className="w-5 h-5 mr-2" />
                Investment Opportunities
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {data.investmentOpportunities.map((opportunity, index) => (
                  <div key={index} className="p-4 border rounded-lg hover:bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium">{opportunity.address}</h4>
                        <p className="text-sm text-gray-600">{opportunity.city}</p>
                        <div className="flex items-center space-x-4 mt-2">
                          <Badge className="bg-green-100 text-green-800">
                            Score: {opportunity.score}/100
                          </Badge>
                          <span className="text-sm">Cap Rate: {formatPercentage(opportunity.capRate)}</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold">{formatCurrency(opportunity.price)}</p>
                        <p className="text-sm text-gray-600">
                          {formatCurrency(opportunity.cashFlow)}/month
                        </p>
                        <Button size="sm" className="mt-2">
                          <Eye className="w-4 h-4 mr-1" />
                          View Details
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Price vs. Square Footage Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <ScatterChart>
                    <CartesianGrid />
                    <XAxis type="number" dataKey="sqft" name="Square Feet" />
                    <YAxis type="number" dataKey="price" name="Price" />
                    <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                    <Scatter name="Properties" data={data.priceDistribution} fill="#8884d8" />
                  </ScatterChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>County Performance Comparison</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={data.countyStats}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="county" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="avgValue" fill="#8884d8" />
                    <Bar dataKey="salesVolume" fill="#82ca9d" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Alerts Tab */}
        <TabsContent value="alerts" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-red-600">High Risk Properties</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {data.riskAlerts.filter(alert => alert.severity === 'High').map((alert, index) => (
                    <Alert key={index} className="border-red-200 bg-red-50">
                      <AlertDescription className="text-red-700">
                        <strong>{alert.area}</strong>: {alert.description}
                      </AlertDescription>
                    </Alert>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-orange-600">Medium Risk Properties</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {data.riskAlerts.filter(alert => alert.severity === 'Medium').map((alert, index) => (
                    <Alert key={index} className="border-orange-200 bg-orange-50">
                      <AlertDescription className="text-orange-700">
                        <strong>{alert.area}</strong>: {alert.description}
                      </AlertDescription>
                    </Alert>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Projections Tab */}
        <TabsContent value="projections" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <TrendingUp className="w-5 h-5 mr-2" />
                Market Growth Projections
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={data.growthProjections}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="projectedGrowth" stroke="#8884d8" strokeWidth={2} />
                  <Line type="monotone" dataKey="conservativeGrowth" stroke="#82ca9d" strokeWidth={2} />
                  <Line type="monotone" dataKey="optimisticGrowth" stroke="#ffc658" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

// Data fetching function
async function fetchComprehensiveDashboardData(county: string, city?: string, timeRange?: string): Promise<DashboardData> {
  try {
    // This would normally make multiple parallel API calls to get comprehensive data
    // For demo purposes, we'll return mock data

    return {
      overview: {
        totalProperties: 789542,
        totalValue: 234567890000,
        avgValue: 297000,
        medianValue: 235000,
        recentSales: 3421,
        activeInvestments: 156
      },
      marketTrends: generateMarketTrends(),
      topPerformers: generateTopPerformers(),
      riskAlerts: generateRiskAlerts(),
      countyStats: generateCountyStats(),
      cityBreakdown: generateCityBreakdown(),
      investmentOpportunities: generateInvestmentOpportunities(),
      priceDistribution: generatePriceDistribution(),
      salesVelocity: generateSalesVelocity(),
      growthProjections: generateGrowthProjections()
    };
  } catch (error) {
    console.error('Error fetching dashboard data:', error);
    throw error;
  }
}

// Mock data generators
function generateMarketTrends() {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return months.map(month => ({
    date: month,
    avgValue: 280000 + Math.random() * 50000,
    medianValue: 235000 + Math.random() * 40000,
    salesCount: 280 + Math.random() * 120
  }));
}

function generateTopPerformers() {
  return [
    { area: 'Downtown Fort Lauderdale', properties: 1245, growth: 8.2, avgValue: 485000 },
    { area: 'Las Olas', properties: 892, growth: 7.8, avgValue: 650000 },
    { area: 'Hollywood Beach', properties: 567, growth: 6.9, avgValue: 425000 },
    { area: 'Coral Springs', properties: 2341, growth: 5.4, avgValue: 385000 },
    { area: 'Weston', properties: 1876, growth: 4.7, avgValue: 520000 }
  ];
}

function generateRiskAlerts() {
  return [
    { area: 'Northwest Broward', description: 'High foreclosure rate detected', severity: 'High' },
    { area: 'Oakland Park', description: 'Declining property values', severity: 'Medium' },
    { area: 'Pompano Beach East', description: 'Increased days on market', severity: 'Medium' },
    { area: 'Sunrise', description: 'Tax delinquency spike', severity: 'High' }
  ];
}

function generateCountyStats() {
  return [
    { county: 'Broward', avgValue: 297000, salesVolume: 125000 },
    { county: 'Miami-Dade', avgValue: 425000, salesVolume: 185000 },
    { county: 'Palm Beach', avgValue: 385000, salesVolume: 95000 },
    { county: 'Orange', avgValue: 285000, salesVolume: 110000 }
  ];
}

function generateCityBreakdown() {
  const cities = ['Fort Lauderdale', 'Hollywood', 'Pompano Beach', 'Coral Springs', 'Davie', 'Plantation', 'Sunrise', 'Weston'];
  return cities.map(city => ({
    city,
    avgValue: 250000 + Math.random() * 300000,
    properties: 5000 + Math.random() * 15000,
    growth: -2 + Math.random() * 10
  }));
}

function generateInvestmentOpportunities() {
  return [
    {
      address: '123 Investment Blvd',
      city: 'Fort Lauderdale',
      price: 285000,
      score: 87,
      capRate: 8.2,
      cashFlow: 1850
    },
    {
      address: '456 Opportunity St',
      city: 'Hollywood',
      price: 195000,
      score: 82,
      capRate: 9.1,
      cashFlow: 1450
    },
    {
      address: '789 Cash Flow Ave',
      city: 'Pompano Beach',
      price: 165000,
      score: 79,
      capRate: 7.8,
      cashFlow: 1075
    }
  ];
}

function generatePriceDistribution() {
  return [
    { name: 'Under $200K', count: 125000 },
    { name: '$200K-$400K', count: 285000 },
    { name: '$400K-$600K', count: 185000 },
    { name: '$600K-$1M', count: 125000 },
    { name: 'Over $1M', count: 69000 }
  ];
}

function generateSalesVelocity() {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return months.map(month => ({
    month,
    salesCount: 280 + Math.random() * 120,
    avgDaysOnMarket: 45 + Math.random() * 30,
    totalVolume: 85000000 + Math.random() * 25000000
  }));
}

function generateGrowthProjections() {
  const years = [2024, 2025, 2026, 2027, 2028];
  return years.map(year => ({
    year,
    projectedGrowth: 3.2 - (year - 2024) * 0.3,
    conservativeGrowth: 2.1 - (year - 2024) * 0.2,
    optimisticGrowth: 4.8 - (year - 2024) * 0.4
  }));
}