import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  ZoomIn, 
  ZoomOut, 
  Maximize2, 
  Filter, 
  Download,
  Play,
  Pause,
  RefreshCw,
  Layers,
  Search
} from 'lucide-react';

interface GraphNode {
  id: string;
  label: string;
  type: 'property' | 'owner' | 'transaction' | 'community' | 'entity';
  properties?: Record<string, any>;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
  type: string;
  properties?: Record<string, any>;
  timestamp?: string;
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
  metadata?: {
    totalNodes: number;
    totalRelationships: number;
    timestamp: string;
  };
}

interface GraphVisualizationProps {
  parcelId?: string;
  data?: GraphData;
  height?: number;
  onNodeClick?: (node: GraphNode) => void;
  onLinkClick?: (link: GraphLink) => void;
  showControls?: boolean;
  enablePhysics?: boolean;
  colorScheme?: 'default' | 'dark' | 'colorful';
}

const nodeColors = {
  property: '#3B82F6',     // blue
  owner: '#10B981',        // green
  transaction: '#F59E0B',  // amber
  community: '#8B5CF6',    // purple
  entity: '#EF4444'        // red
};

const linkColors = {
  owns: '#10B981',
  sold_to: '#F59E0B',
  related_to: '#6B7280',
  part_of: '#8B5CF6',
  transacted: '#EF4444'
};

export const GraphVisualization: React.FC<GraphVisualizationProps> = ({
  parcelId,
  data: initialData,
  height = 600,
  onNodeClick,
  onLinkClick,
  showControls = true,
  enablePhysics = true,
  colorScheme = 'default'
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(initialData || null);
  const [loading, setLoading] = useState(!initialData);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [simulation, setSimulation] = useState<d3.Simulation<GraphNode, GraphLink> | null>(null);
  const [zoom, setZoom] = useState(1);
  const [isPlaying, setIsPlaying] = useState(enablePhysics);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [depthLimit, setDepthLimit] = useState(2);

  // Fetch graph data if parcelId provided
  useEffect(() => {
    if (parcelId && !initialData) {
      fetchGraphData(parcelId);
    }
  }, [parcelId]);

  const fetchGraphData = async (id: string) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/graph/property/${id}/network?depth=${depthLimit}`);
      const data = await response.json();
      setGraphData(data);
    } catch (error) {
      console.error('Error fetching graph data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Initialize D3 visualization
  useEffect(() => {
    if (!graphData || !svgRef.current || !containerRef.current) return;

    const width = containerRef.current.clientWidth;
    const svg = d3.select(svgRef.current);
    
    // Clear previous visualization
    svg.selectAll('*').remove();

    // Create zoom behavior
    const zoomBehavior = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 10])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
        setZoom(event.transform.k);
      });

    svg.call(zoomBehavior);

    // Create main group for transformation
    const g = svg.append('g');

    // Create arrow markers for directed edges
    const defs = svg.append('defs');
    Object.entries(linkColors).forEach(([type, color]) => {
      defs.append('marker')
        .attr('id', `arrow-${type}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 20)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', color);
    });

    // Create force simulation
    const sim = d3.forceSimulation<GraphNode>(graphData.nodes)
      .force('link', d3.forceLink<GraphNode, GraphLink>(graphData.links)
        .id(d => d.id)
        .distance(100))
      .force('charge', d3.forceManyBody().strength(-500))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30));

    if (!isPlaying) {
      sim.stop();
    }

    setSimulation(sim);

    // Create links
    const link = g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(graphData.links)
      .enter().append('line')
      .attr('stroke', d => linkColors[d.type as keyof typeof linkColors] || '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', d => d.type === 'owns' ? 3 : 2)
      .attr('marker-end', d => `url(#arrow-${d.type})`)
      .on('click', (event, d) => {
        event.stopPropagation();
        onLinkClick?.(d);
      });

    // Create link labels
    const linkLabel = g.append('g')
      .attr('class', 'link-labels')
      .selectAll('text')
      .data(graphData.links)
      .enter().append('text')
      .attr('font-size', 10)
      .attr('fill', '#666')
      .text(d => d.type);

    // Create nodes
    const node = g.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(graphData.nodes)
      .enter().append('g')
      .call(d3.drag<SVGGElement, GraphNode>()
        .on('start', dragStarted)
        .on('drag', dragged)
        .on('end', dragEnded));

    // Add circles to nodes
    node.append('circle')
      .attr('r', d => d.type === 'property' ? 12 : 10)
      .attr('fill', d => nodeColors[d.type as keyof typeof nodeColors] || '#999')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .on('click', (event, d) => {
        event.stopPropagation();
        setSelectedNode(d);
        onNodeClick?.(d);
      })
      .on('mouseover', function(event, d) {
        d3.select(this).attr('r', d.type === 'property' ? 15 : 12);
        showTooltip(event, d);
      })
      .on('mouseout', function(event, d) {
        d3.select(this).attr('r', d.type === 'property' ? 12 : 10);
        hideTooltip();
      });

    // Add labels to nodes
    node.append('text')
      .attr('dx', 15)
      .attr('dy', 4)
      .attr('font-size', 12)
      .attr('fill', '#333')
      .text(d => d.label?.substring(0, 20) || d.id);

    // Update positions on simulation tick
    sim.on('tick', () => {
      link
        .attr('x1', d => (d.source as GraphNode).x || 0)
        .attr('y1', d => (d.source as GraphNode).y || 0)
        .attr('x2', d => (d.target as GraphNode).x || 0)
        .attr('y2', d => (d.target as GraphNode).y || 0);

      linkLabel
        .attr('x', d => ((d.source as GraphNode).x! + (d.target as GraphNode).x!) / 2)
        .attr('y', d => ((d.source as GraphNode).y! + (d.target as GraphNode).y!) / 2);

      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    // Drag functions
    function dragStarted(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>) {
      if (!event.active) sim.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragEnded(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>) {
      if (!event.active) sim.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    // Cleanup
    return () => {
      sim.stop();
    };
  }, [graphData, height, isPlaying]);

  // Tooltip functions
  const showTooltip = (event: MouseEvent, node: GraphNode) => {
    const tooltip = d3.select('body').append('div')
      .attr('class', 'graph-tooltip')
      .style('position', 'absolute')
      .style('padding', '10px')
      .style('background', 'rgba(0, 0, 0, 0.8)')
      .style('color', 'white')
      .style('border-radius', '4px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('opacity', 0);

    let content = `<strong>${node.label || node.id}</strong><br/>Type: ${node.type}`;
    if (node.properties) {
      Object.entries(node.properties).slice(0, 3).forEach(([key, value]) => {
        content += `<br/>${key}: ${value}`;
      });
    }

    tooltip.html(content)
      .style('left', `${event.pageX + 10}px`)
      .style('top', `${event.pageY - 10}px`)
      .transition()
      .duration(200)
      .style('opacity', 1);
  };

  const hideTooltip = () => {
    d3.selectAll('.graph-tooltip').remove();
  };

  // Control functions
  const handleZoomIn = () => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.transition().call(
      d3.zoom<SVGSVGElement, unknown>().scaleBy as any,
      1.3
    );
  };

  const handleZoomOut = () => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.transition().call(
      d3.zoom<SVGSVGElement, unknown>().scaleBy as any,
      0.7
    );
  };

  const handleReset = () => {
    if (!svgRef.current || !containerRef.current) return;
    const svg = d3.select(svgRef.current);
    const width = containerRef.current.clientWidth;
    
    svg.transition().call(
      d3.zoom<SVGSVGElement, unknown>().transform as any,
      d3.zoomIdentity.translate(width / 2, height / 2).scale(1)
    );
  };

  const togglePhysics = () => {
    setIsPlaying(!isPlaying);
    if (simulation) {
      if (!isPlaying) {
        simulation.alphaTarget(0.3).restart();
      } else {
        simulation.stop();
      }
    }
  };

  const handleExport = () => {
    if (!svgRef.current) return;
    
    const svgData = new XMLSerializer().serializeToString(svgRef.current);
    const blob = new Blob([svgData], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `graph-${parcelId || 'export'}-${Date.now()}.svg`;
    link.click();
    
    URL.revokeObjectURL(url);
  };

  const handleSearch = (term: string) => {
    setSearchTerm(term);
    if (!term) return;

    // Highlight matching nodes
    d3.selectAll('.nodes g circle')
      .attr('stroke', function(this: SVGCircleElement) {
        const node = d3.select(this).datum() as GraphNode;
        return node.label?.toLowerCase().includes(term.toLowerCase()) ? '#FFD700' : '#fff';
      })
      .attr('stroke-width', function(this: SVGCircleElement) {
        const node = d3.select(this).datum() as GraphNode;
        return node.label?.toLowerCase().includes(term.toLowerCase()) ? 4 : 2;
      });
  };

  const handleRefresh = () => {
    if (parcelId) {
      fetchGraphData(parcelId);
    }
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="relative">
      {showControls && (
        <div className="absolute top-4 left-4 right-4 z-10 flex justify-between items-start">
          {/* Left controls */}
          <div className="flex flex-col gap-2">
            <div className="flex gap-2">
              <Button size="sm" variant="secondary" onClick={handleZoomIn}>
                <ZoomIn className="h-4 w-4" />
              </Button>
              <Button size="sm" variant="secondary" onClick={handleZoomOut}>
                <ZoomOut className="h-4 w-4" />
              </Button>
              <Button size="sm" variant="secondary" onClick={handleReset}>
                <Maximize2 className="h-4 w-4" />
              </Button>
              <Button size="sm" variant="secondary" onClick={togglePhysics}>
                {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              </Button>
            </div>
            
            <div className="flex gap-2">
              <Input
                type="text"
                placeholder="Search nodes..."
                value={searchTerm}
                onChange={(e) => handleSearch(e.target.value)}
                className="w-48 h-8"
                prefix={<Search className="h-3 w-3" />}
              />
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs">Depth:</span>
              <Slider
                value={[depthLimit]}
                onValueChange={([value]) => setDepthLimit(value)}
                min={1}
                max={5}
                step={1}
                className="w-32"
              />
              <span className="text-xs">{depthLimit}</span>
            </div>
          </div>

          {/* Right controls */}
          <div className="flex flex-col gap-2">
            <div className="flex gap-2">
              <Button size="sm" variant="secondary" onClick={handleRefresh}>
                <RefreshCw className="h-4 w-4" />
              </Button>
              <Button size="sm" variant="secondary" onClick={handleExport}>
                <Download className="h-4 w-4" />
              </Button>
            </div>

            {graphData?.metadata && (
              <div className="bg-background/80 backdrop-blur-sm rounded p-2">
                <div className="text-xs space-y-1">
                  <div>Nodes: {graphData.metadata.totalNodes}</div>
                  <div>Links: {graphData.metadata.totalRelationships}</div>
                  <div>Zoom: {(zoom * 100).toFixed(0)}%</div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-10">
        <div className="bg-background/80 backdrop-blur-sm rounded p-2">
          <div className="text-xs font-semibold mb-1">Node Types</div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(nodeColors).map(([type, color]) => (
              <div key={type} className="flex items-center gap-1">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: color }}
                />
                <span className="text-xs capitalize">{type}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Selected node info */}
      {selectedNode && (
        <div className="absolute top-20 right-4 z-10 w-64">
          <Card className="p-3">
            <div className="space-y-2">
              <div className="flex justify-between items-start">
                <h4 className="font-semibold text-sm">{selectedNode.label}</h4>
                <Badge variant="outline">{selectedNode.type}</Badge>
              </div>
              {selectedNode.properties && (
                <div className="space-y-1">
                  {Object.entries(selectedNode.properties).slice(0, 5).map(([key, value]) => (
                    <div key={key} className="text-xs">
                      <span className="font-medium">{key}:</span> {String(value)}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Card>
        </div>
      )}

      {/* SVG Container */}
      <div ref={containerRef} className="relative w-full" style={{ height }}>
        <svg
          ref={svgRef}
          width="100%"
          height={height}
          className="cursor-move"
          style={{ background: colorScheme === 'dark' ? '#1a1a1a' : '#fafafa' }}
        />
      </div>
    </Card>
  );
};

export default GraphVisualization;