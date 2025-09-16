import React, { useState, useCallback } from 'react';
import { Search, Sparkles, Brain, Loader2, X } from 'lucide-react';
import { debounce } from 'lodash';

interface AISearchBarProps {
  onSearch: (query: string, aiResults?: any) => void;
  placeholder?: string;
}

export const AISearchBar: React.FC<AISearchBarProps> = ({ 
  onSearch, 
  placeholder = "Search with AI: 'waterfront home with modern kitchen' or 'investment property under 500k'" 
}) => {
  const [query, setQuery] = useState('');
  const [isAIMode, setIsAIMode] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // AI-powered semantic search
  const performSemanticSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) return;
    
    setIsProcessing(true);
    try {
      const response = await fetch('http://localhost:8000/api/ai/semantic-search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: searchQuery,
          max_results: 10
        }),
      });

      if (response.ok) {
        const data = await response.json();
        onSearch(searchQuery, data);
        
        // Generate suggestions based on the query
        generateSuggestions(searchQuery);
      } else {
        // Fallback to regular search
        onSearch(searchQuery);
      }
    } catch (error) {
      console.error('AI search error:', error);
      // Fallback to regular search
      onSearch(searchQuery);
    } finally {
      setIsProcessing(false);
    }
  };

  // Generate smart suggestions
  const generateSuggestions = (searchQuery: string) => {
    const smartSuggestions = [
      `${searchQuery} with pool`,
      `${searchQuery} near schools`,
      `${searchQuery} recently renovated`,
      `luxury ${searchQuery}`,
      `affordable ${searchQuery}`,
    ];
    setSuggestions(smartSuggestions.slice(0, 3));
    setShowSuggestions(true);
  };

  // Debounced search
  const debouncedSearch = useCallback(
    debounce((searchQuery: string) => {
      if (isAIMode) {
        performSemanticSearch(searchQuery);
      } else {
        onSearch(searchQuery);
      }
    }, 500),
    [isAIMode]
  );

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    
    if (value.length > 2) {
      debouncedSearch(value);
    } else {
      setShowSuggestions(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (isAIMode) {
      performSemanticSearch(query);
    } else {
      onSearch(query);
    }
    setShowSuggestions(false);
  };

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    performSemanticSearch(suggestion);
    setShowSuggestions(false);
  };

  const clearSearch = () => {
    setQuery('');
    setSuggestions([]);
    setShowSuggestions(false);
    onSearch('');
  };

  return (
    <div className="relative w-full">
      <form onSubmit={handleSearch} className="relative">
        <div className="relative flex items-center">
          {/* AI Mode Toggle */}
          <button
            type="button"
            onClick={() => setIsAIMode(!isAIMode)}
            className={`absolute left-3 p-1.5 rounded-lg transition-all z-10 ${
              isAIMode 
                ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white shadow-lg' 
                : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
            }`}
            title={isAIMode ? 'AI Search Enabled' : 'Standard Search'}
          >
            {isAIMode ? (
              <Brain className="w-5 h-5" />
            ) : (
              <Search className="w-5 h-5" />
            )}
          </button>

          {/* Search Input */}
          <input
            type="text"
            value={query}
            onChange={handleInputChange}
            placeholder={placeholder}
            autoComplete="off"
            className={`w-full pl-14 pr-10 py-3 text-sm border rounded-xl transition-all ${
              isAIMode 
                ? 'border-purple-300 focus:border-purple-500 focus:ring-2 focus:ring-purple-200' 
                : 'border-gray-300 focus:border-gray-500 focus:ring-2 focus:ring-gray-200'
            } outline-none`}
          />

          {/* Clear Button */}
          {query && (
            <button
              type="button"
              onClick={clearSearch}
              className="absolute right-3 p-1 text-gray-400 hover:text-gray-600"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* AI Mode Indicator */}
        {isAIMode && (
          <div className="absolute -bottom-6 left-0 flex items-center gap-1 text-xs text-purple-600">
            <Sparkles className="w-3 h-3" />
            <span>AI-powered semantic search active</span>
          </div>
        )}
      </form>

      {/* Smart Suggestions */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute top-full mt-2 w-full bg-white border border-gray-200 rounded-xl shadow-lg z-50">
          <div className="p-2">
            <div className="flex items-center gap-2 px-3 py-2 text-xs text-gray-500">
              <Sparkles className="w-3 h-3" />
              <span>AI Suggestions</span>
            </div>
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(suggestion)}
                className="w-full text-left px-3 py-2 text-sm hover:bg-purple-50 rounded-lg transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Example Searches */}
      <div className="mt-8 flex flex-wrap gap-2">
        <span className="text-xs text-gray-500">Try:</span>
        {[
          'luxury waterfront estate',
          'family home near schools',
          'investment property with high ROI',
          'modern condo downtown'
        ].map((example) => (
          <button
            key={example}
            onClick={() => {
              setQuery(example);
              performSemanticSearch(example);
            }}
            className="px-3 py-1 text-xs bg-purple-100 text-purple-700 rounded-full hover:bg-purple-200 transition-colors"
          >
            {example}
          </button>
        ))}
      </div>
    </div>
  );
};