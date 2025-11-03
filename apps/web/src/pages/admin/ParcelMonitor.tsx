import { useState, useEffect } from 'react'
import { supabase } from '@/lib/supabase'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { 
  Download, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle, 
  Clock,
  Database,
  Activity,
  FileDown
} from 'lucide-react'

interface MonitoringAgent {
  id: number
  agent_name: string
  agent_type: string
  enabled: boolean
  last_run: string
  next_run: string
  check_frequency_hours: number
}

interface DataSource {
  id: number
  source_url: string
  county: string
  file_name: string
  file_size: number
  last_checked: string
  last_downloaded: string
  status: string
  change_detected: boolean
}

interface UpdateHistory {
  id: number
  county: string
  update_type: string
  records_added: number
  records_updated: number
  success: boolean
  update_date: string
}

export default function ParcelMonitor() {
  const [agents, setAgents] = useState<MonitoringAgent[]>([])
  const [dataSources, setDataSources] = useState<DataSource[]>([])
  const [updateHistory, setUpdateHistory] = useState<UpdateHistory[]>([])
  const [statistics, setStatistics] = useState<any>({})
  const [isRefreshing, setIsRefreshing] = useState(false)

  useEffect(() => {
    fetchMonitoringData()
    const interval = setInterval(fetchMonitoringData, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchMonitoringData = async () => {
    try {
      // Fetch monitoring agents
      const { data: agentsData } = await supabase
        .from('monitoring_agents')
        .select('*')
        .order('agent_name')

      if (agentsData) setAgents(agentsData)

      // Fetch data sources with changes
      const { data: sourcesData } = await supabase
        .from('data_source_monitor')
        .select('*')
        .eq('change_detected', true)
        .order('county')
        .limit(20)

      if (sourcesData) setDataSources(sourcesData)

      // Fetch recent update history
      const { data: historyData } = await supabase
        .from('parcel_update_history')
        .select('*')
        .order('update_date', { ascending: false })
        .limit(10)

      if (historyData) setUpdateHistory(historyData)

      // Fetch statistics
      const { count: parcelsCount } = await supabase
        .from('florida_parcels')
        .select('county', { count: 'exact', head: true })

      const { data: qualityData } = await supabase
        .from('data_quality_dashboard')
        .select('*')

      setStatistics({
        totalParcels: parcelsCount || 0,
        counties: qualityData?.length || 0,
        lastUpdate: new Date().toISOString()
      })
    } catch (error) {
      console.error('Error fetching monitoring data:', error)
    }
  }

  const triggerSync = async (county?: string) => {
    setIsRefreshing(true)
    try {
      const response = await fetch('/api/trigger-parcel-sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ county })
      })
      
      if (response.ok) {
        await fetchMonitoringData()
      }
    } catch (error) {
      console.error('Error triggering sync:', error)
    } finally {
      setIsRefreshing(false)
    }
  }

  const toggleAgent = async (agent: MonitoringAgent) => {
    await supabase
      .from('monitoring_agents')
      .update({ enabled: !agent.enabled })
      .eq('id', agent.id)
    
    await fetchMonitoringData()
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Florida Parcel Data Monitor
        </h1>
        <p className="text-gray-600">
          Real-time monitoring of Florida Revenue property data updates
        </p>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Total Parcels
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center">
              <Database className="h-4 w-4 text-blue-600 mr-2" />
              <span className="text-2xl font-bold">
                {statistics.totalParcels?.toLocaleString() || 0}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Counties Monitored
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center">
              <Activity className="h-4 w-4 text-green-600 mr-2" />
              <span className="text-2xl font-bold">{statistics.counties || 0}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Updates Available
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center">
              <FileDown className="h-4 w-4 text-orange-600 mr-2" />
              <span className="text-2xl font-bold">{dataSources.length}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Last Check
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center">
              <Clock className="h-4 w-4 text-purple-600 mr-2" />
              <span className="text-sm">
                {new Date(statistics.lastUpdate).toLocaleTimeString()}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Monitoring Agents */}
      <Card className="mb-8">
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle>Monitoring Agents</CardTitle>
            <Button 
              onClick={() => fetchMonitoringData()} 
              size="sm"
              disabled={isRefreshing}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {agents.map(agent => (
              <div key={agent.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  {agent.enabled ? (
                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-gray-400" />
                  )}
                  <div>
                    <p className="font-medium">{agent.agent_name}</p>
                    <p className="text-sm text-gray-600">
                      Type: {agent.agent_type} • Every {agent.check_frequency_hours}h
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant={agent.enabled ? "default" : "secondary"}>
                    {agent.enabled ? 'Active' : 'Disabled'}
                  </Badge>
                  <Button
                    onClick={() => toggleAgent(agent)}
                    size="sm"
                    variant="outline"
                  >
                    {agent.enabled ? 'Disable' : 'Enable'}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Updates Available */}
      {dataSources.length > 0 && (
        <Card className="mb-8">
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle>Updates Available</CardTitle>
              <Button onClick={() => triggerSync()} disabled={isRefreshing}>
                <Download className="h-4 w-4 mr-2" />
                Download All Updates
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {dataSources.map(source => (
                <div key={source.id} className="flex items-center justify-between p-2 bg-orange-50 rounded">
                  <div>
                    <p className="font-medium">{source.county} - {source.file_name}</p>
                    <p className="text-sm text-gray-600">
                      Last checked: {new Date(source.last_checked).toLocaleDateString()}
                    </p>
                  </div>
                  <Button
                    onClick={() => triggerSync(source.county)}
                    size="sm"
                    variant="outline"
                  >
                    Download
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Update History */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Updates</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {updateHistory.map(update => (
              <div key={update.id} className="flex items-center justify-between p-2 border-b last:border-0">
                <div className="flex items-center space-x-2">
                  {update.success ? (
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-red-600" />
                  )}
                  <div>
                    <p className="font-medium">{update.county}</p>
                    <p className="text-sm text-gray-600">
                      {update.update_type} • {update.records_added} added, {update.records_updated} updated
                    </p>
                  </div>
                </div>
                <span className="text-sm text-gray-500">
                  {new Date(update.update_date).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}