import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { supabase } from '@/lib/supabase';
import {
  Activity,
  Brain,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock,
  MessageSquare,
  BarChart3,
  Settings,
  RefreshCw,
  Zap,
  Building2,
  FileText,
  DollarSign,
  Home,
  Hammer,
  Network
} from 'lucide-react';

interface Agent {
  agent_id: string;
  agent_name: string;
  status: 'online' | 'offline' | 'error';
  last_heartbeat: string;
  capabilities: string[];
  metadata?: any;
}

interface AgentMetric {
  id: string;
  agent_id: string;
  metric_type: string;
  metric_name: string;
  metric_value: number;
  metadata?: any;
  created_at: string;
}

interface AgentAlert {
  id: string;
  agent_id: string;
  alert_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  status: 'active' | 'acknowledged' | 'resolved';
  created_at: string;
}

interface AgentMessage {
  id: string;
  from_agent_id: string;
  to_agent_id: string;
  message_type: string;
  payload: any;
  priority: number;
  status: string;
  created_at: string;
}

interface ChainOfThoughtStep {
  thought: string;
  timestamp: string;
  agent_name: string;
}

const AgentDashboard: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [metrics, setMetrics] = useState<AgentMetric[]>([]);
  const [alerts, setAlerts] = useState<AgentAlert[]>([]);
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [chainOfThought, setChainOfThought] = useState<ChainOfThoughtStep[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch all agent data
  const fetchAgentData = async () => {
    try {
      // Fetch agents
      const { data: agentsData, error: agentsError } = await supabase
        .from('agent_registry')
        .select('*')
        .order('last_heartbeat', { ascending: false });

      if (agentsError) throw agentsError;
      setAgents(agentsData || []);

      // Fetch recent metrics
      const { data: metricsData, error: metricsError } = await supabase
        .from('agent_metrics')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(100);

      if (metricsError) throw metricsError;
      setMetrics(metricsData || []);

      // Fetch active alerts
      const { data: alertsData, error: alertsError } = await supabase
        .from('agent_alerts')
        .select('*')
        .eq('status', 'active')
        .order('created_at', { ascending: false })
        .limit(50);

      if (alertsError) throw alertsError;
      setAlerts(alertsData || []);

      // Fetch recent messages
      const { data: messagesData, error: messagesError } = await supabase
        .from('agent_messages')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(50);

      if (messagesError) throw messagesError;
      setMessages(messagesData || []);

      // Extract Chain-of-Thought steps
      const cotSteps: ChainOfThoughtStep[] = (metricsData || [])
        .filter(m => m.metric_type === 'reasoning' && m.metadata?.thought)
        .map(m => ({
          thought: m.metadata.thought,
          timestamp: m.created_at,
          agent_name: agents.find(a => a.agent_id === m.agent_id)?.agent_name || m.agent_id
        }))
        .slice(0, 50);

      setChainOfThought(cotSteps);
      setLastUpdate(new Date());
      setLoading(false);
    } catch (error) {
      console.error('Error fetching agent data:', error);
      setLoading(false);
    }
  };

  // Auto-refresh every 10 seconds
  useEffect(() => {
    fetchAgentData();

    if (autoRefresh) {
      const interval = setInterval(fetchAgentData, 10000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  // Get agent icon
  const getAgentIcon = (agentName: string) => {
    if (agentName.includes('Property Data')) return <Home className="h-5 w-5" />;
    if (agentName.includes('Tax Deed')) return <DollarSign className="h-5 w-5" />;
    if (agentName.includes('Sales Activity')) return <BarChart3 className="h-5 w-5" />;
    if (agentName.includes('Market Analysis')) return <TrendingUp className="h-5 w-5" />;
    if (agentName.includes('Foreclosure')) return <AlertTriangle className="h-5 w-5" />;
    if (agentName.includes('Permit')) return <Hammer className="h-5 w-5" />;
    if (agentName.includes('Entity')) return <Building2 className="h-5 w-5" />;
    if (agentName.includes('Pattern')) return <Brain className="h-5 w-5" />;
    if (agentName.includes('Predictor')) return <TrendingUp className="h-5 w-5" />;
    if (agentName.includes('Orchestrator')) return <Network className="h-5 w-5" />;
    return <Activity className="h-5 w-5" />;
  };

  // Get status badge
  const getStatusBadge = (status: string, lastHeartbeat: string) => {
    const heartbeatTime = new Date(lastHeartbeat).getTime();
    const now = Date.now();
    const ageMinutes = (now - heartbeatTime) / 1000 / 60;

    if (ageMinutes < 2) {
      return <Badge className="bg-green-500">Online</Badge>;
    } else if (ageMinutes < 5) {
      return <Badge className="bg-yellow-500">Idle</Badge>;
    } else {
      return <Badge className="bg-red-500">Offline</Badge>;
    }
  };

  // Get severity badge
  const getSeverityBadge = (severity: string) => {
    const colors = {
      low: 'bg-blue-500',
      medium: 'bg-yellow-500',
      high: 'bg-orange-500',
      critical: 'bg-red-500'
    };
    return <Badge className={colors[severity as keyof typeof colors]}>{severity.toUpperCase()}</Badge>;
  };

  // Calculate system health
  const calculateSystemHealth = () => {
    const onlineAgents = agents.filter(a => {
      const ageMinutes = (Date.now() - new Date(a.last_heartbeat).getTime()) / 1000 / 60;
      return ageMinutes < 2;
    }).length;

    const totalAgents = agents.length;
    const healthPercent = totalAgents > 0 ? (onlineAgents / totalAgents) * 100 : 0;

    return {
      percent: Math.round(healthPercent),
      online: onlineAgents,
      total: totalAgents
    };
  };

  const systemHealth = calculateSystemHealth();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <RefreshCw className="h-12 w-12 animate-spin mx-auto mb-4" />
          <p className="text-lg">Loading Agent Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Brain className="h-8 w-8" />
            Autonomous Agent System
          </h1>
          <p className="text-muted-foreground">
            Real-time monitoring • Chain-of-Thought • Chain-of-Agents
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-sm text-muted-foreground">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            {autoRefresh ? 'Auto' : 'Manual'}
          </Button>
          <Button onClick={fetchAgentData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* System Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemHealth.percent}%</div>
            <p className="text-xs text-muted-foreground">
              {systemHealth.online} of {systemHealth.total} agents online
            </p>
            <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full ${
                  systemHealth.percent > 80 ? 'bg-green-500' :
                  systemHealth.percent > 50 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${systemHealth.percent}%` }}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Alerts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{alerts.length}</div>
            <p className="text-xs text-muted-foreground">
              {alerts.filter(a => a.severity === 'high' || a.severity === 'critical').length} high priority
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Chain-of-Thought</CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{chainOfThought.length}</div>
            <p className="text-xs text-muted-foreground">
              Recent reasoning steps
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Agent Messages</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{messages.length}</div>
            <p className="text-xs text-muted-foreground">
              Inter-agent communication
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="agents" className="space-y-4">
        <TabsList>
          <TabsTrigger value="agents">
            <Network className="h-4 w-4 mr-2" />
            Agents
          </TabsTrigger>
          <TabsTrigger value="thoughts">
            <Brain className="h-4 w-4 mr-2" />
            Chain-of-Thought
          </TabsTrigger>
          <TabsTrigger value="alerts">
            <AlertTriangle className="h-4 w-4 mr-2" />
            Alerts
          </TabsTrigger>
          <TabsTrigger value="messages">
            <MessageSquare className="h-4 w-4 mr-2" />
            Messages
          </TabsTrigger>
          <TabsTrigger value="metrics">
            <BarChart3 className="h-4 w-4 mr-2" />
            Metrics
          </TabsTrigger>
        </TabsList>

        {/* Agents Tab */}
        <TabsContent value="agents" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.map(agent => (
              <Card key={agent.agent_id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      {getAgentIcon(agent.agent_name)}
                      <div>
                        <CardTitle className="text-base">{agent.agent_name}</CardTitle>
                        <p className="text-xs text-muted-foreground">{agent.agent_id}</p>
                      </div>
                    </div>
                    {getStatusBadge(agent.status, agent.last_heartbeat)}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex items-center text-sm">
                      <Clock className="h-4 w-4 mr-2" />
                      <span className="text-muted-foreground">
                        {new Date(agent.last_heartbeat).toLocaleTimeString()}
                      </span>
                    </div>
                    {agent.capabilities && agent.capabilities.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {agent.capabilities.map((cap, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs">
                            {cap}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Chain-of-Thought Tab */}
        <TabsContent value="thoughts">
          <Card>
            <CardHeader>
              <CardTitle>Chain-of-Thought Timeline</CardTitle>
              <p className="text-sm text-muted-foreground">
                Real-time reasoning steps from all agents
              </p>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <div className="space-y-4">
                  {chainOfThought.map((step, idx) => (
                    <div key={idx} className="border-l-2 border-blue-500 pl-4 pb-4">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="outline">{step.agent_name}</Badge>
                        <span className="text-xs text-muted-foreground">
                          {new Date(step.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <p className="text-sm">{step.thought}</p>
                    </div>
                  ))}
                  {chainOfThought.length === 0 && (
                    <p className="text-center text-muted-foreground py-8">
                      No Chain-of-Thought steps yet. Agents will start thinking soon...
                    </p>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Alerts Tab */}
        <TabsContent value="alerts">
          <Card>
            <CardHeader>
              <CardTitle>Active Alerts</CardTitle>
              <p className="text-sm text-muted-foreground">
                Autonomous alerts generated by agents
              </p>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <div className="space-y-4">
                  {alerts.map(alert => (
                    <div key={alert.id} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          {getSeverityBadge(alert.severity)}
                          <Badge variant="outline">{alert.alert_type}</Badge>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {new Date(alert.created_at).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-sm mb-2">{alert.message}</p>
                      <p className="text-xs text-muted-foreground">
                        Agent: {agents.find(a => a.agent_id === alert.agent_id)?.agent_name || alert.agent_id}
                      </p>
                    </div>
                  ))}
                  {alerts.length === 0 && (
                    <p className="text-center text-muted-foreground py-8">
                      <CheckCircle className="h-12 w-12 mx-auto mb-2" />
                      No active alerts. All systems nominal.
                    </p>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Messages Tab */}
        <TabsContent value="messages">
          <Card>
            <CardHeader>
              <CardTitle>Chain-of-Agents Messages</CardTitle>
              <p className="text-sm text-muted-foreground">
                Inter-agent communication and coordination
              </p>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <div className="space-y-4">
                  {messages.map(msg => {
                    const fromAgent = agents.find(a => a.agent_id === msg.from_agent_id);
                    const toAgent = agents.find(a => a.agent_id === msg.to_agent_id);

                    return (
                      <div key={msg.id} className="border rounded-lg p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge>{msg.message_type}</Badge>
                          <Badge variant="outline">Priority: {msg.priority}</Badge>
                          <span className="text-xs text-muted-foreground ml-auto">
                            {new Date(msg.created_at).toLocaleString()}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-sm mb-2">
                          <span className="font-medium">{fromAgent?.agent_name || 'Unknown'}</span>
                          <span className="text-muted-foreground">→</span>
                          <span className="font-medium">{toAgent?.agent_name || 'Unknown'}</span>
                        </div>
                        <div className="bg-muted rounded p-2 mt-2">
                          <pre className="text-xs overflow-x-auto">
                            {JSON.stringify(msg.payload, null, 2)}
                          </pre>
                        </div>
                      </div>
                    );
                  })}
                  {messages.length === 0 && (
                    <p className="text-center text-muted-foreground py-8">
                      No inter-agent messages yet. Agents will start coordinating soon...
                    </p>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Metrics Tab */}
        <TabsContent value="metrics">
          <Card>
            <CardHeader>
              <CardTitle>Agent Metrics</CardTitle>
              <p className="text-sm text-muted-foreground">
                Performance measurements and statistics
              </p>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <div className="space-y-4">
                  {metrics
                    .filter(m => m.metric_type !== 'reasoning')
                    .map(metric => {
                      const agent = agents.find(a => a.agent_id === metric.agent_id);

                      return (
                        <div key={metric.id} className="border rounded-lg p-4">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <div className="flex items-center gap-2">
                                <Badge variant="outline">{metric.metric_type}</Badge>
                                <span className="text-sm font-medium">{metric.metric_name}</span>
                              </div>
                              <p className="text-xs text-muted-foreground mt-1">
                                {agent?.agent_name || metric.agent_id}
                              </p>
                            </div>
                            <div className="text-right">
                              <div className="text-2xl font-bold">{metric.metric_value}</div>
                              <span className="text-xs text-muted-foreground">
                                {new Date(metric.created_at).toLocaleTimeString()}
                              </span>
                            </div>
                          </div>
                          {metric.metadata && Object.keys(metric.metadata).length > 0 && (
                            <div className="bg-muted rounded p-2 mt-2">
                              <pre className="text-xs overflow-x-auto">
                                {JSON.stringify(metric.metadata, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  {metrics.filter(m => m.metric_type !== 'reasoning').length === 0 && (
                    <p className="text-center text-muted-foreground py-8">
                      No metrics recorded yet. Agents will start reporting soon...
                    </p>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AgentDashboard;
