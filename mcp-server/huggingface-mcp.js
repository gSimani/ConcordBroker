/**
 * HuggingFace MCP Server Integration
 * Provides AI capabilities through HuggingFace models
 */

const axios = require('axios');
const WebSocket = require('ws');
const dotenv = require('dotenv');
const path = require('path');

// Load HuggingFace environment variables
dotenv.config({ path: path.join(__dirname, '..', '.env.huggingface') });

class HuggingFaceMCP {
    constructor() {
        this.apiToken = process.env.HUGGINGFACE_API_TOKEN;
        this.baseUrl = process.env.HUGGINGFACE_BASE_URL || 'https://api-inference.huggingface.co';
        this.organization = process.env.HUGGINGFACE_ORG || 'Concord Broker';
        
        if (!this.apiToken) {
            throw new Error('HUGGINGFACE_API_TOKEN is required');
        }
        
        this.headers = {
            'Authorization': `Bearer ${this.apiToken}`,
            'Content-Type': 'application/json'
        };
        
        this.models = {
            embedding: process.env.HF_EMBEDDING_MODEL || 'sentence-transformers/all-MiniLM-L6-v2',
            textGeneration: process.env.HF_TEXT_MODEL || 'gpt2',
            classification: process.env.HF_CLASSIFICATION_MODEL || 'distilbert-base-uncased-finetuned-sst-2-english',
            propertyDesc: process.env.HF_PROPERTY_DESC_MODEL || 'gpt2',
            marketAnalysis: process.env.HF_MARKET_ANALYSIS_MODEL || 'facebook/bart-large-mnli'
        };
    }
    
    /**
     * Initialize MCP connection
     */
    async connect() {
        console.log(`🤖 Connecting to HuggingFace MCP...`);
        console.log(`📍 Organization: ${this.organization}`);
        console.log(`🔗 Base URL: ${this.baseUrl}`);
        
        // Test connection with a simple API call
        try {
            const response = await axios.get(
                `${this.baseUrl}/models/${this.models.embedding}`,
                { headers: this.headers }
            );
            
            console.log('✅ HuggingFace MCP connected successfully');
            return true;
        } catch (error) {
            console.error('❌ Failed to connect to HuggingFace:', error.message);
            return false;
        }
    }
    
    /**
     * Generate property description using AI
     */
    async generatePropertyDescription(propertyData) {
        const prompt = this._createPropertyPrompt(propertyData);
        
        try {
            const response = await axios.post(
                `${this.baseUrl}/models/${this.models.propertyDesc}`,
                {
                    inputs: prompt,
                    parameters: {
                        max_length: 200,
                        temperature: 0.7,
                        top_p: 0.9
                    }
                },
                { headers: this.headers }
            );
            
            return response.data[0]?.generated_text || '';
        } catch (error) {
            console.error('Error generating property description:', error);
            throw error;
        }
    }
    
    /**
     * Create embeddings for property features
     */
    async createEmbeddings(features) {
        try {
            const response = await axios.post(
                `${this.baseUrl}/models/${this.models.embedding}`,
                {
                    inputs: features.join(' '),
                    options: { wait_for_model: true }
                },
                { headers: this.headers }
            );
            
            return response.data;
        } catch (error) {
            console.error('Error creating embeddings:', error);
            throw error;
        }
    }
    
    /**
     * Analyze market sentiment
     */
    async analyzeMarketSentiment(location, propertyType) {
        const text = `Real estate market analysis for ${propertyType} properties in ${location}`;
        
        try {
            const response = await axios.post(
                `${this.baseUrl}/models/${this.models.marketAnalysis}`,
                {
                    inputs: text,
                    parameters: {
                        candidate_labels: ['bullish', 'bearish', 'neutral'],
                        multi_label: false
                    }
                },
                { headers: this.headers }
            );
            
            return {
                sentiment: response.data.labels?.[0] || 'neutral',
                confidence: response.data.scores?.[0] || 0.5
            };
        } catch (error) {
            console.error('Error analyzing market sentiment:', error);
            throw error;
        }
    }
    
    /**
     * Classify property inquiry
     */
    async classifyInquiry(inquiry) {
        try {
            const response = await axios.post(
                `${this.baseUrl}/models/${this.models.classification}`,
                {
                    inputs: inquiry,
                    options: { wait_for_model: true }
                },
                { headers: this.headers }
            );
            
            const result = response.data[0]?.[0] || response.data[0] || {};
            return {
                intent: result.label || 'unknown',
                confidence: result.score || 0.0
            };
        } catch (error) {
            console.error('Error classifying inquiry:', error);
            throw error;
        }
    }
    
    /**
     * Create property description prompt
     */
    _createPropertyPrompt(propertyData) {
        const {
            address = 'Unknown address',
            bedrooms = 0,
            bathrooms = 0,
            square_feet = 0,
            property_type = 'property',
            features = []
        } = propertyData;
        
        return `Generate a compelling real estate description for:
        Address: ${address}
        Type: ${property_type}
        Bedrooms: ${bedrooms}
        Bathrooms: ${bathrooms}
        Size: ${square_feet} sq ft
        Features: ${features.join(', ')}
        
        Description:`;
    }
    
    /**
     * Setup WebSocket for real-time AI responses
     */
    setupWebSocket(port = 8765) {
        const wss = new WebSocket.Server({ port });
        
        wss.on('connection', (ws) => {
            console.log('🔌 New WebSocket connection for HuggingFace MCP');
            
            ws.on('message', async (message) => {
                try {
                    const data = JSON.parse(message);
                    let response;
                    
                    switch (data.action) {
                        case 'generateDescription':
                            response = await this.generatePropertyDescription(data.payload);
                            break;
                        case 'createEmbeddings':
                            response = await this.createEmbeddings(data.payload);
                            break;
                        case 'analyzeMarket':
                            response = await this.analyzeMarketSentiment(
                                data.payload.location,
                                data.payload.propertyType
                            );
                            break;
                        case 'classifyInquiry':
                            response = await this.classifyInquiry(data.payload);
                            break;
                        default:
                            response = { error: 'Unknown action' };
                    }
                    
                    ws.send(JSON.stringify({
                        action: data.action,
                        response
                    }));
                } catch (error) {
                    ws.send(JSON.stringify({
                        error: error.message
                    }));
                }
            });
            
            ws.on('close', () => {
                console.log('🔌 WebSocket connection closed');
            });
        });
        
        console.log(`🚀 HuggingFace MCP WebSocket server running on port ${port}`);
    }
}

// Export for use in other modules
module.exports = HuggingFaceMCP;

// Run if executed directly
if (require.main === module) {
    const mcp = new HuggingFaceMCP();
    
    (async () => {
        const connected = await mcp.connect();
        
        if (connected) {
            // Setup WebSocket server
            mcp.setupWebSocket();
            
            // Test functionality
            console.log('\n🧪 Testing HuggingFace capabilities...\n');
            
            // Test property description generation
            const testProperty = {
                address: '123 Main St, Miami, FL',
                bedrooms: 3,
                bathrooms: 2,
                square_feet: 2000,
                property_type: 'Single Family Home',
                features: ['Pool', 'Garden', 'Garage']
            };
            
            try {
                console.log('📝 Testing property description generation...');
                const description = await mcp.generatePropertyDescription(testProperty);
                console.log('Generated Description:', description);
                
                console.log('\n📊 Testing market sentiment analysis...');
                const sentiment = await mcp.analyzeMarketSentiment('Miami', 'residential');
                console.log('Market Sentiment:', sentiment);
                
                console.log('\n✅ All tests completed successfully!');
            } catch (error) {
                console.error('❌ Test failed:', error.message);
            }
        }
    })();
}