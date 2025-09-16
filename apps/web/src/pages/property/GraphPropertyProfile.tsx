import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import GraphVisualization from '@/components/graph/GraphVisualization';
import GraphTimeline from '@/components/graph/GraphTimeline';
import GraphInsights from '@/components/graph/GraphInsights';
import PropertyProfile from './PropertyProfile';
import { 
  Network, 
  Clock, 
  Lightbulb, 
  Home,
  Share2,
  Download,
  RefreshCw
} from 'lucide-react';

interface GraphPropertyProfileProps {
  parcelId?: string;
}

export const GraphPropertyProfile: React.FC<GraphPropertyProfileProps> = () => {
  const { parcelId } = useParams<{ parcelId: string }>();
  const [loading, setLoading] = useState(true);
  const [graphData, setGraphData] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [graphEnabled, setGraphEnabled] = useState(false);

  useEffect(() => {
    checkGraphStatus();
    if (parcelId) {
      fetchGraphData();
    }
  }, [parcelId]);

  const checkGraphStatus = async () => {
    try {
      const response = await fetch('/api/graph/health');
      const data = await response.json();
      setGraphEnabled(data.status === 'healthy');
    } catch (error) {
      console.error('Graph service not available:', error);
      setGraphEnabled(false);
    }
  };

  const fetchGraphData = async () => {
    if (!parcelId) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/api/graph/property/${parcelId}/full`);
      const data = await response.json();
      setGraphData(data);
    } catch (error) {
      console.error('Error fetching graph data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExportGraph = async () => {
    if (!parcelId) return;
    
    try {
      const response = await fetch(`/api/graph/property/${parcelId}/export`);
      const data = await response.blob();
      
      const url = URL.createObjectURL(data);
      const link = document.createElement('a');
      link.href = url;
      link.download = `property-${parcelId}-graph-${Date.now()}.json`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting graph:', error);
    }
  };

  const handleShareGraph = async () => {
    if (!parcelId) return;
    
    const shareUrl = `${window.location.origin}/property/${parcelId}/graph`;
    
    if (navigator.share) {
      try {
        await navigator.share({
          title: `Property Graph - ${parcelId}`,
          text: 'Check out this property relationship graph',
          url: shareUrl
        });
      } catch (error) {
        console.error('Error sharing:', error);
      }
    } else {
      // Fallback - copy to clipboard
      navigator.clipboard.writeText(shareUrl);
      alert('Link copied to clipboard!');
    }
  };

  if (!graphEnabled) {
    // Fallback to regular property profile if graph is not enabled
    return <PropertyProfile />;
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Property Intelligence</h1>
          <p className="text-gray-600">Parcel ID: {parcelId}</p>
        </div>
        
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchGraphData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" onClick={handleShareGraph}>
            <Share2 className="h-4 w-4 mr-2" />
            Share
          </Button>
          <Button variant="outline" onClick={handleExportGraph}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Graph Status */}
      {graphData?.metadata && (
        <Card className="p-4">
          <div className="flex justify-between items-center">
            <div className="flex gap-6">
              <div>
                <span className="text-sm text-gray-600">Total Nodes</span>
                <p className="text-xl font-semibold">{graphData.metadata.totalNodes}</p>
              </div>
              <div>
                <span className="text-sm text-gray-600">Relationships</span>
                <p className="text-xl font-semibold">{graphData.metadata.totalRelationships}</p>
              </div>
              <div>
                <span className="text-sm text-gray-600">Data Sources</span>
                <p className="text-xl font-semibold">{graphData.metadata.sources?.length || 0}</p>
              </div>
            </div>
            
            <Badge variant={graphData.metadata.lastUpdated ? 'default' : 'secondary'}>
              {graphData.metadata.lastUpdated 
                ? `Updated ${new Date(graphData.metadata.lastUpdated).toLocaleDateString()}`
                : 'Real-time data'}
            </Badge>
          </div>
        </Card>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid grid-cols-4 w-full max-w-2xl">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <Home className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="network" className="flex items-center gap-2">
            <Network className="h-4 w-4" />
            Network
          </TabsTrigger>
          <TabsTrigger value="timeline" className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Timeline
          </TabsTrigger>
          <TabsTrigger value="insights" className="flex items-center gap-2">
            <Lightbulb className="h-4 w-4" />
            Insights
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* Standard property profile with graph enhancements */}
          <PropertyProfile />
        </TabsContent>

        <TabsContent value="network" className="space-y-4">
          <Card className="p-6">
            <div className="mb-4">
              <h2 className="text-xl font-semibold mb-2">Property Network Graph</h2>
              <p className="text-gray-600">
                Interactive visualization of property relationships, ownership history, and connected entities
              </p>
            </div>
            
            <GraphVisualization
              parcelId={parcelId}
              data={graphData}
              height={600}
              showControls={true}
              enablePhysics={true}
              onNodeClick={(node) => {
                console.log('Node clicked:', node);
                // Handle node click - could navigate to related property
                if (node.type === 'property' && node.id !== parcelId) {
                  window.location.href = `/property/${node.id}/graph`;
                }
              }}
              onLinkClick={(link) => {
                console.log('Link clicked:', link);
                // Handle link click - could show relationship details
              }}
            />
          </Card>

          {/* Network Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="p-4">
              <h3 className="font-semibold mb-2">Ownership Network</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Direct Connections</span>
                  <span className="font-medium">{graphData?.stats?.directConnections || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Indirect Connections</span>
                  <span className="font-medium">{graphData?.stats?.indirectConnections || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Network Depth</span>
                  <span className="font-medium">{graphData?.stats?.maxDepth || 0}</span>
                </div>
              </div>
            </Card>

            <Card className="p-4">
              <h3 className="font-semibold mb-2">Entity Types</h3>
              <div className="space-y-2">
                {graphData?.stats?.entityTypes?.map((type: any) => (
                  <div key={type.name} className="flex justify-between">
                    <span className="text-sm text-gray-600">{type.name}</span>
                    <span className="font-medium">{type.count}</span>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="p-4">
              <h3 className="font-semibold mb-2">Relationship Types</h3>
              <div className="space-y-2">
                {graphData?.stats?.relationshipTypes?.map((type: any) => (
                  <div key={type.name} className="flex justify-between">
                    <span className="text-sm text-gray-600">{type.name}</span>
                    <span className="font-medium">{type.count}</span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="timeline" className="space-y-4">
          <GraphTimeline
            parcelId={parcelId!}
            events={graphData?.timeline}
            onEventClick={(event) => {
              console.log('Timeline event clicked:', event);
              // Handle event click - could show detailed view
            }}
          />
        </TabsContent>

        <TabsContent value="insights" className="space-y-4">
          <GraphInsights
            parcelId={parcelId}
            insights={graphData?.insights}
            patterns={graphData?.patterns}
            onInsightClick={(insight) => {
              console.log('Insight clicked:', insight);
              // Handle insight click - could trigger action
            }}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default GraphPropertyProfile;