import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Send, Bot, User, Loader2, Sparkles, X, Minimize2, Maximize2, RefreshCw, ThumbsUp, ThumbsDown } from 'lucide-react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';

interface Message {
  id: string;
  type: 'user' | 'assistant' | 'system' | 'property_card' | 'typing';
  content: string;
  properties?: any[];
  timestamp: Date;
  rating?: number;
}

interface PropertyCard {
  id: string;
  address: string;
  city: string;
  price: number;
  bedrooms?: number;
  bathrooms?: number;
  sqft?: number;
  year_built?: number;
  score?: number;
}

interface AIChatboxProps {
  position?: 'bottom-right' | 'bottom-left' | 'center';
  initialOpen?: boolean;
  onPropertySelect?: (propertyId: string) => void;
}

export const AIChatbox: React.FC<AIChatboxProps> = ({
  position = 'bottom-right',
  initialOpen = false,
  onPropertySelect
}) => {
  const [isOpen, setIsOpen] = useState(initialOpen);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [conversationId, setConversationId] = useState<string>('');
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // WebSocket connection
  useEffect(() => {
    if (isOpen && !ws) {
      const clientId = Math.random().toString(36).substring(7);
      const websocket = new WebSocket(`ws://localhost:8000/api/ai/chat/${clientId}`);

      websocket.onopen = () => {
        setIsConnected(true);
        console.log('Connected to AI Assistant');
      };

      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };

      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };

      websocket.onclose = () => {
        setIsConnected(false);
        console.log('Disconnected from AI Assistant');
      };

      setWs(websocket);
    }

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [isOpen]);

  // Handle WebSocket messages
  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'system':
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          type: 'system',
          content: data.message,
          timestamp: new Date(data.timestamp)
        }]);
        setConversationId(data.conversation_id);
        break;

      case 'typing':
        setIsTyping(true);
        break;

      case 'assistant':
        setIsTyping(false);
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          type: 'assistant',
          content: data.message,
          properties: data.properties,
          timestamp: new Date(data.timestamp)
        }]);
        break;

      case 'property_card':
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          type: 'property_card',
          content: '',
          properties: [data.property],
          timestamp: new Date(data.timestamp)
        }]);
        break;

      case 'error':
        setIsTyping(false);
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          type: 'system',
          content: data.message,
          timestamp: new Date(data.timestamp)
        }]);
        break;
    }
  };

  // Send message
  const sendMessage = () => {
    if (!inputValue.trim() || !ws || !isConnected) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    
    ws.send(JSON.stringify({
      message: inputValue,
      conversation_id: conversationId
    }));

    setInputValue('');
  };

  // Fetch suggestions
  const fetchSuggestions = async (query: string) => {
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }

    try {
      const response = await fetch(`/api/ai/suggestions?q=${encodeURIComponent(query)}`);
      const data = await response.json();
      setSuggestions(data.suggestions || []);
    } catch (error) {
      console.error('Error fetching suggestions:', error);
    }
  };

  // Handle input change with debounced suggestions
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setInputValue(value);
    
    // Debounce suggestions
    const timeoutId = setTimeout(() => {
      fetchSuggestions(value);
    }, 300);

    return () => clearTimeout(timeoutId);
  };

  // Rate message
  const rateMessage = (messageId: string, rating: number) => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId ? { ...msg, rating } : msg
    ));

    // Send feedback to backend
    fetch('/api/ai/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conversation_id: conversationId,
        rating,
        message_id: messageId
      })
    });
  };

  // Clear conversation
  const clearConversation = () => {
    setMessages([{
      id: Date.now().toString(),
      type: 'system',
      content: 'Conversation cleared. How can I help you find your perfect property?',
      timestamp: new Date()
    }]);

    if (conversationId) {
      fetch(`/api/ai/conversation/${conversationId}`, {
        method: 'DELETE'
      });
    }
  };

  // Position classes
  const positionClasses = {
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'center': 'bottom-4 left-1/2 transform -translate-x-1/2'
  };

  // Property card component
  const PropertyCardComponent: React.FC<{ property: PropertyCard }> = ({ property }) => (
    <Card className="p-3 mb-2 cursor-pointer hover:shadow-lg transition-shadow"
          onClick={() => onPropertySelect?.(property.id)}>
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <h4 className="font-semibold text-sm">{property.address}</h4>
          <p className="text-xs text-gray-600">{property.city}</p>
          <p className="text-lg font-bold text-blue-600">${property.price.toLocaleString()}</p>
          <div className="flex gap-3 text-xs text-gray-500 mt-1">
            {property.bedrooms && <span>{property.bedrooms} beds</span>}
            {property.bathrooms && <span>{property.bathrooms} baths</span>}
            {property.sqft && <span>{property.sqft.toLocaleString()} sqft</span>}
          </div>
        </div>
        {property.score && (
          <div className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
            {property.score}% match
          </div>
        )}
      </div>
    </Card>
  );

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className={`fixed ${positionClasses[position]} z-50 bg-blue-600 text-white p-4 rounded-full shadow-lg hover:bg-blue-700 transition-all hover:scale-110`}
      >
        <Sparkles className="w-6 h-6" />
      </button>
    );
  }

  return (
    <div className={`fixed ${positionClasses[position]} z-50 ${isMinimized ? 'w-80' : 'w-96'} transition-all`}>
      <Card className={`${isMinimized ? 'h-16' : 'h-[600px]'} flex flex-col shadow-2xl transition-all`}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-t-lg">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5" />
            <span className="font-semibold">AI Property Assistant</span>
            {isConnected && <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={clearConversation}
              className="hover:bg-white/20 p-1 rounded transition-colors"
              title="Clear conversation"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              onClick={() => setIsMinimized(!isMinimized)}
              className="hover:bg-white/20 p-1 rounded transition-colors"
            >
              {isMinimized ? <Maximize2 className="w-4 h-4" /> : <Minimize2 className="w-4 h-4" />}
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className="hover:bg-white/20 p-1 rounded transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {!isMinimized && (
          <>
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {message.type === 'user' ? (
                    <div className="flex items-start gap-2 max-w-[80%]">
                      <div className="bg-blue-600 text-white p-3 rounded-lg rounded-br-none">
                        <p className="text-sm">{message.content}</p>
                      </div>
                      <User className="w-8 h-8 p-1.5 bg-gray-200 rounded-full" />
                    </div>
                  ) : message.type === 'assistant' ? (
                    <div className="flex items-start gap-2 max-w-[80%]">
                      <Bot className="w-8 h-8 p-1.5 bg-gradient-to-br from-blue-500 to-purple-500 text-white rounded-full" />
                      <div>
                        <div className="bg-gray-100 p-3 rounded-lg rounded-bl-none">
                          <p className="text-sm">{message.content}</p>
                        </div>
                        {message.properties && message.properties.length > 0 && (
                          <div className="mt-2 space-y-2">
                            {message.properties.map((prop, idx) => (
                              <PropertyCardComponent key={idx} property={prop} />
                            ))}
                          </div>
                        )}
                        <div className="flex gap-2 mt-2">
                          <button
                            onClick={() => rateMessage(message.id, 1)}
                            className={`p-1 rounded ${message.rating === 1 ? 'bg-green-100 text-green-600' : 'hover:bg-gray-100'}`}
                          >
                            <ThumbsUp className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => rateMessage(message.id, -1)}
                            className={`p-1 rounded ${message.rating === -1 ? 'bg-red-100 text-red-600' : 'hover:bg-gray-100'}`}
                          >
                            <ThumbsDown className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ) : message.type === 'property_card' && message.properties ? (
                    <div className="w-full">
                      {message.properties.map((prop, idx) => (
                        <PropertyCardComponent key={idx} property={prop} />
                      ))}
                    </div>
                  ) : (
                    <div className="text-center text-sm text-gray-500 italic">
                      {message.content}
                    </div>
                  )}
                </div>
              ))}

              {isTyping && (
                <div className="flex items-center gap-2">
                  <Bot className="w-8 h-8 p-1.5 bg-gradient-to-br from-blue-500 to-purple-500 text-white rounded-full" />
                  <div className="bg-gray-100 p-3 rounded-lg">
                    <Loader2 className="w-4 h-4 animate-spin" />
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Suggestions */}
            {suggestions.length > 0 && (
              <div className="px-4 py-2 border-t">
                <p className="text-xs text-gray-500 mb-2">Suggestions:</p>
                <div className="flex flex-wrap gap-2">
                  {suggestions.slice(0, 3).map((suggestion, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        setInputValue(suggestion);
                        setSuggestions([]);
                        inputRef.current?.focus();
                      }}
                      className="text-xs bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded-full transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Input */}
            <div className="p-4 border-t">
              <div className="flex gap-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={inputValue}
                  onChange={handleInputChange}
                  onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                  placeholder="Ask about properties..."
                  className="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={!isConnected}
                />
                <Button
                  onClick={sendMessage}
                  disabled={!inputValue.trim() || !isConnected}
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
              {!isConnected && (
                <p className="text-xs text-red-500 mt-2">Connecting to AI Assistant...</p>
              )}
            </div>
          </>
        )}
      </Card>
    </div>
  );
};