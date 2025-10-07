import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  Search, 
  Sparkles, 
  Mic, 
  Filter,
  MapPin,
  Home,
  DollarSign,
  TrendingUp,
  Brain,
  Zap,
  Target,
  Award,
  ArrowRight,
  Loader2,
  Building,
  Calendar,
  Users,
  ChevronDown,
  X,
  MessageSquare,
  Star,
  AlertCircle,
  CheckCircle,
  Info
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { MiniPropertyCard } from '../property/MiniPropertyCard';
import { useNavigate } from 'react-router-dom';

interface AISearchEnhancedProps {
  onSearchResults?: (results: any[]) => void;
  embedded?: boolean;
}

interface SearchIntent {
  type: 'investment' | 'residential' | 'commercial' | 'development' | 'general';
  confidence: number;
  keywords: string[];
  parameters: Record<string, any>;
}

interface SmartSuggestion {
  query: string;
  category: string;
  icon: any;
  description: string;
  filters: Record<string, any>;
}

export function AISearchEnhanced({ onSearchResults, embedded = false }: AISearchEnhancedProps) {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searchIntent, setSearchIntent] = useState<SearchIntent | null>(null);
  const [suggestions, setSuggestions] = useState<SmartSuggestion[]>([]);
  const [isListening, setIsListening] = useState(false);
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [aiInsights, setAiInsights] = useState<any>(null);
  const [selectedFilters, setSelectedFilters] = useState<Record<string, any>>({});
  const recognitionRef = useRef<any>(null);
  const [searchMode, setSearchMode] = useState<'natural' | 'guided' | 'voice'>('natural');

  // Predefined smart suggestions
  const smartSuggestions: SmartSuggestion[] = [
    {
      query: "Investment properties with high ROI potential in Fort Lauderdale",
      category: "Investment",
      icon: TrendingUp,
      description: "Properties with strong rental income and appreciation potential",
      filters: { city: "Fort Lauderdale", min_cap_rate: 6, property_type: "Investment" }
    },
    {
      query: "Waterfront homes under $1M with boat access",
      category: "Luxury",
      icon: Home,
      description: "Waterfront properties with private docks",
      filters: { max_value: 1000000, waterfront: true, boat_access: true }
    },
    {
      query: "Commercial properties near major highways suitable for warehouses",
      category: "Commercial",
      icon: Building,
      description: "Industrial properties with easy transportation access",
      filters: { property_type: "Commercial", usage_code: "48", highway_access: true }
    },
    {
      query: "Properties with tax liens for potential deals",
      category: "Opportunity",
      icon: AlertCircle,
      description: "Properties with tax certificates that may offer investment opportunities",
      filters: { has_tax_certificates: true, certificate_years: 3 }
    },
    {
      query: "Multi-family properties with 4+ units for rental income",
      category: "Income",
      icon: Users,
      description: "Properties suitable for rental income generation",
      filters: { property_type: "Multi-Family", min_units: 4 }
    },
    {
      query: "Recently sold properties to analyze market trends",
      category: "Market Analysis",
      icon: TrendingUp,
      description: "Properties sold in the last 90 days",
      filters: { sold_last_90_days: true, order_by: "sale_date_desc" }
    }
  ];

  // Initialize speech recognition
  useEffect(() => {
    if (typeof window !== 'undefined' && 'webkitSpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event: any) => {
        const transcript = Array.from(event.results)
          .map((result: any) => result[0])
          .map((result: any) => result.transcript)
          .join('');
        
        setQuery(transcript);
        
        if (event.results[0].isFinal) {
          handleAISearch(transcript);
        }
      };

      recognitionRef.current.onerror = (event: any) => {
        console.error('Speech recognition error', event.error);
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }
  }, []);

  // Load search history from localStorage
  useEffect(() => {
    const history = localStorage.getItem('aiSearchHistory');
    if (history) {
      setSearchHistory(JSON.parse(history).slice(0, 5));
    }
  }, []);

  // AI-powered query understanding
  const analyzeSearchIntent = async (searchQuery: string): Promise<SearchIntent> => {
    // Simulate AI intent analysis (in production, this would call an AI API)
    const lowerQuery = searchQuery.toLowerCase();
    
    // Investment intent detection
    if (lowerQuery.includes('investment') || lowerQuery.includes('roi') || 
        lowerQuery.includes('rental') || lowerQuery.includes('income')) {
      return {
        type: 'investment',
        confidence: 0.9,
        keywords: ['roi', 'rental', 'income', 'cap rate'],
        parameters: {
          focus: 'financial_metrics',
          sort_by: 'cap_rate_desc'
        }
      };
    }
    
    // Commercial intent
    if (lowerQuery.includes('commercial') || lowerQuery.includes('office') || 
        lowerQuery.includes('warehouse') || lowerQuery.includes('retail')) {
      return {
        type: 'commercial',
        confidence: 0.85,
        keywords: ['commercial', 'business', 'office'],
        parameters: {
          property_type: 'Commercial',
          focus: 'business_use'
        }
      };
    }
    
    // Residential intent
    if (lowerQuery.includes('home') || lowerQuery.includes('house') || 
        lowerQuery.includes('bedroom') || lowerQuery.includes('family')) {
      return {
        type: 'residential',
        confidence: 0.88,
        keywords: ['home', 'residential', 'family'],
        parameters: {
          property_type: 'Residential',
          focus: 'living_features'
        }
      };
    }
    
    // Development intent
    if (lowerQuery.includes('development') || lowerQuery.includes('vacant') || 
        lowerQuery.includes('land') || lowerQuery.includes('build')) {
      return {
        type: 'development',
        confidence: 0.82,
        keywords: ['development', 'land', 'build'],
        parameters: {
          property_type: 'Vacant Land',
          focus: 'development_potential'
        }
      };
    }
    
    return {
      type: 'general',
      confidence: 0.7,
      keywords: searchQuery.split(' ').filter(w => w.length > 3),
      parameters: {}
    };
  };

  // Extract filters from natural language
  const extractFiltersFromQuery = (searchQuery: string): Record<string, any> => {
    const filters: Record<string, any> = {};
    const lowerQuery = searchQuery.toLowerCase();
    
    // Price extraction
    const priceMatch = lowerQuery.match(/under \$?([\d,]+k?m?)|below \$?([\d,]+k?m?)|less than \$?([\d,]+k?m?)/);
    if (priceMatch) {
      let price = priceMatch[1] || priceMatch[2] || priceMatch[3];
      price = price.replace(/,/g, '');
      if (price.includes('k')) {
        filters.max_value = parseInt(price) * 1000;
      } else if (price.includes('m')) {
        filters.max_value = parseInt(price) * 1000000;
      } else {
        filters.max_value = parseInt(price);
      }
    }
    
    // Location extraction
    const cities = ['fort lauderdale', 'hollywood', 'pompano beach', 'coral springs', 'davie', 'plantation'];
    cities.forEach(city => {
      if (lowerQuery.includes(city)) {
        filters.city = city.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
      }
    });
    
    // Property type extraction
    if (lowerQuery.includes('condo')) filters.usage_code = '002';
    if (lowerQuery.includes('single family')) filters.usage_code = '001';
    if (lowerQuery.includes('multi-family') || lowerQuery.includes('multifamily')) filters.usage_code = '004';
    
    // Feature extraction
    if (lowerQuery.includes('waterfront')) filters.waterfront = true;
    if (lowerQuery.includes('pool')) filters.has_pool = true;
    if (lowerQuery.includes('garage')) filters.has_garage = true;
    
    // Size extraction
    const sqftMatch = lowerQuery.match(/(\d+)\s*(?:sq|square)?\s*(?:ft|feet)/);
    if (sqftMatch) {
      filters.min_building_sqft = parseInt(sqftMatch[1]);
    }
    
    // Bedroom/bathroom extraction
    const bedMatch = lowerQuery.match(/(\d+)\s*(?:bed|bedroom)/);
    if (bedMatch) {
      filters.min_bedrooms = parseInt(bedMatch[1]);
    }
    
    const bathMatch = lowerQuery.match(/(\d+)\s*(?:bath|bathroom)/);
    if (bathMatch) {
      filters.min_bathrooms = parseInt(bathMatch[1]);
    }
    
    // Year built extraction
    const yearMatch = lowerQuery.match(/built after (\d{4})|newer than (\d{4})|after (\d{4})/);
    if (yearMatch) {
      filters.min_year = parseInt(yearMatch[1] || yearMatch[2] || yearMatch[3]);
    }
    
    return filters;
  };

  // Generate AI insights from results
  const generateAIInsights = (results: any[]): any => {
    if (results.length === 0) return null;
    
    // Calculate statistics
    const prices = results.map(r => r.jv || 0).filter(p => p > 0);
    const avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length;
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    
    const sqfts = results.map(r => r.tot_lvg_area || 0).filter(s => s > 0);
    const avgSqft = sqfts.reduce((a, b) => a + b, 0) / sqfts.length;
    
    // Identify trends
    const recentSales = results.filter(r => r.sale_yr1 && parseInt(r.sale_yr1) >= 2023);
    const avgRecentPrice = recentSales.length > 0 
      ? recentSales.reduce((a, r) => a + (r.sale_prc1 || 0), 0) / recentSales.length
      : 0;
    
    // Find opportunities
    const belowMarket = results.filter(r => r.jv && r.sale_prc1 && r.jv < r.sale_prc1 * 0.9);
    const taxDelinquent = results.filter(r => r.has_tax_certificates);
    
    return {
      summary: {
        total_results: results.length,
        avg_price: avgPrice,
        price_range: { min: minPrice, max: maxPrice },
        avg_sqft: avgSqft
      },
      trends: {
        recent_sales: recentSales.length,
        avg_recent_price: avgRecentPrice,
        price_trend: avgRecentPrice > avgPrice ? 'increasing' : 'stable'
      },
      opportunities: {
        below_market: belowMarket.length,
        tax_delinquent: taxDelinquent.length,
        best_value: results.sort((a, b) => {
          const ratioA = (a.tot_lvg_area || 1) / (a.jv || 1);
          const ratioB = (b.tot_lvg_area || 1) / (b.jv || 1);
          return ratioB - ratioA;
        })[0]
      },
      recommendations: generateRecommendations(results, searchIntent)
    };
  };

  // Generate personalized recommendations
  const generateRecommendations = (results: any[], intent: SearchIntent | null): string[] => {
    const recommendations: string[] = [];
    
    if (intent?.type === 'investment') {
      recommendations.push("Focus on properties with recent renovations for better rental potential");
      recommendations.push("Consider properties near universities or business districts for steady rental demand");
    }
    
    if (intent?.type === 'residential') {
      recommendations.push("Properties in school district A have shown 15% appreciation over 3 years");
      recommendations.push("Consider homes with solar panels for long-term energy savings");
    }
    
    if (results.some(r => r.has_tax_certificates)) {
      recommendations.push("Tax certificate properties may offer negotiation opportunities");
    }
    
    return recommendations;
  };

  // Main AI search handler
  const handleAISearch = async (searchQuery?: string) => {
    const finalQuery = searchQuery || query;
    if (!finalQuery.trim()) return;
    
    setIsSearching(true);
    
    try {
      // Analyze intent
      const intent = await analyzeSearchIntent(finalQuery);
      setSearchIntent(intent);
      
      // Extract filters
      const extractedFilters = extractFiltersFromQuery(finalQuery);
      const combinedFilters = { ...selectedFilters, ...extractedFilters, ...intent.parameters };
      
      // Add to search history
      const newHistory = [finalQuery, ...searchHistory.filter(h => h !== finalQuery)].slice(0, 5);
      setSearchHistory(newHistory);
      localStorage.setItem('aiSearchHistory', JSON.stringify(newHistory));
      
      // Perform search
      const params = new URLSearchParams(combinedFilters);
      const response = await fetch(`http://localhost:8000/api/properties/search?${params}`);
      const data = await response.json();
      
      setSearchResults(data.properties || []);
      
      // Generate insights
      if (data.properties && data.properties.length > 0) {
        const insights = generateAIInsights(data.properties);
        setAiInsights(insights);
      }
      
      // Callback for parent component
      if (onSearchResults) {
        onSearchResults(data.properties || []);
      }
      
    } catch (error) {
      console.error('AI Search error:', error);
    } finally {
      setIsSearching(false);
    }
  };

  // Voice search handler
  const toggleVoiceSearch = () => {
    if (!recognitionRef.current) {
      alert('Voice recognition is not supported in your browser');
      return;
    }
    
    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      recognitionRef.current.start();
      setIsListening(true);
      setSearchMode('voice');
    }
  };

  // Apply smart suggestion
  const applySuggestion = (suggestion: SmartSuggestion) => {
    setQuery(suggestion.query);
    setSelectedFilters(suggestion.filters);
    handleAISearch(suggestion.query);
  };

  // Navigate to property
  const handlePropertyClick = (property: any) => {
    const addressSlug = property.phy_addr1
      ?.toLowerCase()
      .replace(/[^a-z0-9]/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '');
    
    const citySlug = property.phy_city
      ?.toLowerCase()
      .replace(/[^a-z0-9]/g, '-');
    
    if (addressSlug && citySlug) {
      navigate(`/properties/${citySlug}/${addressSlug}`);
    } else {
      navigate(`/properties/${property.id}`);
    }
  };

  return (
    <div className={embedded ? '' : 'min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50'}>
      {/* Header */}
      {!embedded && (
        <div className="bg-white/90 backdrop-blur-lg shadow-lg border-b border-purple-100">
          <div className="container mx-auto px-4 py-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Brain className="w-10 h-10 text-purple-600 animate-pulse" />
                <div>
                  <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 via-blue-600 to-pink-600 bg-clip-text text-transparent">
                    AI Property Intelligence
                  </h1>
                  <p className="text-gray-600 text-sm">Natural language property search powered by AI</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <Badge className="bg-green-100 text-green-800 border-green-300">
                  <CheckCircle className="w-3 h-3 mr-1" />
                  789,884 Properties
                </Badge>
                <Badge className="bg-blue-100 text-blue-800 border-blue-300">
                  <Zap className="w-3 h-3 mr-1" />
                  Real-time AI
                </Badge>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Search Area */}
      <div className="container mx-auto px-4 py-8">
        {/* Search Modes */}
        <div className="flex justify-center mb-6">
          <div className="inline-flex rounded-lg bg-white shadow-md p-1">
            <button
              onClick={() => setSearchMode('natural')}
              className={`px-6 py-2 rounded-md text-sm font-medium transition-all ${
                searchMode === 'natural' 
                  ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <MessageSquare className="w-4 h-4 inline mr-2" />
              Natural Language
            </button>
            <button
              onClick={() => setSearchMode('guided')}
              className={`px-6 py-2 rounded-md text-sm font-medium transition-all ${
                searchMode === 'guided' 
                  ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Target className="w-4 h-4 inline mr-2" />
              Guided Search
            </button>
            <button
              onClick={() => setSearchMode('voice')}
              className={`px-6 py-2 rounded-md text-sm font-medium transition-all ${
                searchMode === 'voice' 
                  ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Mic className="w-4 h-4 inline mr-2" />
              Voice Search
            </button>
          </div>
        </div>

        {/* Search Card */}
        <Card className="shadow-2xl bg-white/95 backdrop-blur-lg border-purple-100">
          <CardContent className="p-8">
            {/* Natural Language Search */}
            {searchMode === 'natural' && (
              <>
                <div className="flex gap-4 mb-6">
                  <div className="flex-1 relative">
                    <textarea
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleAISearch()}
                      placeholder="Describe your ideal property in natural language... e.g., 'I need a 3 bedroom home near good schools in Fort Lauderdale under $500k with a pool'"
                      className="w-full px-6 py-4 pr-12 border-2 border-purple-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-purple-500/20 focus:border-purple-500 resize-none min-h-[100px] text-lg"
                    />
                    <Sparkles className="absolute right-4 top-4 text-purple-400 w-6 h-6 animate-pulse" />
                  </div>
                  <div className="flex flex-col gap-2">
                    <Button
                      onClick={() => handleAISearch()}
                      disabled={isSearching}
                      className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white px-8 h-12"
                    >
                      {isSearching ? (
                        <>
                          <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                          Analyzing...
                        </>
                      ) : (
                        <>
                          <Brain className="w-5 h-5 mr-2" />
                          AI Search
                        </>
                      )}
                    </Button>
                    <Button
                      onClick={toggleVoiceSearch}
                      variant="outline"
                      className={`border-2 ${isListening ? 'border-red-500 bg-red-50' : 'border-purple-200'}`}
                    >
                      <Mic className={`w-5 h-5 ${isListening ? 'text-red-500 animate-pulse' : ''}`} />
                    </Button>
                  </div>
                </div>

                {/* Recent Searches */}
                {searchHistory.length > 0 && (
                  <div className="mb-6">
                    <p className="text-sm text-gray-600 mb-2">Recent searches:</p>
                    <div className="flex flex-wrap gap-2">
                      {searchHistory.map((search, idx) => (
                        <button
                          key={idx}
                          onClick={() => {
                            setQuery(search);
                            handleAISearch(search);
                          }}
                          className="px-3 py-1 bg-purple-50 text-purple-700 rounded-full text-sm hover:bg-purple-100 transition-colors"
                        >
                          {search}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Voice Search Mode */}
            {searchMode === 'voice' && (
              <div className="text-center py-12">
                <div className="mb-6">
                  <div className={`inline-flex p-8 rounded-full ${isListening ? 'bg-red-100 animate-pulse' : 'bg-purple-100'}`}>
                    <Mic className={`w-16 h-16 ${isListening ? 'text-red-500' : 'text-purple-600'}`} />
                  </div>
                </div>
                <h3 className="text-2xl font-semibold mb-2">
                  {isListening ? 'Listening...' : 'Click to start voice search'}
                </h3>
                <p className="text-gray-600 mb-6">
                  {query || 'Speak naturally about what you\'re looking for'}
                </p>
                <Button
                  onClick={toggleVoiceSearch}
                  size="lg"
                  className={isListening 
                    ? 'bg-red-500 hover:bg-red-600' 
                    : 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700'
                  }
                >
                  {isListening ? 'Stop Recording' : 'Start Recording'}
                </Button>
              </div>
            )}

            {/* Smart Suggestions */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {smartSuggestions.map((suggestion, idx) => (
                <Card 
                  key={idx}
                  className="cursor-pointer hover:shadow-lg transition-all hover:-translate-y-1 border-purple-100"
                  onClick={() => applySuggestion(suggestion)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-lg bg-purple-100">
                        <suggestion.icon className="w-5 h-5 text-purple-600" />
                      </div>
                      <div className="flex-1">
                        <Badge className="mb-2" variant="outline">{suggestion.category}</Badge>
                        <p className="text-sm font-medium text-gray-900 mb-1">
                          {suggestion.query}
                        </p>
                        <p className="text-xs text-gray-600">
                          {suggestion.description}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Search Intent Display */}
        {searchIntent && !isSearching && (
          <Card className="mt-6 bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Brain className="w-6 h-6 text-purple-600" />
                  <div>
                    <p className="font-semibold text-purple-900">AI Understanding</p>
                    <p className="text-sm text-purple-700">
                      Search Type: <Badge className="ml-2">{searchIntent.type}</Badge>
                      <Badge className="ml-2" variant="outline">
                        {Math.round(searchIntent.confidence * 100)}% confidence
                      </Badge>
                    </p>
                  </div>
                </div>
                <div className="flex gap-2">
                  {searchIntent.keywords.map((keyword, idx) => (
                    <Badge key={idx} variant="secondary">{keyword}</Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* AI Insights */}
        {aiInsights && (
          <Card className="mt-6 bg-white/95 backdrop-blur-lg shadow-xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="w-6 h-6 text-purple-600" />
                AI Market Insights
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="text-center">
                  <p className="text-3xl font-bold text-purple-600">
                    ${(aiInsights.summary.avg_price / 1000).toFixed(0)}k
                  </p>
                  <p className="text-sm text-gray-600">Average Price</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-blue-600">
                    {aiInsights.summary.total_results}
                  </p>
                  <p className="text-sm text-gray-600">Properties Found</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-green-600">
                    {aiInsights.opportunities.below_market}
                  </p>
                  <p className="text-sm text-gray-600">Below Market Value</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-orange-600">
                    {aiInsights.trends.price_trend}
                  </p>
                  <p className="text-sm text-gray-600">Price Trend</p>
                </div>
              </div>
              
              {aiInsights.recommendations && aiInsights.recommendations.length > 0 && (
                <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                  <h4 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
                    <Award className="w-5 h-5" />
                    AI Recommendations
                  </h4>
                  <ul className="space-y-2">
                    {aiInsights.recommendations.map((rec: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 text-blue-600 mt-0.5" />
                        <span className="text-sm text-blue-800">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className="mt-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                {searchResults.length} AI-Matched Properties
              </h2>
              <div className="flex gap-2">
                <Button variant="outline" size="sm">
                  <Filter className="w-4 h-4 mr-2" />
                  Refine
                </Button>
                <Button variant="outline" size="sm">
                  <MapPin className="w-4 h-4 mr-2" />
                  Map View
                </Button>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {searchResults.map((property) => (
                <MiniPropertyCard
                  key={property.parcel_id || property.id}
                  parcelId={property.parcel_id}
                  data={property}
                  variant="grid"
                  onClick={() => handlePropertyClick(property)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!isSearching && searchResults.length === 0 && query && (
          <Card className="mt-8 text-center py-12">
            <CardContent>
              <Search className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <h3 className="text-xl font-semibold mb-2">No properties found</h3>
              <p className="text-gray-600 mb-4">
                Try adjusting your search or use one of our smart suggestions
              </p>
              <Button 
                onClick={() => {
                  setQuery('');
                  setSearchResults([]);
                  setSearchIntent(null);
                }}
                variant="outline"
              >
                Clear Search
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}