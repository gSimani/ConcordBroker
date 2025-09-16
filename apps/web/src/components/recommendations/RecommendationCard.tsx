import React, { useState } from 'react';
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
  ChevronDown,
  ChevronUp,
  ExternalLink,
  BookmarkPlus,
  Share2,
  Calculator,
  Calendar,
  Users
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
  comparable_properties?: string[];
  supporting_data?: Record<string, any>;
}

interface RecommendationCardProps {
  recommendation: PropertyRecommendation;
  onFeedback?: (parcelId: string, rating: number, feedback: string) => void;
  onBookmark?: (parcelId: string) => void;
  onShare?: (parcelId: string) => void;
  onCalculateROI?: (parcelId: string) => void;
  showActions?: boolean;
}

const typeIcons = {
  investment: TrendingUp,
  similar_properties: Building,
  market_opportunities: Target,
  risk_analysis: AlertTriangle,
  portfolio_expansion: MapPin,
  flip_opportunities: DollarSign
};

const typeColors = {
  investment: 'bg-green-500',
  similar_properties: 'bg-blue-500',
  market_opportunities: 'bg-purple-500',
  risk_analysis: 'bg-red-500',
  portfolio_expansion: 'bg-orange-500',
  flip_opportunities: 'bg-yellow-500'
};

const riskColors = {
  low: 'text-green-700 bg-green-100 border-green-200',
  medium: 'text-yellow-700 bg-yellow-100 border-yellow-200',
  high: 'text-red-700 bg-red-100 border-red-200'
};

const urgencyStyles = {
  low: 'border-gray-200',
  normal: 'border-blue-200',
  high: 'border-orange-300',
  urgent: 'border-red-400 shadow-lg'
};

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  recommendation,
  onFeedback,
  onBookmark,
  onShare,
  onCalculateROI,
  showActions = true
}) => {
  const [expanded, setExpanded] = useState(false);
  const [showComparables, setShowComparables] = useState(false);

  const Icon = typeIcons[recommendation.recommendation_type as keyof typeof typeIcons];
  const typeColor = typeColors[recommendation.recommendation_type as keyof typeof typeColors];
  const riskColor = riskColors[recommendation.risk_level as keyof typeof riskColors];
  const urgencyStyle = urgencyStyles[recommendation.urgency as keyof typeof urgencyStyles];

  const handleViewProperty = () => {
    window.open(`/property/${recommendation.parcel_id}`, '_blank');
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: recommendation.title,
        text: recommendation.description,
        url: `/property/${recommendation.parcel_id}`
      });
    } else {
      navigator.clipboard.writeText(`${window.location.origin}/property/${recommendation.parcel_id}`);
      alert('Link copied to clipboard!');
    }
    onShare?.(recommendation.parcel_id);
  };

  return (
    <Card className={`p-6 transition-all hover:shadow-md ${urgencyStyle} ${
      recommendation.urgency === 'urgent' ? 'border-2' : 'border'
    }`}>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1">
            <div className={`p-2 rounded-lg ${typeColor} text-white flex-shrink-0`}>
              <Icon className="h-5 w-5" />
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-semibold text-gray-900 truncate">{recommendation.title}</h3>
                {recommendation.urgency === 'urgent' && (
                  <Badge variant="destructive" className="animate-pulse">
                    URGENT
                  </Badge>
                )}
              </div>
              
              <p className="text-gray-600 text-sm leading-relaxed">
                {recommendation.description}
              </p>
            </div>
          </div>

          {showActions && (
            <Button size="sm" onClick={handleViewProperty}>
              <ExternalLink className="h-4 w-4 mr-1" />
              View
            </Button>
          )}
        </div>

        {/* Metrics */}
        <div className="flex flex-wrap gap-2">
          <Badge variant="outline" className="font-medium">
            {(recommendation.confidence_score * 100).toFixed(0)}% confident
          </Badge>
          
          {recommendation.potential_roi && (
            <Badge variant="secondary" className="font-medium">
              {recommendation.potential_roi.toFixed(1)}% ROI
            </Badge>
          )}
          
          <Badge className={riskColor}>
            {recommendation.risk_level} risk
          </Badge>
          
          {recommendation.estimated_value && (
            <Badge variant="outline">
              ${recommendation.estimated_value.toLocaleString()}
            </Badge>
          )}
        </div>

        {/* Confidence Progress */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-gray-500">
            <span>Confidence Score</span>
            <span>{(recommendation.confidence_score * 100).toFixed(0)}%</span>
          </div>
          <Progress value={recommendation.confidence_score * 100} className="h-2" />
        </div>

        {/* Key Factors */}
        {recommendation.reasoning && recommendation.reasoning.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-700">Key Factors:</h4>
            <ul className="space-y-1">
              {recommendation.reasoning.slice(0, expanded ? recommendation.reasoning.length : 3).map((reason, index) => (
                <li key={index} className="flex items-start gap-2 text-sm text-gray-600">
                  <span className="text-blue-500 mt-1 flex-shrink-0">•</span>
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
            
            {recommendation.reasoning.length > 3 && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
              >
                {expanded ? (
                  <>
                    Show less <ChevronUp className="h-3 w-3" />
                  </>
                ) : (
                  <>
                    +{recommendation.reasoning.length - 3} more factors <ChevronDown className="h-3 w-3" />
                  </>
                )}
              </button>
            )}
          </div>
        )}

        {/* Supporting Data */}
        {expanded && recommendation.supporting_data && Object.keys(recommendation.supporting_data).length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-700">Supporting Data:</h4>
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(recommendation.supporting_data).slice(0, 4).map(([key, value]) => (
                <div key={key} className="bg-gray-50 p-2 rounded text-sm">
                  <div className="font-medium text-gray-700 capitalize">
                    {key.replace('_', ' ')}
                  </div>
                  <div className="text-gray-600">
                    {typeof value === 'number' 
                      ? value.toLocaleString() 
                      : String(value)
                    }
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Items */}
        {expanded && recommendation.action_items && recommendation.action_items.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-700">Next Steps:</h4>
            <ul className="space-y-1">
              {recommendation.action_items.map((action, index) => (
                <li key={index} className="flex items-start gap-2 text-sm text-gray-600">
                  <span className="text-green-500 mt-1 flex-shrink-0">→</span>
                  <span>{action}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Comparable Properties */}
        {expanded && recommendation.comparable_properties && recommendation.comparable_properties.length > 0 && (
          <div className="space-y-2">
            <button
              onClick={() => setShowComparables(!showComparables)}
              className="text-sm font-medium text-gray-700 flex items-center gap-1 hover:text-gray-900"
            >
              <Users className="h-4 w-4" />
              Comparable Properties ({recommendation.comparable_properties.length})
              {showComparables ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            </button>
            
            {showComparables && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {recommendation.comparable_properties.slice(0, 4).map((parcelId, index) => (
                  <button
                    key={index}
                    onClick={() => window.open(`/property/${parcelId}`, '_blank')}
                    className="text-left p-2 bg-gray-50 hover:bg-gray-100 rounded text-sm transition-colors"
                  >
                    <div className="font-mono text-xs text-gray-500">ID: {parcelId}</div>
                    <div className="text-blue-600 hover:underline">View Similar Property</div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        {showActions && (
          <div className="flex items-center justify-between pt-2 border-t border-gray-100">
            <div className="flex gap-2">
              {onBookmark && (
                <Button variant="outline" size="sm" onClick={() => onBookmark(recommendation.parcel_id)}>
                  <BookmarkPlus className="h-4 w-4 mr-1" />
                  Save
                </Button>
              )}
              
              <Button variant="outline" size="sm" onClick={handleShare}>
                <Share2 className="h-4 w-4 mr-1" />
                Share
              </Button>
              
              {onCalculateROI && recommendation.recommendation_type === 'investment' && (
                <Button variant="outline" size="sm" onClick={() => onCalculateROI(recommendation.parcel_id)}>
                  <Calculator className="h-4 w-4 mr-1" />
                  Calculate
                </Button>
              )}
            </div>

            <div className="flex gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onFeedback?.(recommendation.parcel_id, 5, 'helpful')}
                className="text-green-600 hover:bg-green-50"
              >
                👍
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onFeedback?.(recommendation.parcel_id, 2, 'not helpful')}
                className="text-red-600 hover:bg-red-50"
              >
                👎
              </Button>
            </div>
          </div>
        )}

        {/* Timestamp */}
        <div className="text-xs text-gray-400 flex items-center gap-1 pt-1">
          <Calendar className="h-3 w-3" />
          Updated {new Date().toLocaleDateString()}
        </div>
      </div>
    </Card>
  );
};

export default RecommendationCard;