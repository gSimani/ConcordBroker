import React, { useState } from 'react';
import { Search, Sparkles, Filter, MapPin, Home, DollarSign } from 'lucide-react';
import { AIChatbox } from '../components/ai/AIChatbox';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';

interface SearchResult {
  id: string;
  address: string;
  city: string;
  state: string;
  zip: string;
  price: number;
  bedrooms: number;
  bathrooms: number;
  sqft: number;
  year_built: number;
  property_type: string;
  image_url?: string;
  relevance_score?: number;
}

const AISearchPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [extractedFeatures, setExtractedFeatures] = useState<any>(null);
  const [selectedProperty, setSelectedProperty] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    try {
      const response = await fetch('/api/ai/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery })
      });

      const data = await response.json();
      setSearchResults(data.properties || []);
      setExtractedFeatures(data.extracted_features);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const handlePropertySelect = (propertyId: string) => {
    setSelectedProperty(propertyId);
    // Navigate to property detail page
    window.location.href = `/property/${propertyId}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Sparkles className="w-8 h-8 text-blue-600" />
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                AI Property Search
              </h1>
            </div>
            <p className="text-gray-600">Find your perfect property with AI assistance</p>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="container mx-auto px-4 py-8">
        <Card className="p-6 shadow-xl bg-white/90 backdrop-blur">
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Describe your dream property in natural language..."
                className="w-full px-4 py-3 pr-12 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <Search className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            </div>
            <Button
              onClick={handleSearch}
              disabled={isSearching}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8"
            >
              {isSearching ? 'Searching...' : 'Search'}
            </Button>
          </div>

          {/* Example queries */}
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="text-sm text-gray-500">Try:</span>
            {[
              "3 bedroom house with pool in Miami under $500k",
              "Waterfront property with ocean view",
              "Modern condo near downtown",
              "Investment property with good rental potential"
            ].map((example, idx) => (
              <button
                key={idx}
                onClick={() => setSearchQuery(example)}
                className="text-sm bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded-full transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        </Card>

        {/* Extracted Features */}
        {extractedFeatures && (
          <Card className="mt-6 p-4 bg-blue-50 border-blue-200">
            <h3 className="font-semibold text-blue-900 mb-2">AI Understanding:</h3>
            <div className="flex flex-wrap gap-3">
              {extractedFeatures.location?.length > 0 && (
                <div className="flex items-center gap-1 bg-white px-3 py-1 rounded-full">
                  <MapPin className="w-4 h-4 text-blue-600" />
                  <span className="text-sm">{extractedFeatures.location.join(', ')}</span>
                </div>
              )}
              {extractedFeatures.property_type && (
                <div className="flex items-center gap-1 bg-white px-3 py-1 rounded-full">
                  <Home className="w-4 h-4 text-blue-600" />
                  <span className="text-sm">{extractedFeatures.property_type}</span>
                </div>
              )}
              {extractedFeatures.price_range && (
                <div className="flex items-center gap-1 bg-white px-3 py-1 rounded-full">
                  <DollarSign className="w-4 h-4 text-blue-600" />
                  <span className="text-sm">
                    {extractedFeatures.price_range.min && `$${extractedFeatures.price_range.min.toLocaleString()}`}
                    {extractedFeatures.price_range.min && extractedFeatures.price_range.max && ' - '}
                    {extractedFeatures.price_range.max && `$${extractedFeatures.price_range.max.toLocaleString()}`}
                  </span>
                </div>
              )}
              {extractedFeatures.bedrooms && (
                <div className="bg-white px-3 py-1 rounded-full">
                  <span className="text-sm">{extractedFeatures.bedrooms} Bedrooms</span>
                </div>
              )}
              {extractedFeatures.bathrooms && (
                <div className="bg-white px-3 py-1 rounded-full">
                  <span className="text-sm">{extractedFeatures.bathrooms} Bathrooms</span>
                </div>
              )}
              {extractedFeatures.features?.map((feature: string, idx: number) => (
                <div key={idx} className="bg-white px-3 py-1 rounded-full">
                  <span className="text-sm">{feature}</span>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className="mt-8">
            <h2 className="text-xl font-semibold mb-4">
              Found {searchResults.length} Properties
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {searchResults.map((property) => (
                <Card
                  key={property.id}
                  className="overflow-hidden hover:shadow-xl transition-shadow cursor-pointer"
                  onClick={() => handlePropertySelect(property.id)}
                >
                  {property.image_url && (
                    <img
                      src={property.image_url}
                      alt={property.address}
                      className="w-full h-48 object-cover"
                    />
                  )}
                  <div className="p-4">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-semibold text-lg">{property.address}</h3>
                      {property.relevance_score && (
                        <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                          {property.relevance_score}% match
                        </span>
                      )}
                    </div>
                    <p className="text-gray-600 text-sm mb-2">
                      {property.city}, {property.state} {property.zip}
                    </p>
                    <p className="text-2xl font-bold text-blue-600 mb-3">
                      ${property.price.toLocaleString()}
                    </p>
                    <div className="flex justify-between text-sm text-gray-500">
                      <span>{property.bedrooms} beds</span>
                      <span>{property.bathrooms} baths</span>
                      <span>{property.sqft.toLocaleString()} sqft</span>
                    </div>
                    <div className="mt-3 pt-3 border-t">
                      <div className="flex justify-between text-xs text-gray-400">
                        <span>{property.property_type}</span>
                        <span>Built {property.year_built}</span>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* No Results */}
        {searchResults.length === 0 && extractedFeatures && (
          <div className="mt-8 text-center">
            <p className="text-gray-500">No properties found matching your criteria.</p>
            <p className="text-sm text-gray-400 mt-2">Try adjusting your search terms or using the AI chat for assistance.</p>
          </div>
        )}
      </div>

      {/* AI Chatbox */}
      <AIChatbox
        position="bottom-right"
        initialOpen={false}
        onPropertySelect={handlePropertySelect}
      />
    </div>
  );
};

export default AISearchPage;