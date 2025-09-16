/**
 * API Routes for MCP Server
 * Defines all REST endpoints for service integrations
 */

const express = require('express');
const router = express.Router();

// Middleware for API key authentication
const authenticateRequest = (req, res, next) => {
  const apiKey = req.headers['x-api-key'];
  const validApiKey = process.env.MCP_API_KEY || 'concordbroker-mcp-key';
  
  if (apiKey !== validApiKey) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  next();
};

// Apply authentication to all routes
router.use(authenticateRequest);

// Health check endpoint
router.get('/health', (req, res) => {
  const services = req.app.locals.services;
  const health = {};
  
  Object.keys(services).forEach(service => {
    health[service] = 'connected';
  });
  
  res.json({
    status: 'healthy',
    services: health,
    timestamp: new Date().toISOString()
  });
});

// === VERCEL ROUTES ===
router.get('/vercel/deployments', async (req, res) => {
  try {
    const { limit = 10 } = req.query;
    const result = await req.app.locals.services.vercel.getDeployments(limit);
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.post('/vercel/deploy', async (req, res) => {
  try {
    const result = await req.app.locals.services.vercel.triggerDeploy();
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.get('/vercel/project', async (req, res) => {
  try {
    const result = await req.app.locals.services.vercel.getProject();
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.get('/vercel/domains', async (req, res) => {
  try {
    const result = await req.app.locals.services.vercel.getDomains();
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// === RAILWAY ROUTES ===
router.get('/railway/status', async (req, res) => {
  try {
    const result = await req.app.locals.services.railway.getStatus();
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.get('/railway/environments', async (req, res) => {
  try {
    const result = await req.app.locals.services.railway.getEnvironments();
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.post('/railway/deploy', async (req, res) => {
  try {
    const { environmentId } = req.body;
    const result = await req.app.locals.services.railway.triggerDeployment(environmentId);
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// === SUPABASE ROUTES ===
router.post('/supabase/query', async (req, res) => {
  try {
    if (process.env.SUPABASE_ENABLE_SQL !== 'true') {
      return res.status(403).json({ success: false, error: 'Direct SQL execution is disabled. Use PostgREST or vetted RPCs.' });
    }
    const { sql } = req.body;
    const result = await req.app.locals.services.supabase.query(sql);
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.get('/supabase/:table', async (req, res) => {
  try {
    const { table } = req.params;
    const filters = req.query;
    const result = await req.app.locals.services.supabase.getFromTable(table, filters);
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.post('/supabase/:table', async (req, res) => {
  try {
    const { table } = req.params;
    const result = await req.app.locals.services.supabase.insertIntoTable(table, req.body);
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.patch('/supabase/:table/:id', async (req, res) => {
  try {
    const { table, id } = req.params;
    const result = await req.app.locals.services.supabase.updateTable(table, id, req.body);
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.delete('/supabase/:table/:id', async (req, res) => {
  try {
    const { table, id } = req.params;
    const result = await req.app.locals.services.supabase.deleteFromTable(table, id);
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// === HUGGINGFACE ROUTES ===
router.post('/huggingface/inference', async (req, res) => {
  try {
    const { model, inputs, options } = req.body;
    const result = await req.app.locals.services.huggingface.inference(model, inputs, options);
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.post('/huggingface/text-generation', async (req, res) => {
  try {
    const { prompt, model } = req.body;
    const result = await req.app.locals.services.huggingface.textGeneration(prompt, model);
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.post('/huggingface/classification', async (req, res) => {
  try {
    const { text, model } = req.body;
    const result = await req.app.locals.services.huggingface.textClassification(text, model);
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.post('/huggingface/qa', async (req, res) => {
  try {
    const { question, context, model } = req.body;
    const result = await req.app.locals.services.huggingface.questionAnswering(question, context, model);
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.post('/huggingface/summarize', async (req, res) => {
  try {
    const { text, model } = req.body;
    const result = await req.app.locals.services.huggingface.summarization(text, model);
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// === OPENAI ROUTES ===
router.post('/openai/complete', async (req, res) => {
  try {
    const { prompt, options } = req.body;
    const result = await req.app.locals.services.openai.complete(prompt, options);
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.post('/openai/embedding', async (req, res) => {
  try {
    const { text, model } = req.body;
    const result = await req.app.locals.services.openai.generateEmbedding(text, model);
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.post('/openai/image', async (req, res) => {
  try {
    const { prompt, options } = req.body;
    const result = await req.app.locals.services.openai.generateImage(prompt, options);
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.post('/openai/moderate', async (req, res) => {
  try {
    const { input } = req.body;
    const result = await req.app.locals.services.openai.moderateContent(input);
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// === GITHUB ROUTES ===
router.get('/github/commits', async (req, res) => {
  try {
    const { branch, limit } = req.query;
    const result = await req.app.locals.services.github.getCommits(branch, limit);
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.post('/github/issue', async (req, res) => {
  try {
    const { title, body, labels } = req.body;
    const result = await req.app.locals.services.github.createIssue(title, body, labels);
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.post('/github/pr', async (req, res) => {
  try {
    const { title, head, base, body } = req.body;
    const result = await req.app.locals.services.github.createPullRequest(title, head, base, body);
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.get('/github/workflows/:workflowId/runs', async (req, res) => {
  try {
    const { workflowId } = req.params;
    const result = await req.app.locals.services.github.getWorkflowRuns(workflowId);
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.post('/github/workflows/:workflowId/trigger', async (req, res) => {
  try {
    const { workflowId } = req.params;
    const { ref, inputs } = req.body;
    const result = await req.app.locals.services.github.triggerWorkflow(workflowId, ref, inputs);
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.get('/github/branches', async (req, res) => {
  try {
    const result = await req.app.locals.services.github.getBranches();
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.post('/github/branch', async (req, res) => {
  try {
    const { branchName, sha } = req.body;
    const result = await req.app.locals.services.github.createBranch(branchName, sha);
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// === UNIFIED OPERATIONS ===
router.post('/deploy-all', async (req, res) => {
  try {
    const results = {};
    
    // Trigger Vercel deployment
    try {
      results.vercel = await req.app.locals.services.vercel.triggerDeploy();
    } catch (error) {
      results.vercel = { error: error.message };
    }
    
    // Trigger Railway deployment (if environment ID provided)
    if (req.body.railwayEnvironmentId) {
      try {
        results.railway = await req.app.locals.services.railway.triggerDeployment(req.body.railwayEnvironmentId);
      } catch (error) {
        results.railway = { error: error.message };
      }
    }
    
    res.json({ success: true, data: results });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.get('/status-all', async (req, res) => {
  try {
    const results = {};
    
    // Get Vercel status
    try {
      const deployments = await req.app.locals.services.vercel.getDeployments(1);
      results.vercel = deployments.deployments?.[0] || null;
    } catch (error) {
      results.vercel = { error: error.message };
    }
    
    // Get Railway status
    try {
      results.railway = await req.app.locals.services.railway.getStatus();
    } catch (error) {
      results.railway = { error: error.message };
    }
    
    // Get latest GitHub commits
    try {
      const commits = await req.app.locals.services.github.getCommits('main', 5);
      results.github = commits.slice(0, 5);
    } catch (error) {
      results.github = { error: error.message };
    }
    
    res.json({ success: true, data: results });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

module.exports = router;
