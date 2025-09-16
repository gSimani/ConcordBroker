/**
 * LangChain Integration for MCP Server
 * Provides WebSocket and REST API endpoints for LangChain agents
 */

const axios = require('axios');
const { WebSocket } = require('ws');
const { EventEmitter } = require('events');

class LangChainIntegration extends EventEmitter {
    constructor(config = {}) {
        super();
        
        this.config = {
            langchainApiUrl: config.langchainApiUrl || 'http://localhost:8003',
            langsmithApiKey: config.langsmithApiKey || process.env.LANGSMITH_API_KEY,
            openaiApiKey: config.openaiApiKey || process.env.OPENAI_API_KEY,
            ...config
        };
        
        this.agents = {
            propertyAnalysis: null,
            investmentAdvisor: null,
            dataResearch: null,
            marketAnalysis: null,
            legalCompliance: null
        };
        
        this.wsConnections = new Map();
        this.activeChats = new Map();

        // Axios instance with x-request-id propagation
        this.http = axios.create();
        this.http.interceptors.request.use((config) => {
            const rid = `${Date.now()}-${Math.floor(Math.random()*1e6)}`;
            config.headers = config.headers || {};
            config.headers['x-request-id'] = config.headers['x-request-id'] || rid;
            return config;
        });
    }
    
    /**
     * Initialize LangChain connection
     */
    async initialize() {
        try {
            console.log('🤖 Initializing LangChain integration...');
            
            // Test connection to LangChain API
            const response = await this.http.get(`${this.config.langchainApiUrl}/health`);
            
            if (response.data.status === 'healthy') {
                console.log('✅ LangChain API is healthy');
                
                // Initialize agents
                await this.initializeAgents();
                
                // Set up LangSmith tracing
                this.setupLangSmithTracing();
                
                this.emit('initialized', { status: 'success' });
                return true;
            }
        } catch (error) {
            console.error('❌ Failed to initialize LangChain:', error.message);
            
            // Try to start the LangChain API server
            await this.startLangChainServer();
            
            this.emit('initialized', { status: 'error', error: error.message });
            return false;
        }
    }
    
    /**
     * Start the LangChain API server if not running
     */
    async startLangChainServer() {
        console.log('🚀 Starting LangChain API server...');
        
        const { spawn } = await import('child_process');
        
        this.langchainProcess = spawn('python', [
            'apps/api/langchain_api.py'
        ], {
            cwd: process.cwd().replace('mcp-server', ''),
            env: {
                ...process.env,
                LANGSMITH_API_KEY: this.config.langsmithApiKey,
                OPENAI_API_KEY: this.config.openaiApiKey
            }
        });
        
        this.langchainProcess.stdout.on('data', (data) => {
            console.log(`LangChain API: ${data}`);
        });
        
        this.langchainProcess.stderr.on('data', (data) => {
            console.error(`LangChain API Error: ${data}`);
        });
        
        // Wait for server to start
        await new Promise(resolve => setTimeout(resolve, 5000));
        
        // Retry initialization
        await this.initialize();
    }
    
    /**
     * Initialize all LangChain agents
     */
    async initializeAgents() {
        try {
            const agentTypes = [
                'property_analysis',
                'investment_advisor',
                'data_research',
                'market_analysis',
                'legal_compliance'
            ];
            
            for (const agentType of agentTypes) {
                const response = await this.http.post(
                    `${this.config.langchainApiUrl}/agents/initialize`,
                    { agent_type: agentType }
                );
                
                if (response.data.status === 'initialized') {
                    this.agents[this.toCamelCase(agentType)] = {
                        id: response.data.agent_id,
                        type: agentType,
                        status: 'ready'
                    };
                    
                    console.log(`✅ Initialized ${agentType} agent`);
                }
            }
        } catch (error) {
            console.error('Error initializing agents:', error.message);
        }
    }
    
    /**
     * Setup LangSmith tracing
     */
    setupLangSmithTracing() {
        // Configure LangSmith for monitoring
        this.langsmithConfig = {
            apiKey: this.config.langsmithApiKey,
            projectName: 'concordbroker-property-analysis',
            enabled: true
        };
        
        console.log('📊 LangSmith tracing configured');
    }
    
    /**
     * Analyze a property using LangChain agents
     */
    async analyzeProperty(parcelId, analysisType = 'comprehensive') {
        try {
            const response = await this.http.post(
                `${this.config.langchainApiUrl}/analyze/property`,
                {
                    parcel_id: parcelId,
                    analysis_type: analysisType,
                    include_recommendations: true,
                    include_comparables: true
                }
            );
            
            return {
                success: true,
                data: response.data
            };
        } catch (error) {
            console.error('Property analysis error:', error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Get investment advice for a property
     */
    async getInvestmentAdvice(propertyData, investorProfile) {
        try {
            const response = await this.http.post(
                `${this.config.langchainApiUrl}/advice/investment`,
                {
                    property_data: propertyData,
                    investor_profile: investorProfile,
                    market_conditions: await this.getMarketConditions()
                }
            );
            
            return {
                success: true,
                advice: response.data
            };
        } catch (error) {
            console.error('Investment advice error:', error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Research property data
     */
    async researchProperty(query, researchType = 'general') {
        try {
            const response = await this.http.post(
                `${this.config.langchainApiUrl}/research/property`,
                {
                    query: query,
                    research_type: researchType,
                    include_sources: true
                }
            );
            
            return {
                success: true,
                findings: response.data
            };
        } catch (error) {
            console.error('Research error:', error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Analyze market conditions
     */
    async analyzeMarket(location, timeframe = 'current') {
        try {
            const response = await this.http.post(
                `${this.config.langchainApiUrl}/analyze/market`,
                {
                    location: location,
                    timeframe: timeframe,
                    include_projections: true
                }
            );
            
            return {
                success: true,
                analysis: response.data
            };
        } catch (error) {
            console.error('Market analysis error:', error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Check legal compliance
     */
    async checkCompliance(propertyData, checkType = 'general') {
        try {
            const response = await this.http.post(
                `${this.config.langchainApiUrl}/compliance/check`,
                {
                    property_data: propertyData,
                    check_type: checkType,
                    include_recommendations: true
                }
            );
            
            return {
                success: true,
                compliance: response.data
            };
        } catch (error) {
            console.error('Compliance check error:', error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Chat with LangChain agent
     */
    async chat(sessionId, message, agentType = 'property_analysis') {
        try {
            // Get or create chat session
            if (!this.activeChats.has(sessionId)) {
                this.activeChats.set(sessionId, {
                    agent: agentType,
                    history: [],
                    context: {}
                });
            }
            
            const session = this.activeChats.get(sessionId);
            
            const response = await this.http.post(
                `${this.config.langchainApiUrl}/chat`,
                {
                    session_id: sessionId,
                    message: message,
                    agent_type: agentType,
                    history: session.history,
                    context: session.context
                }
            );
            
            // Update session history
            session.history.push({
                user: message,
                assistant: response.data.response
            });
            
            return {
                success: true,
                response: response.data.response,
                metadata: response.data.metadata
            };
        } catch (error) {
            console.error('Chat error:', error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Create a RAG pipeline for documents
     */
    async createRAGPipeline(documentPath, pipelineName) {
        try {
            const response = await axios.post(
                `${this.config.langchainApiUrl}/rag/create`,
                {
                    document_path: documentPath,
                    pipeline_name: pipelineName,
                    chunk_size: 1000,
                    chunk_overlap: 200
                }
            );
            
            return {
                success: true,
                pipeline: response.data
            };
        } catch (error) {
            console.error('RAG pipeline error:', error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Query knowledge base
     */
    async queryKnowledgeBase(query, knowledgeBase = 'properties') {
        try {
            const response = await axios.post(
                `${this.config.langchainApiUrl}/knowledge/query`,
                {
                    query: query,
                    knowledge_base: knowledgeBase,
                    k: 5
                }
            );
            
            return {
                success: true,
                results: response.data
            };
        } catch (error) {
            console.error('Knowledge base query error:', error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Get agent metrics
     */
    async getMetrics() {
        try {
            const response = await axios.get(
                `${this.config.langchainApiUrl}/metrics`
            );
            
            return {
                success: true,
                metrics: response.data
            };
        } catch (error) {
            console.error('Metrics error:', error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Get current market conditions
     */
    async getMarketConditions() {
        // This could fetch real market data
        return {
            interest_rates: 7.5,
            market_trend: 'stable',
            inventory_level: 'low',
            average_dom: 45,
            price_trend: '+3.2%'
        };
    }
    
    /**
     * Setup WebSocket connection for real-time chat
     */
    setupWebSocket(ws, sessionId) {
        this.wsConnections.set(sessionId, ws);
        
        ws.on('message', async (data) => {
            try {
                const message = JSON.parse(data);
                
                switch (message.type) {
                    case 'chat':
                        const response = await this.chat(
                            sessionId,
                            message.content,
                            message.agent || 'property_analysis'
                        );
                        
                        ws.send(JSON.stringify({
                            type: 'response',
                            ...response
                        }));
                        break;
                    
                    case 'analyze':
                        const analysis = await this.analyzeProperty(
                            message.parcel_id,
                            message.analysis_type
                        );
                        
                        ws.send(JSON.stringify({
                            type: 'analysis',
                            ...analysis
                        }));
                        break;
                    
                    case 'research':
                        const research = await this.researchProperty(
                            message.query,
                            message.research_type
                        );
                        
                        ws.send(JSON.stringify({
                            type: 'research',
                            ...research
                        }));
                        break;
                    
                    default:
                        ws.send(JSON.stringify({
                            type: 'error',
                            message: 'Unknown message type'
                        }));
                }
            } catch (error) {
                ws.send(JSON.stringify({
                    type: 'error',
                    message: error.message
                }));
            }
        });
        
        ws.on('close', () => {
            this.wsConnections.delete(sessionId);
            this.activeChats.delete(sessionId);
        });
    }
    
    /**
     * Express middleware for LangChain routes
     */
    getExpressRouter() {
        const express = require('express');
        const router = express.Router();
        
        // Property analysis endpoint
        router.post('/analyze/property/:id', async (req, res) => {
            const result = await this.analyzeProperty(
                req.params.id,
                req.body.analysis_type
            );
            res.json(result);
        });
        
        // Investment advice endpoint
        router.post('/advice/investment', async (req, res) => {
            const result = await this.getInvestmentAdvice(
                req.body.property_data,
                req.body.investor_profile
            );
            res.json(result);
        });
        
        // Research endpoint
        router.post('/research', async (req, res) => {
            const result = await this.researchProperty(
                req.body.query,
                req.body.research_type
            );
            res.json(result);
        });
        
        // Market analysis endpoint
        router.post('/analyze/market', async (req, res) => {
            const result = await this.analyzeMarket(
                req.body.location,
                req.body.timeframe
            );
            res.json(result);
        });
        
        // Compliance check endpoint
        router.post('/compliance/check', async (req, res) => {
            const result = await this.checkCompliance(
                req.body.property_data,
                req.body.check_type
            );
            res.json(result);
        });
        
        // Chat endpoint
        router.post('/chat', async (req, res) => {
            const result = await this.chat(
                req.body.session_id || req.sessionID,
                req.body.message,
                req.body.agent_type
            );
            res.json(result);
        });
        
        // Knowledge base query endpoint
        router.post('/knowledge/query', async (req, res) => {
            const result = await this.queryKnowledgeBase(
                req.body.query,
                req.body.knowledge_base
            );
            res.json(result);
        });
        
        // Metrics endpoint
        router.get('/metrics', async (req, res) => {
            const result = await this.getMetrics();
            res.json(result);
        });
        
        // Health check
        router.get('/health', (req, res) => {
            res.json({
                status: 'healthy',
                agents: this.agents,
                langsmith: this.langsmithConfig
            });
        });
        
        return router;
    }
    
    /**
     * Helper function to convert snake_case to camelCase
     */
    toCamelCase(str) {
        return str.replace(/_([a-z])/g, (g) => g[1].toUpperCase());
    }
    
    /**
     * Shutdown LangChain integration
     */
    async shutdown() {
        console.log('Shutting down LangChain integration...');
        
        // Close WebSocket connections
        for (const [sessionId, ws] of this.wsConnections) {
            ws.close();
        }
        
        // Clear active chats
        this.activeChats.clear();
        
        // Stop LangChain process if we started it
        if (this.langchainProcess) {
            this.langchainProcess.kill();
        }
        
        this.emit('shutdown');
    }
}

module.exports = LangChainIntegration;
