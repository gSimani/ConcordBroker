import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { 
  TrendingUp, 
  AlertTriangle, 
  Target, 
  Building,
  MapPin,
  DollarSign,
  Star,
  Filter,
  RefreshCw,
  Download,
  ThumbsUp,
  ThumbsDown,
  MoreHorizontal
} from 'lucide-react';

interface PropertyRecommendation {
  parcel_id: string;
  recommendation_type: string;
  title: string;
  description: string;
  confidence_score: number;
  potential_roi?: number;
  risk_level: string;
  reasoning: string[];
  urgency: string;
  estimated_value?: number;
  action_items: string[];
}

interface RecommendationSummary {
  total_recommendations: number;
  by_type: Record<string, number>;
  by_risk_level: Record<string, number>;
  by_urgency: Record<string, number>;
  avg_confidence: number;
  top_opportunity?: PropertyRecommendation;
}

const recommendationTypeIcons = {
  investment: TrendingUp,
  similar_properties: Building,
  market_opportunities: Target,
  risk_analysis: AlertTriangle,
  portfolio_expansion: MapPin,
  flip_opportunities: DollarSign
};

const recommendationTypeColors = {
  investment: 'bg-green-500',
  similar_properties: 'bg-blue-500',
  market_opportunities: 'bg-purple-500',
  risk_analysis: 'bg-red-500',
  portfolio_expansion: 'bg-orange-500',
  flip_opportunities: 'bg-yellow-500'
};

const riskColors = {
  low: 'text-green-600 bg-green-50',
  medium: 'text-yellow-600 bg-yellow-50',
  high: 'text-red-600 bg-red-50'
};

const urgencyColors = {
  low: 'border-gray-300',
  normal: 'border-blue-300',
  high: 'border-orange-300',
  urgent: 'border-red-300'
};

export const RecommendationDashboard: React.FC = () => {
  const [summary, setSummary] = useState<RecommendationSummary | null>(null);
  const [recommendations, setRecommendations] = useState<PropertyRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [confidenceThreshold, setConfidenceThreshold] = useState(60);
  const [expandedCard, setExpandedCard] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, [selectedTypes, confidenceThreshold]);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch summary
      const summaryResponse = await fetch('/api/recommendations/summary?' + 
        new URLSearchParams({
          confidence_threshold: (confidenceThreshold / 100).toString(),
          ...(selectedTypes.length > 0 && { recommendation_types: selectedTypes.join(',') })
        })
      );
      const summaryData = await summaryResponse.json();
      setSummary(summaryData);

      // Fetch detailed recommendations
      const recsResponse = await fetch('/api/recommendations/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recommendation_types: selectedTypes.length > 0 ? selectedTypes : [
            'investment', 'similar_properties', 'market_opportunities', 'risk_analysis'
          ],
          max_results: 20,
          confidence_threshold: confidenceThreshold / 100
        })
      });
      const recsData = await recsResponse.json();
      setRecommendations(recsData);

    } catch (error) {
      console.error('Error fetching recommendations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (parcelId: string, rating: number, feedback: string) => {
    try {
      await fetch('/api/recommendations/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          parcel_id: parcelId,
          rating,
          feedback
        })
      });
      // Show success message or update UI
    } catch (error) {
      console.error('Error submitting feedback:', error);
    }
  };

  const exportRecommendations = async () => {
    try {
      const response = await fetch('/api/recommendations/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recommendation_types: selectedTypes.length > 0 ? selectedTypes : [
            'investment', 'similar_properties', 'market_opportunities', 'risk_analysis'
          ],
          max_results: 100,
          confidence_threshold: confidenceThreshold / 100
        })
      });
      const data = await response.json();
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `recommendations-${new Date().toISOString().split('T')[0]}.json`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting recommendations:', error);
    }
  };

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-32 bg-gray-200 rounded" />
            ))}
          </div>
          <div className="space-y-4">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-48 bg-gray-200 rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Property Recommendations</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" onClick={exportRecommendations}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4" />
            <span className="font-medium">Filters:</span>
          </div>
          
          <div className="flex items-center gap-2">
            <span className="text-sm">Confidence:</span>
            <input
              type="range"
              min="10"
              max="100"
              value={confidenceThreshold}
              onChange={(e) => setConfidenceThreshold(Number(e.target.value))}
              className="w-24"
            />
            <span className="text-sm">{confidenceThreshold}%</span>
          </div>

          <div className="flex gap-2">
            {Object.keys(recommendationTypeIcons).map(type => (
              <Button
                key={type}
                variant={selectedTypes.includes(type) ? "default" : "outline"}
                size="sm"
                onClick={() => {
                  setSelectedTypes(prev => 
                    prev.includes(type) 
                      ? prev.filter(t => t !== type)
                      : [...prev, type]
                  );
                }}
              >
                {type.replace('_', ' ')}
              </Button>
            ))}
          </div>
        </div>
      </Card>

      {/* Summary Statistics */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-4">
            <div className="flex items-center gap-2">
              <Target className="h-5 w-5 text-blue-600" />
              <div>
                <p className="text-sm text-gray-600">Total Recommendations</p>
                <p className="text-2xl font-bold">{summary.total_recommendations}</p>
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center gap-2">
              <Star className="h-5 w-5 text-yellow-600" />
              <div>
                <p className="text-sm text-gray-600">Avg Confidence</p>
                <p className="text-2xl font-bold">{(summary.avg_confidence * 100).toFixed(0)}%</p>
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-600" />
              <div>
                <p className="text-sm text-gray-600">High Priority</p>
                <p className="text-2xl font-bold">{summary.by_urgency.high || 0}</p>
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-green-600" />
              <div>
                <p className="text-sm text-gray-600">Investment Opps</p>
                <p className="text-2xl font-bold">{summary.by_type.investment || 0}</p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Top Opportunity Highlight */}
      {summary?.top_opportunity && (
        <Card className="p-6 border-2 border-gold-200 bg-gradient-to-r from-yellow-50 to-gold-50">
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-full bg-gold-100">
              <Star className="h-6 w-6 text-gold-600" />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-semibold text-gold-800">Top Opportunity</h3>
              <p className="text-gold-700 mt-1">{summary.top_opportunity.title}</p>
              <p className="text-sm text-gold-600 mt-2">{summary.top_opportunity.description}</p>
              <div className="flex gap-4 mt-3">
                <Badge variant="secondary">
                  Confidence: {(summary.top_opportunity.confidence_score * 100).toFixed(0)}%
                </Badge>
                {summary.top_opportunity.potential_roi && (
                  <Badge variant="secondary">
                    ROI: {summary.top_opportunity.potential_roi.toFixed(1)}%
                  </Badge>
                )}
                <Badge className={riskColors[summary.top_opportunity.risk_level as keyof typeof riskColors]}>
                  {summary.top_opportunity.risk_level} risk
                </Badge>
              </div>
            </div>
            <Button>
              View Details
            </Button>
          </div>
        </Card>
      )}

      {/* Recommendations List */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold">All Recommendations</h2>
        
        {recommendations.map((rec) => {
          const Icon = recommendationTypeIcons[rec.recommendation_type as keyof typeof recommendationTypeIcons];
          const isExpanded = expandedCard === rec.parcel_id;
          
          return (
            <Card 
              key={rec.parcel_id} 
              className={`p-6 transition-all ${urgencyColors[rec.urgency as keyof typeof urgencyColors]} ${
                rec.urgency === 'urgent' ? 'border-2' : 'border'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4 flex-1">
                  <div className={`p-3 rounded-full ${recommendationTypeColors[rec.recommendation_type as keyof typeof recommendationTypeColors]} text-white`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="font-semibold">{rec.title}</h3>
                      {rec.urgency === 'urgent' && (
                        <Badge variant="destructive" className="animate-pulse">
                          URGENT
                        </Badge>
                      )}
                    </div>
                    
                    <p className="text-gray-600 mb-3">{rec.description}</p>
                    
                    <div className="flex flex-wrap gap-2 mb-3">
                      <Badge variant="outline">
                        Confidence: {(rec.confidence_score * 100).toFixed(0)}%
                      </Badge>
                      {rec.potential_roi && (
                        <Badge variant="secondary">
                          ROI: {rec.potential_roi.toFixed(1)}%
                        </Badge>
                      )}
                      <Badge className={riskColors[rec.risk_level as keyof typeof riskColors]}>
                        {rec.risk_level} risk
                      </Badge>
                      {rec.estimated_value && (
                        <Badge variant="outline">
                          ${rec.estimated_value.toLocaleString()}
                        </Badge>
                      )}
                    </div>

                    <div className="mb-3">
                      <Progress value={rec.confidence_score * 100} className="h-2" />
                    </div>

                    {/* Reasoning - always show first 2 items */}
                    {rec.reasoning && rec.reasoning.length > 0 && (
                      <div className="mb-3">
                        <p className="text-sm font-medium text-gray-700 mb-1">Key Factors:</p>
                        <ul className="text-sm text-gray-600 space-y-1">
                          {rec.reasoning.slice(0, isExpanded ? rec.reasoning.length : 2).map((reason, index) => (
                            <li key={index} className="flex items-start gap-2">
                              <span className="text-blue-500 mt-1">•</span>
                              {reason}
                            </li>
                          ))}
                        </ul>
                        {rec.reasoning.length > 2 && !isExpanded && (
                          <button 
                            className="text-sm text-blue-600 hover:underline mt-1"
                            onClick={() => setExpandedCard(rec.parcel_id)}
                          >
                            +{rec.reasoning.length - 2} more reasons
                          </button>
                        )}
                      </div>
                    )}

                    {/* Action Items - show when expanded */}
                    {isExpanded && rec.action_items && rec.action_items.length > 0 && (
                      <div className="mb-4">
                        <p className="text-sm font-medium text-gray-700 mb-2">Next Steps:</p>
                        <ul className="text-sm text-gray-600 space-y-1">
                          {rec.action_items.map((action, index) => (
                            <li key={index} className="flex items-start gap-2">
                              <span className="text-green-500 mt-1">→</span>
                              {action}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col gap-2">
                  <Button size="sm" onClick={() => window.open(`/property/${rec.parcel_id}`, '_blank')}>
                    View Property
                  </Button>
                  
                  <div className="flex gap-1">
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => handleFeedback(rec.parcel_id, 5, 'helpful')}
                    >
                      <ThumbsUp className="h-3 w-3" />
                    </Button>
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => handleFeedback(rec.parcel_id, 2, 'not helpful')}
                    >
                      <ThumbsDown className="h-3 w-3" />
                    </Button>
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => setExpandedCard(isExpanded ? null : rec.parcel_id)}
                    >
                      <MoreHorizontal className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {recommendations.length === 0 && (
        <Card className="p-12 text-center">
          <Target className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-semibold text-gray-600 mb-2">No Recommendations Found</h3>
          <p className="text-gray-500">
            Try adjusting your filters or check back later for new opportunities.
          </p>
        </Card>
      )}
    </div>
  );
};

export default RecommendationDashboard;