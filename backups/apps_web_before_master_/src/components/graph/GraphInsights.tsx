import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  TrendingUp, 
  TrendingDown, 
  Users, 
  Building,
  MapPin,
  Activity,
  AlertCircle,
  CheckCircle,
  Info
} from 'lucide-react';

interface GraphInsight {
  id: string;
  type: 'positive' | 'negative' | 'neutral' | 'warning';
  category: 'ownership' | 'value' | 'market' | 'risk' | 'opportunity';
  title: string;
  description: string;
  confidence: number;
  impact?: 'high' | 'medium' | 'low';
  metadata?: {
    value?: number;
    percentage?: number;
    count?: number;
    [key: string]: any;
  };
}

interface GraphPattern {
  name: string;
  description: string;
  frequency: number;
  examples: string[];
}

interface GraphInsightsProps {
  parcelId?: string;
  insights?: GraphInsight[];
  patterns?: GraphPattern[];
  onInsightClick?: (insight: GraphInsight) => void;
}

const insightIcons = {
  positive: CheckCircle,
  negative: AlertCircle,
  neutral: Info,
  warning: AlertCircle
};

const insightColors = {
  positive: 'text-green-600 bg-green-50',
  negative: 'text-red-600 bg-red-50',
  neutral: 'text-blue-600 bg-blue-50',
  warning: 'text-yellow-600 bg-yellow-50'
};

const categoryIcons = {
  ownership: Users,
  value: TrendingUp,
  market: Activity,
  risk: AlertCircle,
  opportunity: Building
};

export const GraphInsights: React.FC<GraphInsightsProps> = ({
  parcelId,
  insights: initialInsights,
  patterns: initialPatterns,
  onInsightClick
}) => {
  const [insights, setInsights] = useState<GraphInsight[]>(initialInsights || []);
  const [patterns, setPatterns] = useState<GraphPattern[]>(initialPatterns || []);
  const [loading, setLoading] = useState(!initialInsights);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  useEffect(() => {
    if (parcelId && !initialInsights) {
      fetchInsights();
    }
  }, [parcelId]);

  const fetchInsights = async () => {
    if (!parcelId) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/api/graph/property/${parcelId}/insights`);
      const data = await response.json();
      setInsights(data.insights || []);
      setPatterns(data.patterns || []);
    } catch (error) {
      console.error('Error fetching insights:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredInsights = selectedCategory === 'all' 
    ? insights 
    : insights.filter(i => i.category === selectedCategory);

  const categories = ['all', ...new Set(insights.map(i => i.category))];

  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3" />
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-20 bg-gray-200 rounded" />
            ))}
          </div>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Insights Section */}
      <Card className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Graph Insights</h3>
          <div className="flex gap-2">
            {categories.map(cat => (
              <Badge
                key={cat}
                variant={selectedCategory === cat ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() => setSelectedCategory(cat)}
              >
                {cat}
              </Badge>
            ))}
          </div>
        </div>

        {filteredInsights.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Info className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>No insights available for this selection</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredInsights.map(insight => {
              const Icon = insightIcons[insight.type];
              const CategoryIcon = categoryIcons[insight.category];
              const colorClass = insightColors[insight.type];
              
              return (
                <div
                  key={insight.id}
                  className={`p-4 rounded-lg border cursor-pointer hover:shadow-md transition-shadow ${colorClass}`}
                  onClick={() => onInsightClick?.(insight)}
                >
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0">
                      <Icon className="h-5 w-5" />
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <CategoryIcon className="h-4 w-4" />
                        <h4 className="font-medium">{insight.title}</h4>
                        {insight.impact && (
                          <Badge 
                            variant="outline" 
                            className={`text-xs ${
                              insight.impact === 'high' ? 'border-red-500 text-red-600' :
                              insight.impact === 'medium' ? 'border-yellow-500 text-yellow-600' :
                              'border-gray-500 text-gray-600'
                            }`}
                          >
                            {insight.impact} impact
                          </Badge>
                        )}
                      </div>
                      
                      <p className="text-sm opacity-90">{insight.description}</p>
                      
                      {insight.metadata && (
                        <div className="flex gap-3 mt-2">
                          {insight.metadata.value && (
                            <span className="text-sm font-medium">
                              ${insight.metadata.value.toLocaleString()}
                            </span>
                          )}
                          {insight.metadata.percentage !== undefined && (
                            <Badge variant="secondary" className="text-xs">
                              {insight.metadata.percentage > 0 ? '+' : ''}{insight.metadata.percentage.toFixed(1)}%
                            </Badge>
                          )}
                          {insight.metadata.count && (
                            <span className="text-sm">
                              {insight.metadata.count} occurrences
                            </span>
                          )}
                        </div>
                      )}
                      
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-xs opacity-75">Confidence:</span>
                        <Progress value={insight.confidence * 100} className="h-1.5 w-24" />
                        <span className="text-xs font-medium">{(insight.confidence * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      {/* Patterns Section */}
      {patterns.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Discovered Patterns</h3>
          
          <div className="space-y-3">
            {patterns.map((pattern, index) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-medium">{pattern.name}</h4>
                  <Badge variant="outline">
                    {pattern.frequency}x
                  </Badge>
                </div>
                
                <p className="text-sm text-gray-600 mb-2">{pattern.description}</p>
                
                {pattern.examples.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    <span className="text-xs text-gray-500">Examples:</span>
                    {pattern.examples.slice(0, 3).map((example, i) => (
                      <Badge key={i} variant="secondary" className="text-xs">
                        {example}
                      </Badge>
                    ))}
                    {pattern.examples.length > 3 && (
                      <span className="text-xs text-gray-500">
                        +{pattern.examples.length - 3} more
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Summary Stats */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Insight Summary</h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {insights.filter(i => i.type === 'positive').length}
            </div>
            <div className="text-sm text-gray-600">Positive</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">
              {insights.filter(i => i.type === 'negative').length}
            </div>
            <div className="text-sm text-gray-600">Negative</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">
              {insights.filter(i => i.type === 'warning').length}
            </div>
            <div className="text-sm text-gray-600">Warnings</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {(insights.reduce((acc, i) => acc + i.confidence, 0) / insights.length * 100).toFixed(0)}%
            </div>
            <div className="text-sm text-gray-600">Avg Confidence</div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default GraphInsights;