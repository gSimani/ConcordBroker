/**
 * Comprehensive Property Charts Component
 * Displays interactive visualizations for property data
 */

import React, { useEffect, useState } from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  AreaChart, Area, ComposedChart, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { formatCurrency, formatPercentage } from '@/lib/formatters';

interface PropertyChartsProps {
  propertyData: any;
  salesHistory: any[];
  calculations: any;
  comparables: any[];
  taxHistory?: any[];
}

// Color palette for charts
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

export const PropertyCharts: React.FC<PropertyChartsProps> = ({
  propertyData,
  salesHistory,
  calculations,
  comparables,
  taxHistory = []
}) => {
  const [pythonCharts, setPythonCharts] = useState<{ [key: string]: string }>({});
  const [loading, setLoading] = useState(false);

  // Fetch Python-generated visualizations
  useEffect(() => {
    const fetchPythonCharts = async () => {
      if (!propertyData?.parcel_id) return;

      setLoading(true);
      try {
        const endpoints = [
          `/api/visualize/investment-metrics/${propertyData.parcel_id}`,
          '/api/visualize/market-overview?county=' + (propertyData.county || 'BROWARD'),
          '/api/visualize/sales-trends?folio=' + propertyData.parcel_id
        ];

        const responses = await Promise.all(
          endpoints.map(url =>
            fetch(`http://localhost:8002${url}`).then(res => res.json())
          )
        );

        setPythonCharts({
          investment: responses[0]?.chart,
          market: responses[1]?.chart,
          sales: responses[2]?.chart
        });
      } catch (error) {
        console.error('Error fetching Python charts:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPythonCharts();
  }, [propertyData]);

  // Prepare data for sales trend chart
  const salesTrendData = salesHistory.map((sale, index) => ({
    date: new Date(sale.sale_date).toLocaleDateString('en-US', { year: 'numeric', month: 'short' }),
    price: sale.sale_price,
    pricePerSqft: propertyData?.living_area ? sale.sale_price / propertyData.living_area : 0,
    index: index
  })).reverse();

  // Prepare data for value breakdown pie chart
  const valueBreakdownData = [
    { name: 'Land Value', value: propertyData?.land_value || 0 },
    { name: 'Building Value', value: propertyData?.building_value || 0 }
  ].filter(item => item.value > 0);

  // Prepare comparison data
  const comparisonData = [
    { name: 'Subject Property', value: propertyData?.just_value || 0, sqft: propertyData?.living_area || 0 },
    ...comparables.slice(0, 5).map((comp, i) => ({
      name: `Comp ${i + 1}`,
      value: comp.just_value,
      sqft: comp.living_area
    }))
  ];

  // Investment metrics radar chart data
  const investmentMetricsData = [
    { metric: 'Cap Rate', value: calculations?.capRate || 0, fullMark: 15 },
    { metric: 'Cash Flow', value: (calculations?.cashFlow || 0) / 1000, fullMark: 10 },
    { metric: 'ROI', value: calculations?.roi || 0, fullMark: 20 },
    { metric: 'GRM', value: 20 - (calculations?.grossRentMultiplier || 0), fullMark: 20 },
    { metric: 'Appreciation', value: calculations?.appreciation || 0, fullMark: 10 },
    { metric: 'Tax Efficiency', value: 100 - (calculations?.effectiveTaxRate || 0), fullMark: 100 }
  ];

  // ROI projection data
  const roiProjectionData = Array.from({ length: 10 }, (_, i) => {
    const year = i + 1;
    const appreciationRate = 0.03;
    const rentalGrowth = 0.025;
    const initialValue = propertyData?.just_value || 0;
    const initialRent = calculations?.estimatedRent || 0;

    const futureValue = initialValue * Math.pow(1 + appreciationRate, year);
    const futureRent = initialRent * Math.pow(1 + rentalGrowth, year);
    const cumulativeCashFlow = futureRent * 12 * year;
    const totalReturn = futureValue + cumulativeCashFlow - initialValue;
    const roi = (totalReturn / initialValue) * 100;

    return {
      year,
      propertyValue: futureValue,
      cumulativeCashFlow,
      totalReturn,
      roi
    };
  });

  // Tax history chart data
  const taxHistoryData = taxHistory.length > 0 ? taxHistory :
    Array.from({ length: 5 }, (_, i) => {
      const year = new Date().getFullYear() - i;
      return {
        year,
        assessed: (propertyData?.assessed_value || 0) * (1 - i * 0.02),
        taxable: (propertyData?.taxable_value || 0) * (1 - i * 0.02),
        taxes: (propertyData?.tax_amount || 0) * (1 - i * 0.01)
      };
    }).reverse();

  // Market position scatter plot
  const marketPositionData = comparables.map(comp => ({
    sqft: comp.living_area,
    value: comp.just_value,
    pricePerSqft: comp.just_value / comp.living_area,
    type: 'comparable'
  }));

  if (propertyData) {
    marketPositionData.push({
      sqft: propertyData.living_area,
      value: propertyData.just_value,
      pricePerSqft: propertyData.just_value / propertyData.living_area,
      type: 'subject'
    });
  }

  // Custom tooltip for currency formatting
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border rounded shadow-lg">
          <p className="font-semibold">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }}>
              {entry.name}: {entry.name.includes('Rate') || entry.name.includes('%')
                ? formatPercentage(entry.value)
                : formatCurrency(entry.value)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid grid-cols-6 w-full">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="sales">Sales Analysis</TabsTrigger>
          <TabsTrigger value="investment">Investment</TabsTrigger>
          <TabsTrigger value="market">Market Position</TabsTrigger>
          <TabsTrigger value="projections">Projections</TabsTrigger>
          <TabsTrigger value="python">Advanced</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Value Breakdown Pie Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Property Value Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={valueBreakdownData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={(entry) => `${entry.name}: ${formatCurrency(entry.value)}`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {valueBreakdownData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: number) => formatCurrency(value)} />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Comparison Bar Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Property Value Comparison</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={comparisonData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                    <YAxis tickFormatter={(value) => `$${(value / 1000000).toFixed(1)}M`} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="value" fill="#82ca9d" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Tax History Area Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Tax Assessment History</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={taxHistoryData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Area type="monotone" dataKey="assessed" stackId="1" stroke="#8884d8" fill="#8884d8" name="Assessed Value" />
                  <Area type="monotone" dataKey="taxable" stackId="2" stroke="#82ca9d" fill="#82ca9d" name="Taxable Value" />
                  <Area type="monotone" dataKey="taxes" stackId="3" stroke="#ffc658" fill="#ffc658" name="Tax Amount" />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sales" className="space-y-4">
          {/* Sales History Line Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Sales Price History</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <ComposedChart data={salesTrendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis yAxisId="left" tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`} />
                  <YAxis yAxisId="right" orientation="right" tickFormatter={(value) => `$${value.toFixed(0)}`} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Bar yAxisId="left" dataKey="price" fill="#82ca9d" name="Sale Price" />
                  <Line yAxisId="right" type="monotone" dataKey="pricePerSqft" stroke="#ff7300" name="Price/SqFt" />
                </ComposedChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Sales Price Growth */}
          {salesTrendData.length > 1 && (
            <Card>
              <CardHeader>
                <CardTitle>Price Appreciation Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={salesTrendData.map((sale, i) => ({
                    ...sale,
                    growth: i === 0 ? 0 : ((sale.price - salesTrendData[i - 1].price) / salesTrendData[i - 1].price) * 100
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis tickFormatter={(value) => `${value.toFixed(1)}%`} />
                    <Tooltip formatter={(value: number) => `${value.toFixed(2)}%`} />
                    <Line type="monotone" dataKey="growth" stroke="#8884d8" name="Price Growth %" />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="investment" className="space-y-4">
          {/* Investment Metrics Radar Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Investment Metrics Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <RadarChart data={investmentMetricsData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="metric" />
                  <PolarRadiusAxis angle={90} domain={[0, 'dataMax']} />
                  <Radar name="Property Metrics" dataKey="value" stroke="#8884d8" fill="#8884d8" fillOpacity={0.6} />
                  <Tooltip />
                </RadarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Cash Flow Analysis */}
          <Card>
            <CardHeader>
              <CardTitle>Monthly Cash Flow Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={[
                  { category: 'Rental Income', amount: calculations?.estimatedRent || 0 },
                  { category: 'Property Tax', amount: -(propertyData?.tax_amount || 0) / 12 },
                  { category: 'Insurance', amount: -(propertyData?.just_value || 0) * 0.005 / 12 },
                  { category: 'Maintenance', amount: -(propertyData?.just_value || 0) * 0.01 / 12 },
                  { category: 'Net Cash Flow', amount: calculations?.cashFlow || 0 }
                ]}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="category" angle={-45} textAnchor="end" height={100} />
                  <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(1)}K`} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="amount">
                    {valueBreakdownData?.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={entry.amount > 0 ? '#82ca9d' : '#ff6b6b'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="market" className="space-y-4">
          {/* Market Position Scatter Plot */}
          <Card>
            <CardHeader>
              <CardTitle>Market Position Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <ScatterChart>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="sqft" name="Square Feet" unit=" sqft" />
                  <YAxis dataKey="value" name="Property Value" tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`} />
                  <Tooltip cursor={{ strokeDasharray: '3 3' }} content={<CustomTooltip />} />
                  <Scatter name="Comparables" data={marketPositionData.filter(d => d.type === 'comparable')} fill="#8884d8" />
                  <Scatter name="Subject Property" data={marketPositionData.filter(d => d.type === 'subject')} fill="#ff7300" />
                </ScatterChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Price per Square Foot Distribution */}
          <Card>
            <CardHeader>
              <CardTitle>Price per Square Foot Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={marketPositionData.sort((a, b) => a.pricePerSqft - b.pricePerSqft).map((d, i) => ({
                  ...d,
                  name: d.type === 'subject' ? 'Subject' : `Comp ${i}`
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis tickFormatter={(value) => `$${value.toFixed(0)}`} />
                  <Tooltip formatter={(value: number) => `$${value.toFixed(2)}/sqft`} />
                  <Bar dataKey="pricePerSqft">
                    {marketPositionData?.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={entry.type === 'subject' ? '#ff7300' : '#82ca9d'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="projections" className="space-y-4">
          {/* ROI Projection Chart */}
          <Card>
            <CardHeader>
              <CardTitle>10-Year ROI Projection</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <ComposedChart data={roiProjectionData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis yAxisId="left" tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`} />
                  <YAxis yAxisId="right" orientation="right" tickFormatter={(value) => `${value.toFixed(0)}%`} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Area yAxisId="left" type="monotone" dataKey="propertyValue" stackId="1" stroke="#8884d8" fill="#8884d8" name="Property Value" />
                  <Area yAxisId="left" type="monotone" dataKey="cumulativeCashFlow" stackId="1" stroke="#82ca9d" fill="#82ca9d" name="Cash Flow" />
                  <Line yAxisId="right" type="monotone" dataKey="roi" stroke="#ff7300" strokeWidth={2} name="Total ROI %" />
                </ComposedChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Total Return Projection */}
          <Card>
            <CardHeader>
              <CardTitle>Total Return Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={roiProjectionData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="totalReturn" stroke="#8884d8" fill="#8884d8" name="Total Return" />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="python" className="space-y-4">
          {/* Python-generated Matplotlib/Seaborn charts */}
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {pythonCharts.investment && (
                <Card>
                  <CardHeader>
                    <CardTitle>Advanced Investment Analysis</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <img
                      src={`data:image/png;base64,${pythonCharts.investment}`}
                      alt="Investment Analysis"
                      className="w-full h-auto"
                    />
                  </CardContent>
                </Card>
              )}

              {pythonCharts.market && (
                <Card>
                  <CardHeader>
                    <CardTitle>Market Overview Visualization</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <img
                      src={`data:image/png;base64,${pythonCharts.market}`}
                      alt="Market Overview"
                      className="w-full h-auto"
                    />
                  </CardContent>
                </Card>
              )}

              {pythonCharts.sales && (
                <Card>
                  <CardHeader>
                    <CardTitle>Sales Trend Analysis</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <img
                      src={`data:image/png;base64,${pythonCharts.sales}`}
                      alt="Sales Trends"
                      className="w-full h-auto"
                    />
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Summary Statistics */}
      <Card>
        <CardHeader>
          <CardTitle>Key Investment Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">Cap Rate</p>
              <p className="text-2xl font-bold text-green-600">
                {formatPercentage(calculations?.capRate || 0)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Monthly Cash Flow</p>
              <p className="text-2xl font-bold text-blue-600">
                {formatCurrency(calculations?.cashFlow || 0)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">ROI</p>
              <p className="text-2xl font-bold text-purple-600">
                {formatPercentage(calculations?.roi || 0)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">GRM</p>
              <p className="text-2xl font-bold text-orange-600">
                {(calculations?.grossRentMultiplier || 0).toFixed(2)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PropertyCharts;