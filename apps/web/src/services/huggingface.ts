/**
 * HuggingFace AI Service for Frontend
 * Provides AI-powered features for property analysis
 */

interface PropertyData {
  address: string;
  bedrooms?: number;
  bathrooms?: number;
  squareFeet?: number;
  propertyType?: string;
  features?: string[];
}

interface MarketSentiment {
  sentiment: 'bullish' | 'bearish' | 'neutral';
  confidence: number;
}

class HuggingFaceService {
  private apiToken: string;
  private baseUrl: string = 'https://api-inference.huggingface.co';
  private wsConnection: WebSocket | null = null;

  constructor() {
    this.apiToken = import.meta.env.VITE_HUGGINGFACE_API_TOKEN || '';
    
    if (!this.apiToken) {
      console.warn('HuggingFace API token not configured');
    }
  }

  /**
   * Connect to HuggingFace MCP WebSocket
   */
  connectWebSocket(): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsUrl = import.meta.env.VITE_MCP_WEBSOCKET_URL || 'ws://localhost:8765';
      
      this.wsConnection = new WebSocket(wsUrl);
      
      this.wsConnection.onopen = () => {
        console.log('Connected to HuggingFace MCP');
        resolve();
      };
      
      this.wsConnection.onerror = (error) => {
        console.error('WebSocket error:', error);
        reject(error);
      };
      
      this.wsConnection.onmessage = (event) => {
        console.log('Received from MCP:', event.data);
      };
    });
  }

  /**
   * Generate AI-powered property description
   */
  async generatePropertyDescription(property: PropertyData): Promise<string> {
    if (!this.apiToken) {
      return this.generateFallbackDescription(property);
    }

    const prompt = this.createPropertyPrompt(property);
    const model = import.meta.env.VITE_HF_PROPERTY_DESC_MODEL || 'gpt2';

    try {
      const response = await fetch(`${this.baseUrl}/models/${model}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.apiToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          inputs: prompt,
          parameters: {
            max_length: 200,
            temperature: 0.7,
            top_p: 0.9,
          },
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data[0]?.generated_text || this.generateFallbackDescription(property);
    } catch (error) {
      console.error('Error generating property description:', error);
      return this.generateFallbackDescription(property);
    }
  }

  /**
   * Analyze market sentiment for a location
   */
  async analyzeMarketSentiment(location: string, propertyType: string): Promise<MarketSentiment> {
    if (!this.apiToken) {
      return { sentiment: 'neutral', confidence: 0.5 };
    }

    const text = `Real estate market analysis for ${propertyType} properties in ${location}`;
    const model = import.meta.env.VITE_HF_MARKET_ANALYSIS_MODEL || 'facebook/bart-large-mnli';

    try {
      const response = await fetch(`${this.baseUrl}/models/${model}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.apiToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          inputs: text,
          parameters: {
            candidate_labels: ['bullish', 'bearish', 'neutral'],
            multi_label: false,
          },
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        sentiment: (data.labels?.[0] || 'neutral') as MarketSentiment['sentiment'],
        confidence: data.scores?.[0] || 0.5,
      };
    } catch (error) {
      console.error('Error analyzing market sentiment:', error);
      return { sentiment: 'neutral', confidence: 0.5 };
    }
  }

  /**
   * Create embeddings for property features
   */
  async createEmbeddings(features: string[]): Promise<number[]> {
    if (!this.apiToken) {
      return [];
    }

    const model = import.meta.env.VITE_HF_EMBEDDING_MODEL || 'sentence-transformers/all-MiniLM-L6-v2';

    try {
      const response = await fetch(`${this.baseUrl}/models/${model}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.apiToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          inputs: features.join(' '),
          options: { wait_for_model: true },
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return Array.isArray(data) ? data : [];
    } catch (error) {
      console.error('Error creating embeddings:', error);
      return [];
    }
  }

  /**
   * Send message via WebSocket
   */
  sendWebSocketMessage(action: string, payload: any): Promise<any> {
    return new Promise((resolve, reject) => {
      if (!this.wsConnection || this.wsConnection.readyState !== WebSocket.OPEN) {
        reject(new Error('WebSocket not connected'));
        return;
      }

      const messageId = Date.now().toString();
      
      const handleResponse = (event: MessageEvent) => {
        const data = JSON.parse(event.data);
        if (data.messageId === messageId) {
          this.wsConnection?.removeEventListener('message', handleResponse);
          resolve(data.response);
        }
      };

      this.wsConnection.addEventListener('message', handleResponse);
      
      this.wsConnection.send(JSON.stringify({
        messageId,
        action,
        payload,
      }));

      // Timeout after 30 seconds
      setTimeout(() => {
        this.wsConnection?.removeEventListener('message', handleResponse);
        reject(new Error('WebSocket request timeout'));
      }, 30000);
    });
  }

  /**
   * Create property description prompt
   */
  private createPropertyPrompt(property: PropertyData): string {
    const { address, bedrooms = 0, bathrooms = 0, squareFeet = 0, propertyType = 'property', features = [] } = property;
    
    return `Generate a compelling real estate description for:
    Address: ${address}
    Type: ${propertyType}
    Bedrooms: ${bedrooms}
    Bathrooms: ${bathrooms}
    Size: ${squareFeet} sq ft
    Features: ${features.join(', ')}
    
    Description:`;
  }

  /**
   * Generate fallback description when AI is unavailable
   */
  private generateFallbackDescription(property: PropertyData): string {
    const { address, bedrooms, bathrooms, squareFeet, propertyType = 'property' } = property;
    
    let description = `Beautiful ${propertyType} located at ${address}.`;
    
    if (bedrooms && bathrooms) {
      description += ` Features ${bedrooms} bedrooms and ${bathrooms} bathrooms.`;
    }
    
    if (squareFeet) {
      description += ` Spacious ${squareFeet} square feet of living space.`;
    }
    
    description += ' Contact us for more details and to schedule a viewing.';
    
    return description;
  }

  /**
   * Disconnect WebSocket
   */
  disconnect(): void {
    if (this.wsConnection) {
      this.wsConnection.close();
      this.wsConnection = null;
    }
  }
}

// Export singleton instance
export const huggingFaceService = new HuggingFaceService();
export type { PropertyData, MarketSentiment };