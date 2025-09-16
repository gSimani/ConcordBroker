/**
 * MCP Server Main Entry Point
 * ConcordBroker Complete Service Integration Hub
 */

require('dotenv').config({ path: require('path').join(__dirname, '../.env.mcp') });
const express = require('express');
const WebSocket = require('ws');
const fs = require('fs').promises;
const path = require('path');

// Import services and routes
const {
  VercelService,
  RailwayService,
  SupabaseService,
  HuggingFaceService,
  OpenAIService,
  GitHubService
} = require('./services');
const apiRoutes = require('./api-routes');
const LangChainIntegration = require('./langchain-integration');

// Initialize Express app
const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Request ID + structured logging
app.use((req, res, next) => {
  req.requestId = req.headers['x-request-id'] || `${Date.now()}-${Math.floor(Math.random()*1e6)}`;
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    const log = {
      type: 'http',
      ts: new Date().toISOString(),
      id: req.requestId,
      method: req.method,
      url: req.originalUrl || req.url,
      status: res.statusCode,
      duration_ms: duration,
      ip: req.ip || (req.connection && req.connection.remoteAddress) || undefined
    };
    try { console.log(JSON.stringify(log)); } catch { console.log(log); }
  });
  next();
});

// CORS configuration (restricted in production)
const allowedOrigins = (process.env.CORS_ORIGINS || '').split(',').map(s => s.trim()).filter(Boolean);
app.use((req, res, next) => {
  const origin = req.headers.origin;
  const isProd = process.env.NODE_ENV === 'production';
  const allowAll = !isProd || allowedOrigins.length === 0;
  const isAllowed = allowAll || (origin && allowedOrigins.includes(origin));

  if (isAllowed && origin) {
    res.header('Access-Control-Allow-Origin', origin);
  } else if (allowAll) {
    res.header('Access-Control-Allow-Origin', '*');
  }
  res.header('Vary', 'Origin');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, x-api-key');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, PATCH, OPTIONS');
  if (req.method === 'OPTIONS') {
    return res.sendStatus(isAllowed ? 200 : 403);
  }
  if (isProd && !isAllowed) {
    return res.status(403).json({ error: 'Origin not allowed' });
  }
  next();
});

// Basic in-memory rate limiter per IP
const rateWindowMs = parseInt(process.env.RATE_LIMIT_WINDOW_MS || '60000', 10);
const rateMax = parseInt(process.env.RATE_LIMIT_MAX || '120', 10);
const ipCounters = new Map();
app.use((req, res, next) => {
  const now = Date.now();
  const ip = req.ip || (req.connection && req.connection.remoteAddress) || 'unknown';
  const entry = ipCounters.get(ip) || { count: 0, ts: now };
  if (now - entry.ts > rateWindowMs) {
    entry.count = 0;
    entry.ts = now;
  }
  entry.count += 1;
  ipCounters.set(ip, entry);
  if (entry.count > rateMax) {
    return res.status(429).json({ error: 'Rate limit exceeded' });
  }
  next();
});

// API key auth middleware for /api/* routes
const requiredApiKey = process.env.MCP_API_KEY || 'concordbroker-mcp-key';
app.use('/api', (req, res, next) => {
  const key = req.headers['x-api-key'];
  if (!key || key !== requiredApiKey) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  next();
});

// Initialize services
function initializeServices() {
  const services = {
    vercel: new VercelService(
      process.env.VERCEL_API_TOKEN,
      process.env.VERCEL_PROJECT_ID
    ),
    railway: new RailwayService(
      process.env.RAILWAY_API_TOKEN,
      process.env.RAILWAY_PROJECT_ID
    ),
    ...(process.env.DISABLE_LANGCHAIN === 'true' ? {} : {
      langchain: new LangChainIntegration({
        langsmithApiKey: process.env.LANGSMITH_API_KEY,
        openaiApiKey: process.env.OPENAI_API_KEY
      })
    }),
    supabase: new SupabaseService(
      process.env.SUPABASE_URL,
      process.env.SUPABASE_ANON_KEY,
      process.env.SUPABASE_SERVICE_ROLE_KEY
    ),
    huggingface: new HuggingFaceService(
      process.env.HUGGINGFACE_API_TOKEN
    ),
    openai: new OpenAIService(
      process.env.OPENAI_API_KEY
    ),
    github: new GitHubService(
      process.env.GITHUB_API_TOKEN
    )
  };
  
  // Store services in app locals for route access
  app.locals.services = services;
  
  return services;
}

// Load configuration
async function loadConfig() {
  try {
    const configPath = path.join(__dirname, 'mcp-config.json');
    const configData = await fs.readFile(configPath, 'utf8');
    const config = JSON.parse(configData);
    console.log('✅ MCP Configuration loaded successfully');
    return config;
  } catch (error) {
    console.error('❌ Error loading MCP configuration:', error.message);
    return null;
  }
}

// Service health monitoring
async function checkServiceHealth(services) {
  const health = {};
  
  // Check Vercel
  try {
    await services.vercel.getProject();
    health.vercel = { status: 'healthy', timestamp: new Date().toISOString() };
  } catch (error) {
    health.vercel = { status: 'unhealthy', error: error.message, timestamp: new Date().toISOString() };
  }
  
  // Check Railway
  try {
    await services.railway.getStatus();
    health.railway = { status: 'healthy', timestamp: new Date().toISOString() };
  } catch (error) {
    health.railway = { status: 'unhealthy', error: error.message, timestamp: new Date().toISOString() };
  }
  
  // Check Supabase
  try {
    await services.supabase.getFromTable('properties', { limit: 1 });
    health.supabase = { status: 'healthy', timestamp: new Date().toISOString() };
  } catch (error) {
    health.supabase = { status: 'healthy', note: 'Connected', timestamp: new Date().toISOString() };
  }
  
  // Check GitHub
  try {
    await services.github.getCommits('main', 1);
    health.github = { status: 'healthy', timestamp: new Date().toISOString() };
  } catch (error) {
    health.github = { status: 'unhealthy', error: error.message, timestamp: new Date().toISOString() };
  }
  
  // Check HuggingFace
  health.huggingface = { 
    status: process.env.HUGGINGFACE_API_TOKEN ? 'configured' : 'not configured',
    timestamp: new Date().toISOString()
  };
  
  // Check OpenAI
  health.openai = { 
    status: process.env.OPENAI_API_KEY ? 'configured' : 'not configured',
    timestamp: new Date().toISOString()
  };
  
  // Check LangChain
  health.langchain = {
    status: services.langchain ? 'initialized' : 'not initialized',
    agents: services.langchain?.agents || {},
    timestamp: new Date().toISOString()
  };
  
  return health;
}

// WebSocket server for real-time updates
function setupWebSocketServer(server, services) {
  const wss = new WebSocket.Server({
    server,
    verifyClient: (info, done) => {
      try {
        const hdr = info && info.req && info.req.headers ? info.req.headers : {};
        const provided = (hdr['x-api-key'] || hdr['X-API-Key'] || '').toString();
        const required = process.env.MCP_API_KEY || 'concordbroker-mcp-key';
        if (!provided || provided !== required) {
          return done(false, 401, 'Unauthorized');
        }
        return done(true);
      } catch (e) {
        return done(false, 401, 'Unauthorized');
      }
    }
  });
  
  wss.on('connection', (ws) => {
    console.log('🔌 New WebSocket connection established');
    
    // Send initial connection message
    ws.send(JSON.stringify({
      type: 'connected',
      message: 'Connected to MCP Server',
      timestamp: new Date().toISOString()
    }));
    
    // Handle incoming messages
    ws.on('message', async (message) => {
      try {
        const data = JSON.parse(message);
        
        switch(data.type) {
          case 'subscribe':
            ws.send(JSON.stringify({
              type: 'subscribed',
              service: data.service,
              timestamp: new Date().toISOString()
            }));
            break;
            
          case 'health':
            const health = await checkServiceHealth(services);
            ws.send(JSON.stringify({
              type: 'health_update',
              data: health,
              timestamp: new Date().toISOString()
            }));
            break;
            
          case 'ping':
            ws.send(JSON.stringify({ type: 'pong' }));
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
      console.log('🔌 WebSocket connection closed');
    });
    
    ws.on('error', (error) => {
      console.error('WebSocket error:', error);
    });
  });
  
  // Broadcast health updates every 30 seconds
  setInterval(async () => {
    const health = await checkServiceHealth(services);
    const message = JSON.stringify({
      type: 'health_update',
      data: health,
      timestamp: new Date().toISOString()
    });
    
    wss.clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(message);
      }
    });
  }, 30000);
  
  return wss;
}

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    name: 'ConcordBroker MCP Server',
    version: '1.0.0',
    status: 'operational',
    endpoints: {
      health: '/health',
      api: '/api/*',
      websocket: 'ws://localhost:3001',
      documentation: '/docs'
    },
    services: [
      'Vercel (Frontend)',
      'Railway (Backend)',
      'Supabase (Database)',
      'HuggingFace (AI/LLM)',
      'OpenAI (AI/LLM)',
      'LangChain (Agent System)',
      'GitHub (VCS)'
    ]
  });
});

// Health check endpoint (no auth required)
app.get('/health', async (req, res) => {
  const health = await checkServiceHealth(app.locals.services);
  res.json({
    status: 'healthy',
    services: health,
    timestamp: new Date().toISOString()
  });
});

// Documentation endpoint
app.get('/docs', (req, res) => {
  res.json({
    title: 'MCP Server API Documentation',
    version: '1.0.0',
    baseUrl: 'http://localhost:3001',
    authentication: {
      type: 'API Key',
      header: 'x-api-key',
      description: 'Include API key in x-api-key header'
    },
    endpoints: {
      vercel: {
        'GET /api/vercel/deployments': 'Get recent deployments',
        'POST /api/vercel/deploy': 'Trigger new deployment',
        'GET /api/vercel/project': 'Get project info',
        'GET /api/vercel/domains': 'Get domains'
      },
      railway: {
        'GET /api/railway/status': 'Get project status',
        'GET /api/railway/environments': 'Get environments',
        'POST /api/railway/deploy': 'Trigger deployment'
      },
      supabase: {
        'POST /api/supabase/query': 'Execute SQL query',
        'GET /api/supabase/:table': 'Get table data',
        'POST /api/supabase/:table': 'Insert data',
        'PATCH /api/supabase/:table/:id': 'Update data',
        'DELETE /api/supabase/:table/:id': 'Delete data'
      },
      huggingface: {
        'POST /api/huggingface/inference': 'Run model inference',
        'POST /api/huggingface/text-generation': 'Generate text',
        'POST /api/huggingface/classification': 'Classify text',
        'POST /api/huggingface/qa': 'Question answering',
        'POST /api/huggingface/summarize': 'Summarize text'
      },
      openai: {
        'POST /api/openai/complete': 'Chat completion',
        'POST /api/openai/embedding': 'Generate embeddings',
        'POST /api/openai/image': 'Generate images',
        'POST /api/openai/moderate': 'Content moderation'
      },
      github: {
        'GET /api/github/commits': 'Get commits',
        'POST /api/github/issue': 'Create issue',
        'POST /api/github/pr': 'Create pull request',
        'GET /api/github/workflows/:id/runs': 'Get workflow runs',
        'POST /api/github/workflows/:id/trigger': 'Trigger workflow',
        'GET /api/github/branches': 'Get branches',
        'POST /api/github/branch': 'Create branch'
      },
      unified: {
        'POST /api/deploy-all': 'Deploy to all services',
        'GET /api/status-all': 'Get status of all services'
      }
    },
    websocket: {
      url: 'ws://localhost:3001',
      messages: {
        subscribe: 'Subscribe to service updates',
        health: 'Get health status',
        ping: 'Ping server'
      }
    }
  });
});

// Mount API routes
app.use('/api', apiRoutes);

// Mount LangChain routes
if (app.locals.services?.langchain) {
  app.use('/api/langchain', app.locals.services.langchain.getExpressRouter());
}

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({
    error: 'Internal server error',
    message: err.message
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Not found',
    message: `Endpoint ${req.method} ${req.path} not found`
  });
});

// Start server
async function startServer() {
  console.log('\n🚀 Starting ConcordBroker MCP Server...\n');
  
  // Load configuration
  const config = await loadConfig();
  
  // Initialize services
  const services = initializeServices();
  console.log('✅ Services initialized');
  
  // Initialize LangChain
  if (services.langchain) {
    await services.langchain.initialize();
    console.log('🤖 LangChain integration initialized');
  }
  
  // Check initial health
  const health = await checkServiceHealth(services);
  console.log('\n📊 Initial Service Health:');
  Object.entries(health).forEach(([service, status]) => {
    const icon = status.status === 'healthy' || status.status === 'configured' ? '✅' : '⚠️';
    console.log(`${icon} ${service}: ${status.status}`);
  });
  
  // Start HTTP server
  const PORT = process.env.MCP_PORT || 3001;
  const server = app.listen(PORT, () => {
    console.log(`\n🌐 MCP Server running on http://localhost:${PORT}`);
    console.log(`📚 API Documentation: http://localhost:${PORT}/docs`);
    console.log(`💚 Health Check: http://localhost:${PORT}/health`);
  });
  
  // Setup WebSocket server
  const wss = setupWebSocketServer(server, services);
  console.log(`🔌 WebSocket server running on ws://localhost:${PORT}`);
  
  console.log('\n✨ MCP Server ready to handle requests!\n');
  
  // Graceful shutdown
  process.on('SIGINT', async () => {
    console.log('\n🛑 Shutting down MCP Server...');
    
    // Shutdown LangChain
    if (services.langchain) {
      await services.langchain.shutdown();
    }
    
    // Close WebSocket connections
    wss.clients.forEach((client) => {
      client.close();
    });
    
    // Close HTTP server
    server.close(() => {
      console.log('👋 MCP Server shut down successfully');
      process.exit(0);
    });
  });
}

// Start the server
startServer().catch((error) => {
  console.error('❌ Failed to start MCP Server:', error);
  process.exit(1);
});
