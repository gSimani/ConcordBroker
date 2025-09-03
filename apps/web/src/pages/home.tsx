import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { 
  Search, 
  TrendingUp, 
  Building, 
  BarChart3,
  ArrowRight,
  DollarSign,
  Users,
  Activity
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { api } from '@/api/client'
import { formatCurrency } from '@/lib/constants'

export default function HomePage() {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: api.getDetailedHealth,
    refetchInterval: 60000, // Refresh every minute
  })
  
  const { data: topOpportunities } = useQuery({
    queryKey: ['top-opportunities'],
    queryFn: () => api.getTopOpportunities(),
  })
  
  const { data: recentActivity } = useQuery({
    queryKey: ['recent-activity'],
    queryFn: () => api.getRecentActivity(7),
  })
  
  return (
    <div className="container mx-auto py-8 space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold tracking-tight">
          ConcordBroker
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Intelligent real estate investment property acquisition for Broward County
        </p>
        <div className="flex justify-center gap-4">
          <Button size="lg" asChild>
            <Link to="/search">
              <Search className="mr-2 h-5 w-5" />
              Search Properties
            </Link>
          </Button>
          <Button size="lg" variant="outline" asChild>
            <Link to="/analytics">
              <BarChart3 className="mr-2 h-5 w-5" />
              View Analytics
            </Link>
          </Button>
        </div>
      </div>
      
      {/* System Status */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Status</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {health?.status === 'healthy' ? '✅ Healthy' : '⚠️ Degraded'}
            </div>
            <p className="text-xs text-muted-foreground">
              All systems operational
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Properties</CardTitle>
            <Building className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {health?.components?.database?.parcels_count?.toLocaleString() || '0'}
            </div>
            <p className="text-xs text-muted-foreground">
              Total properties tracked
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Entities</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {health?.components?.data_sources?.sunbiz?.records?.toLocaleString() || '0'}
            </div>
            <p className="text-xs text-muted-foreground">
              Corporate entities
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Last Sync</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {health?.components?.data_sources?.sunbiz?.last_sync 
                ? new Date(health.components.data_sources.sunbiz.last_sync).toLocaleDateString()
                : 'Never'}
            </div>
            <p className="text-xs text-muted-foreground">
              Data freshness
            </p>
          </CardContent>
        </Card>
      </div>
      
      {/* Top Opportunities */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Top Investment Opportunities
            </CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <Link to="/search?min_score=70">
                View All
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {topOpportunities && topOpportunities.length > 0 ? (
            <div className="space-y-4">
              {topOpportunities.slice(0, 5).map((property: any) => (
                <div key={property.folio} className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent">
                  <div className="space-y-1">
                    <Link
                      to={`/property/${property.folio}`}
                      className="font-medium text-primary hover:underline"
                    >
                      {property.situs_addr || property.folio}
                    </Link>
                    <div className="text-sm text-muted-foreground">
                      {property.city} • Score: {property.score?.toFixed(0)}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium">
                      {formatCurrency(property.just_value)}
                    </div>
                    {property.value_gap > 0 && (
                      <div className="text-sm text-green-600">
                        Gap: {formatCurrency(property.value_gap)}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-muted-foreground py-8">
              No opportunities found. Data may still be loading.
            </p>
          )}
        </CardContent>
      </Card>
      
      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Recent Market Activity
            </CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <Link to="/analytics">
                View Analytics
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {recentActivity && recentActivity.length > 0 ? (
            <div className="space-y-2">
              {recentActivity.slice(0, 10).map((activity: any, idx: number) => (
                <div key={idx} className="flex items-center justify-between py-2 border-b last:border-0">
                  <div className="flex items-center gap-2">
                    {activity.activity_type === 'sale' ? (
                      <DollarSign className="h-4 w-4 text-green-600" />
                    ) : (
                      <FileText className="h-4 w-4 text-blue-600" />
                    )}
                    <div>
                      <Link
                        to={`/property/${activity.folio}`}
                        className="text-sm font-medium hover:underline"
                      >
                        {activity.situs_addr || activity.folio}
                      </Link>
                      <div className="text-xs text-muted-foreground">
                        {activity.city} • {activity.activity_type}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium">
                      {activity.value ? formatCurrency(activity.value) : 'N/A'}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {new Date(activity.activity_date).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-muted-foreground py-8">
              No recent activity found.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}