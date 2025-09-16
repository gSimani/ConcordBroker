import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  TrendingUp, 
  TrendingDown, 
  MapPin, 
  Building, 
  Home, 
  DollarSign,
  Users,
  Calendar,
  FileText,
  AlertTriangle,
  RefreshCw,
  Search,
  Filter
} from 'lucide-react';
import { useNavigate, Link } from 'react-router-dom';

interface DashboardStats {
  totalProperties: number;
  totalValue: number;
  averageValue: number;
  recentSales: number;
  highValueCount: number;
  watchedCount: number;
}

interface CityStats {
  city: string;
  propertyCount: number;
  averageValue: number;
  totalValue: number;
  percentChange: number;
}

interface PropertyTypeStats {
  type: string;
  count: number;
  percentage: number;
  averageValue: number;
}

interface RecentSale {
  id: number;
  address: string;
  city: string;
  saleDate: string;
  salePrice: number;
  propertyType: string;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [cityStats, setCityStats] = useState<CityStats[]>([]);
  const [typeStats, setTypeStats] = useState<PropertyTypeStats[]>([]);
  const [recentSales, setRecentSales] = useState<RecentSale[]>([]);
  const [loading, setLoading] = useState(true);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [statsRes, cityRes, typeRes, salesRes] = await Promise.all([
        fetch('/api/properties/stats/overview'),
        fetch('/api/properties/stats/by-city'),
        fetch('/api/properties/stats/by-type'),
        fetch('/api/properties/recent-sales?days=30&limit=10')
      ]);

      if (statsRes.ok) setStats(await statsRes.json());
      if (cityRes.ok) setCityStats(await cityRes.json());
      if (typeRes.ok) setTypeStats(await typeRes.json());
      if (salesRes.ok) setRecentSales(await salesRes.json());
      
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('en-US').format(value);
  };

  const quickActions = [
    {
      title: 'Search Properties',
      description: 'Find properties by address or owner',
      icon: Search,
      action: () => navigate('/properties'),
      color: 'bg-blue-500'
    },
    {
      title: 'High Value Properties',
      description: 'Properties over $1M',
      icon: TrendingUp,
      action: () => navigate('/properties?min_value=1000000'),
      color: 'bg-green-500'
    },
    {
      title: 'Recent Sales',
      description: 'Properties sold in last 30 days',
      icon: Calendar,
      action: () => navigate('/analytics?view=recent-sales'),
      color: 'bg-purple-500'
    },
    {
      title: 'Fort Lauderdale',
      description: 'Browse Fort Lauderdale properties',
      icon: MapPin,
      action: () => navigate('/properties?city=Fort Lauderdale'),
      color: 'bg-orange-500'
    }
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
          <h2 className="text-lg font-semibold mb-2">Loading Dashboard</h2>
          <p className="text-gray-600">Fetching property data...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Property Dashboard</h1>
              <p className="text-gray-600 mt-1">
                Broward County Property Intelligence
              </p>
            </div>
            
            <div className="flex items-center space-x-3">
              <Badge variant="outline" className="px-3 py-1">
                <MapPin className="w-3 h-3 mr-1" />
                Broward County, FL
              </Badge>
              <Button 
                variant="outline" 
                onClick={loadDashboardData}
                disabled={loading}
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Overview Stats */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Total Properties</p>
                    <p className="text-3xl font-bold">{formatNumber(stats.totalProperties)}</p>
                  </div>
                  <Building className="w-8 h-8 text-blue-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Total Value</p>
                    <p className="text-3xl font-bold">{formatCurrency(stats.totalValue / 1000000)}M</p>
                  </div>
                  <DollarSign className="w-8 h-8 text-green-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Average Value</p>
                    <p className="text-3xl font-bold">{formatCurrency(stats.averageValue)}</p>
                  </div>
                  <TrendingUp className="w-8 h-8 text-purple-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Recent Sales</p>
                    <p className="text-3xl font-bold">{formatNumber(stats.recentSales)}</p>
                    <p className="text-xs text-gray-500">Last 30 days</p>
                  </div>
                  <Calendar className="w-8 h-8 text-orange-500" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {quickActions.map((action, index) => {
              const Icon = action.icon;
              return (
                <Card 
                  key={index}
                  className="cursor-pointer hover:shadow-md transition-shadow"
                  onClick={action.action}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start space-x-3">
                      <div className={`p-2 rounded-lg ${action.color}`}>
                        <Icon className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <h3 className="font-medium text-sm">{action.title}</h3>
                        <p className="text-xs text-gray-600">{action.description}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>

        {/* Main Content Tabs */}
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid grid-cols-4 w-full max-w-md">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="cities">Cities</TabsTrigger>
            <TabsTrigger value="types">Types</TabsTrigger>
            <TabsTrigger value="sales">Sales</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Top Cities */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <MapPin className="w-5 h-5 mr-2" />
                    Top Cities by Property Count
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {cityStats.slice(0, 5).map((city, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <h4 className="font-medium">{city.city}</h4>
                          <p className="text-sm text-gray-600">
                            {formatNumber(city.propertyCount)} properties
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="font-medium">{formatCurrency(city.averageValue)}</p>
                          <p className="text-xs text-gray-500">avg value</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Property Types */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Building className="w-5 h-5 mr-2" />
                    Property Types
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {typeStats.map((type, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <div className={`w-3 h-3 rounded-full ${
                            type.type === 'Residential' ? 'bg-blue-500' :
                            type.type === 'Commercial' ? 'bg-green-500' :
                            type.type === 'Industrial' ? 'bg-purple-500' :
                            'bg-gray-500'
                          }`} />
                          <div>
                            <h4 className="font-medium">{type.type}</h4>
                            <p className="text-sm text-gray-600">{type.percentage.toFixed(1)}%</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-medium">{formatNumber(type.count)}</p>
                          <p className="text-xs text-gray-500">properties</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="cities" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>City Statistics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-2">City</th>
                        <th className="text-right py-2">Properties</th>
                        <th className="text-right py-2">Total Value</th>
                        <th className="text-right py-2">Average Value</th>
                        <th className="text-center py-2">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {cityStats.map((city, index) => (
                        <tr key={index} className="border-b hover:bg-gray-50">
                          <td className="py-3 font-medium">{city.city}</td>
                          <td className="py-3 text-right">{formatNumber(city.propertyCount)}</td>
                          <td className="py-3 text-right">{formatCurrency(city.totalValue)}</td>
                          <td className="py-3 text-right">{formatCurrency(city.averageValue)}</td>
                          <td className="py-3 text-center">
                            <Link href={`/properties?city=${encodeURIComponent(city.city)}`}>
                              <Button variant="outline" size="sm">
                                View Properties
                              </Button>
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="types" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {typeStats.map((type, index) => (
                <Card key={index}>
                  <CardContent className="p-6 text-center">
                    <div className={`w-12 h-12 mx-auto mb-4 rounded-full flex items-center justify-center ${
                      type.type === 'Residential' ? 'bg-blue-100 text-blue-600' :
                      type.type === 'Commercial' ? 'bg-green-100 text-green-600' :
                      type.type === 'Industrial' ? 'bg-purple-100 text-purple-600' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {type.type === 'Residential' ? <Home className="w-6 h-6" /> :
                       type.type === 'Commercial' ? <Building className="w-6 h-6" /> :
                       <Building className="w-6 h-6" />}
                    </div>
                    <h3 className="font-semibold mb-1">{type.type}</h3>
                    <p className="text-2xl font-bold mb-1">{formatNumber(type.count)}</p>
                    <p className="text-sm text-gray-600 mb-3">{type.percentage.toFixed(1)}% of total</p>
                    <Link href={`/properties?property_type=${encodeURIComponent(type.type)}`}>
                      <Button variant="outline" size="sm" className="w-full">
                        Explore
                      </Button>
                    </Link>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="sales" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="flex items-center">
                    <Calendar className="w-5 h-5 mr-2" />
                    Recent Sales
                  </span>
                  <Link href="/analytics?view=recent-sales">
                    <Button variant="outline" size="sm">
                      View All
                    </Button>
                  </Link>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {recentSales.map((sale, index) => (
                    <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                      <div className="flex-1">
                        <h4 className="font-medium">{sale.address}</h4>
                        <p className="text-sm text-gray-600">{sale.city}</p>
                        <div className="flex items-center space-x-2 mt-1">
                          <Badge variant="outline" className="text-xs">
                            {sale.propertyType}
                          </Badge>
                          <span className="text-xs text-gray-500">
                            {new Date(sale.saleDate).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-lg">{formatCurrency(sale.salePrice)}</p>
                        <Link href={`/properties/${sale.id}`}>
                          <Button variant="ghost" size="sm" className="text-xs">
                            View Details
                          </Button>
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

      </div>
    </div>
  );
}