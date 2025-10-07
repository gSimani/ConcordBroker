import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader } from '../ui/card';
import { Sparkles, TrendingUp, TrendingDown, Minus, Loader2, Bot, Search } from 'lucide-react';

interface Property {
  parcel_id: string;
  phy_addr1: string;
  phy_city: string;
  phy_zipcd: string;
  owner_name: string;
  tot_sqft?: number;
  bedrooms?: number;
  bathrooms?: number;
  property_type?: string;
  just_value?: number;
  sale_price?: number;
  sale_date?: string;
}

interface AIPropertyCardProps {
  property: Property;
}

export const AIPropertyCard: React.FC<AIPropertyCardProps> = ({ property }) => {
  const [aiDescription, setAiDescription] = useState<string>('');
  const [marketSentiment, setMarketSentiment] = useState<any>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [showAI, setShowAI] = useState(false);

  const generateAIDescription = async () => {
    setIsGenerating(true);
    try {
      const response = await fetch('http://localhost:8000/api/ai/generate-description', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          address: `${property.phy_addr1}, ${property.phy_city}, FL ${property.phy_zipcd}`,
          bedrooms: property.bedrooms || 3,
          bathrooms: property.bathrooms || 2,
          square_feet: property.tot_sqft || 2000,
          property_type: property.property_type || 'Single Family Home',
          features: [],
          style: 'professional'
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setAiDescription(data.description);
      }
    } catch (error) {
      console.error('Error generating description:', error);
      setAiDescription('Beautiful property with great potential. Contact us for more details.');
    } finally {
      setIsGenerating(false);
    }
  };

  const analyzeMarket = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/ai/market-sentiment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          location: property.phy_city,
          property_type: property.property_type || 'residential',
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setMarketSentiment(data);
      }
    } catch (error) {
      console.error('Error analyzing market:', error);
    }
  };

  useEffect(() => {
    if (showAI && !aiDescription) {
      generateAIDescription();
      analyzeMarket();
    }
  }, [showAI]);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(price);
  };

  const getSentimentIcon = () => {
    if (!marketSentiment) return <Minus className="w-4 h-4" />;
    switch (marketSentiment.sentiment) {
      case 'bullish':
        return <TrendingUp className="w-4 h-4 text-green-500" />;
      case 'bearish':
        return <TrendingDown className="w-4 h-4 text-red-500" />;
      default:
        return <Minus className="w-4 h-4 text-gray-500" />;
    }
  };

  const getSentimentColor = () => {
    if (!marketSentiment) return 'text-gray-600';
    switch (marketSentiment.sentiment) {
      case 'bullish':
        return 'text-green-600';
      case 'bearish':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <Card className="hover:shadow-xl transition-all duration-300 border-gray-200">
      <CardHeader className="pb-3">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900">
              {property.phy_addr1}
            </h3>
            <p className="text-sm text-gray-600">
              {property.phy_city}, FL {property.phy_zipcd}
            </p>
          </div>
          <button
            onClick={() => setShowAI(!showAI)}
            className={`ml-2 p-2 rounded-lg transition-all ${
              showAI 
                ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white' 
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
            title="Toggle AI Features"
          >
            <Sparkles className="w-5 h-5" />
          </button>
        </div>
      </CardHeader>
      
      <CardContent>
        {/* Property Details */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div>
            <p className="text-xs text-gray-500">Owner</p>
            <p className="text-sm font-medium">{property.owner_name}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Assessed Value</p>
            <p className="text-sm font-medium">
              {property.just_value ? formatPrice(property.just_value) : 'N/A'}
            </p>
          </div>
          {property.sale_price && (
            <div>
              <p className="text-xs text-gray-500">Last Sale</p>
              <p className="text-sm font-medium">{formatPrice(property.sale_price)}</p>
            </div>
          )}
          {property.tot_sqft && (
            <div>
              <p className="text-xs text-gray-500">Size</p>
              <p className="text-sm font-medium">{property.tot_sqft.toLocaleString()} sq ft</p>
            </div>
          )}
        </div>

        {/* AI Features Section */}
        {showAI && (
          <div className="space-y-4 pt-4 border-t border-gray-100">
            {/* AI Description */}
            <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Bot className="w-4 h-4 text-purple-600" />
                <h4 className="text-sm font-semibold text-purple-900">AI Property Description</h4>
              </div>
              {isGenerating ? (
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Generating intelligent description...
                </div>
              ) : (
                <p className="text-sm text-gray-700 leading-relaxed">
                  {aiDescription || 'Click to generate AI description'}
                </p>
              )}
            </div>

            {/* Market Sentiment */}
            {marketSentiment && (
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {getSentimentIcon()}
                    <h4 className="text-sm font-semibold text-gray-900">Market Analysis</h4>
                  </div>
                  <span className={`text-xs font-medium ${getSentimentColor()}`}>
                    {marketSentiment.sentiment?.toUpperCase()}
                  </span>
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-600">Confidence</span>
                    <span className="font-medium">
                      {(marketSentiment.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                    <div 
                      className={`h-1.5 rounded-full ${
                        marketSentiment.sentiment === 'bullish' 
                          ? 'bg-green-500' 
                          : marketSentiment.sentiment === 'bearish'
                          ? 'bg-red-500'
                          : 'bg-gray-500'
                      }`}
                      style={{ width: `${marketSentiment.confidence * 100}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-600 mt-2">
                    {marketSentiment.analysis?.recommendation}
                  </p>
                </div>
              </div>
            )}

            {/* AI Actions */}
            <div className="flex gap-2">
              <button 
                className="flex-1 px-3 py-2 text-xs font-medium text-white bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg hover:from-purple-600 hover:to-blue-600 transition-all"
                onClick={generateAIDescription}
                disabled={isGenerating}
              >
                {isGenerating ? 'Generating...' : 'Regenerate Description'}
              </button>
              <button className="flex-1 px-3 py-2 text-xs font-medium text-purple-600 bg-purple-100 rounded-lg hover:bg-purple-200 transition-all flex items-center justify-center gap-1">
                <Search className="w-3 h-3" />
                Similar Properties
              </button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};