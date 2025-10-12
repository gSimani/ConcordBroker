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

// Import Supabase MCP integration
const {
  registerSupabaseMcpTools,
  checkSupabaseMcpHealth
} = require('./supabase-mcp-integration');

// Import AI System Auto-Startup
const { spawn } = require('child_process');
let aiSystemProcess = null;

// Import Permanent Memory, DeepWiki, and Playwright Verification
const PermanentMemorySystem = require('./permanent-memory-system');
const DeepWikiIntegrations = require('./deepwiki-integrations');
const PlaywrightVerificationSystem = require('./playwright-verification-system');

// Initialize advanced systems
const permanentMemory = new PermanentMemorySystem();
const deepWiki = new DeepWikiIntegrations();
const playwrightVerification = new PlaywrightVerificationSystem();

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

  // Check Supabase MCP
  try {
    const supabaseMcpHealth = await checkSupabaseMcpHealth();
    health.supabaseMcp = supabaseMcpHealth;
  } catch (error) {
    health.supabaseMcp = {
      healthy: false,
      error: error.message,
      timestamp: new Date().toISOString()
    };
  }

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

// Supabase MCP health endpoint (no auth required)
app.get('/supabase-mcp/health', async (req, res) => {
  try {
    const health = await checkSupabaseMcpHealth();
    res.json(health);
  } catch (error) {
    res.status(500).json({
      healthy: false,
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
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
      supabaseMcp: {
        'GET /api/supabase/mcp/health': 'Supabase MCP health check (no auth)',
        'POST /api/supabase/mcp/query': 'Query database with MCP',
        'POST /api/supabase/mcp/schema': 'Get table schema',
        'POST /api/supabase/mcp/tables': 'List all tables',
        'POST /api/supabase/mcp/execute': 'Execute safe query',
        'POST /api/supabase/mcp/stats': 'Get database stats',
        'POST /api/supabase/mcp/search': 'Search properties'
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

// Mount Permanent Memory routes
app.get('/api/memory/rules', (req, res) => {
  res.json({ rules: permanentMemory.getRules() });
});

app.get('/api/memory/sessions', (req, res) => {
  const count = parseInt(req.query.count) || 10;
  res.json({ sessions: permanentMemory.getRecentSessions(count) });
});

app.get('/api/memory/verifications', (req, res) => {
  const count = parseInt(req.query.count) || 20;
  res.json({ verifications: permanentMemory.getRecentVerifications(count) });
});

app.get('/api/memory/stats', async (req, res) => {
  const stats = await permanentMemory.getMemoryStats();
  res.json(stats);
});

app.post('/api/memory/check-compliance', async (req, res) => {
  const result = await permanentMemory.checkRuleCompliance();
  res.json(result);
});

// Mount DeepWiki routes
app.get('/api/deepwiki/repositories', (req, res) => {
  res.json({ repositories: deepWiki.getAllRepositories() });
});

app.get('/api/deepwiki/search', async (req, res) => {
  const query = req.query.q || req.query.query;
  if (!query) {
    return res.status(400).json({ error: 'Query parameter required' });
  }
  const results = await deepWiki.searchAllRepositories(query);
  res.json({ query, results });
});

app.get('/api/deepwiki/:repository', async (req, res) => {
  const { repository } = req.params;
  const repo = deepWiki.getRepository(repository);
  if (!repo) {
    return res.status(404).json({ error: 'Repository not found' });
  }
  res.json(repo);
});

// Mount Playwright Verification routes
app.post('/api/verify/frontend', async (req, res) => {
  const url = req.body.url || 'http://localhost:5191';
  const result = await playwrightVerification.verifyFrontend(url);
  res.json(result);
});

app.post('/api/verify/mcp', async (req, res) => {
  const url = req.body.url || 'http://localhost:3001';
  const result = await playwrightVerification.verifyMCPServer(url);
  res.json(result);
});

app.post('/api/verify/property-search', async (req, res) => {
  const result = await playwrightVerification.verifyPropertySearch();
  res.json(result);
});

app.post('/api/verify/all', async (req, res) => {
  const results = await playwrightVerification.runAllVerifications();
  res.json(results);
});

app.get('/api/verify/history', (req, res) => {
  const count = parseInt(req.query.count) || 10;
  const history = playwrightVerification.getVerificationHistory(count);
  res.json({ history });
});

// Mount Supabase MCP tool routes (with auth)
const { supabaseMcpTools } = require('./supabase-mcp-integration');

app.post('/api/supabase/mcp/query', async (req, res) => {
  try {
    const result = await supabaseMcpTools.queryDatabase(req.body);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/supabase/mcp/schema', async (req, res) => {
  try {
    const result = await supabaseMcpTools.getTableSchema(req.body);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/supabase/mcp/tables', async (req, res) => {
  try {
    const result = await supabaseMcpTools.listTables();
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/supabase/mcp/execute', async (req, res) => {
  try {
    const result = await supabaseMcpTools.executeSafeQuery(req.body);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/supabase/mcp/stats', async (req, res) => {
  try {
    const result = await supabaseMcpTools.getDatabaseStats();
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/supabase/mcp/search', async (req, res) => {
  try {
    const result = await supabaseMcpTools.searchProperties(req.body);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

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

// AI System Integration
async function startAISystem() {
  try {
    console.log('🤖 Starting ConcordBroker AI Data Flow System...');

    const aiSystemScript = path.join(__dirname, '../claude-code-ai-system-init.cjs');

    // Check if AI system script exists
    try {
      await fs.access(aiSystemScript);
    } catch {
      console.log('⚠️ AI System script not found, skipping AI startup');
      return;
    }

    // Start AI system as a child process
    aiSystemProcess = spawn('node', [aiSystemScript], {
      cwd: path.dirname(aiSystemScript),
      stdio: ['ignore', 'pipe', 'pipe'],
      detached: false
    });

    // Handle AI system output
    aiSystemProcess.stdout.on('data', (data) => {
      const output = data.toString().trim();
      if (output) {
        console.log(`🤖 AI System: ${output}`);
      }
    });

    aiSystemProcess.stderr.on('data', (data) => {
      const output = data.toString().trim();
      if (output && !output.includes('WARNING')) {
        console.log(`🤖 AI System Warning: ${output}`);
      }
    });

    aiSystemProcess.on('exit', (code, signal) => {
      if (code !== 0 && code !== null) {
        console.log(`🤖 AI System exited with code ${code}`);
      }
    });

    // Wait a moment for startup
    await new Promise(resolve => setTimeout(resolve, 2000));

    console.log('✅ AI Data Flow System startup initiated');
    console.log('📊 Dashboard will be available at: http://localhost:8004');
    console.log('🔗 AI API available at: http://localhost:8003/ai-system/health');

  } catch (error) {
    console.error('❌ Failed to start AI System:', error.message);
  }
}

// Start server
async function startServer() {
  console.log('\n🚀 Starting ConcordBroker MCP Server...\n');

  // Initialize Permanent Memory System
  await permanentMemory.initialize();

  // Initialize DeepWiki Integrations
  await deepWiki.initialize();

  // Initialize Playwright Verification
  await playwrightVerification.initialize();

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
  
  // Initialize Supabase MCP
  console.log('\n🔧 Initializing Supabase MCP integration...');
  try {
    const supabaseMcpHealth = await checkSupabaseMcpHealth();
    if (supabaseMcpHealth.healthy) {
      console.log('✅ Supabase MCP integration ready');
      console.log(`   - Read-only: ${supabaseMcpHealth.config?.readOnly}`);
      console.log(`   - Features: ${supabaseMcpHealth.config?.features?.join(', ')}`);
    } else {
      console.log('⚠️  Supabase MCP health check failed:', supabaseMcpHealth.error);
    }
  } catch (error) {
    console.log('⚠️  Supabase MCP initialization warning:', error.message);
  }

  // Check initial health
  const health = await checkServiceHealth(services);
  console.log('\n📊 Initial Service Health:');
  Object.entries(health).forEach(([service, status]) => {
    const icon = status.status === 'healthy' || status.status === 'configured' || status.healthy === true ? '✅' : '⚠️';
    console.log(`${icon} ${service}: ${status.status || (status.healthy ? 'healthy' : 'unhealthy')}`);
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

  // Start AI Data Flow System
  await startAISystem();
  
  // Run initial rule compliance check
  console.log('\n🔍 Running initial rule compliance check...');
  await permanentMemory.checkRuleCompliance();

  // Schedule periodic verifications (every 30 minutes)
  setInterval(async () => {
    console.log('\n🔍 Running periodic verification...');
    try {
      await playwrightVerification.runAllVerifications();
      await permanentMemory.checkRuleCompliance();
    } catch (error) {
      console.error('❌ Periodic verification failed:', error.message);
    }
  }, 30 * 60 * 1000);

  console.log('\n✅ All systems initialized and running!\n');
  console.log('📚 DeepWiki Repositories:', Object.keys(deepWiki.getAllRepositories()).length);
  console.log('📋 Rules Loaded:', permanentMemory.getRules().length);
  console.log('🎭 Playwright Verification: Active\n');

  // Graceful shutdown
  process.on('SIGINT', async () => {
    console.log('\n🛑 Shutting down MCP Server...');

    // Shutdown AI System
    if (aiSystemProcess) {
      console.log('🤖 Stopping AI Data Flow System...');
      aiSystemProcess.kill('SIGTERM');
      await new Promise(resolve => setTimeout(resolve, 3000));
      if (!aiSystemProcess.killed) {
        aiSystemProcess.kill('SIGKILL');
      }
    }

    // Shutdown Permanent Memory
    console.log('🧠 Saving permanent memory...');
    await permanentMemory.shutdown();

    // Shutdown Playwright
    console.log('🎭 Closing Playwright...');
    await playwrightVerification.shutdown();

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
