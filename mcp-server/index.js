/**
 * MCP Server - ConcordBroker Complete Service Integration Hub
 * Manages connections to all external services and provides a unified API
 * Integrates: Vercel, Railway, Supabase, HuggingFace, OpenAI, GitHub, and more
 */

const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../.env.mcp') });
const https = require('https');
const fs = require('fs');
const express = require('express');
const axios = require('axios');
const WebSocket = require('ws');
const GitHubIntegration = require('./github-integration');

// Express app for API endpoints
const app = express();
app.use(express.json());

class ConcordBrokerMCPServer {
  constructor(config) {
    this.config = config;
    
    // Vercel Configuration
    this.vercelApiToken = process.env.VERCEL_API_TOKEN;
    this.vercelProjectId = process.env.VERCEL_PROJECT_ID;
    
    // Railway Configuration
    this.railwayApiToken = process.env.RAILWAY_API_TOKEN;
    this.railwayProjectId = process.env.RAILWAY_PROJECT_ID;
    
    // Supabase Configuration
    this.supabaseUrl = process.env.SUPABASE_URL;
    this.supabaseAnonKey = process.env.SUPABASE_ANON_KEY;
    this.supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
    
    // HuggingFace Configuration
    this.huggingfaceToken = process.env.HUGGINGFACE_API_TOKEN;
    
    // OpenAI Configuration
    this.openaiKey = process.env.OPENAI_API_KEY;
    
    // GitHub Configuration
    this.githubToken = process.env.GITHUB_API_TOKEN;
    
    // Initialize service managers
    this.initializeServices();
    
    // Initialize GitHub integration (kept for compatibility)
    this.github = new GitHubIntegration({
      token: this.githubToken,
      owner: 'gSimani',
      repo: 'ConcordBroker',
      branch: 'main',
      vercel: { projectId: this.vercelProjectId }
    });
  }
  
  initializeServices() {
    // Initialize all service connections
    this.services = {
      vercel: new VercelService(this.vercelApiToken, this.vercelProjectId),
      railway: new RailwayService(this.railwayApiToken, this.railwayProjectId),
      supabase: new SupabaseService(this.supabaseUrl, this.supabaseAnonKey, this.supabaseServiceKey),
      huggingface: new HuggingFaceService(this.huggingfaceToken),
      openai: new OpenAIService(this.openaiKey),
      github: new GitHubService(this.githubToken)
    };
  }

  /**
   * Initialize the MCP server
   */
  async init() {
    console.log('Initializing Vercel MCP Server...');
    
    // Validate configuration
    if (!this.apiToken) {
      throw new Error('VERCEL_API_TOKEN is required');
    }

    // Check project status
    const project = await this.getProject();
    console.log(`Connected to project: ${project.name}`);
    
    // Initialize GitHub integration
    if (this.github) {
      console.log('\nInitializing GitHub integration...');
      await this.github.init();
    }
    
    // Setup webhooks
    await this.setupWebhooks();
    
    // Initialize monitoring
    this.startMonitoring();
    
    return true;
  }

  /**
   * Get project information from Vercel
   */
  async getProject() {
    return this.makeRequest('GET', `/v9/projects/${this.projectId}`);
  }

  /**
   * Get deployment status
   */
  async getDeployments(limit = 10) {
    return this.makeRequest('GET', `/v6/deployments?projectId=${this.projectId}&limit=${limit}`);
  }

  /**
   * Create a new deployment
   */
  async createDeployment(gitSource) {
    const payload = {
      name: 'concordbroker',
      project: this.projectId,
      gitSource: gitSource || {
        type: 'github',
        repo: 'ConcordBroker',
        ref: 'main'
      },
      target: 'production',
      env: await this.getEnvironmentVariables()
    };

    return this.makeRequest('POST', '/v13/deployments', payload);
  }

  /**
   * Get environment variables
   */
  async getEnvironmentVariables() {
    const envVars = await this.makeRequest('GET', `/v9/projects/${this.projectId}/env`);
    return envVars.envs.reduce((acc, env) => {
      acc[env.key] = env.value;
      return acc;
    }, {});
  }

  /**
   * Update environment variables
   */
  async updateEnvironmentVariable(key, value, target = ['production', 'preview', 'development']) {
    const payload = {
      key,
      value,
      target,
      type: 'encrypted'
    };

    return this.makeRequest('POST', `/v10/projects/${this.projectId}/env`, payload);
  }

  /**
   * Setup webhooks for deployment events
   */
  async setupWebhooks() {
    const webhookUrl = process.env.WEBHOOK_URL || 'https://concordbroker.com/api/webhooks/vercel';
    
    const webhook = {
      name: 'deployment-webhook',
      url: webhookUrl,
      events: [
        'deployment.created',
        'deployment.succeeded',
        'deployment.error',
        'deployment.canceled'
      ]
    };

    try {
      await this.makeRequest('POST', `/v1/integrations/webhooks`, webhook);
      console.log('Webhooks configured successfully');
    } catch (error) {
      console.log('Webhooks may already be configured:', error.message);
    }
  }

  /**
   * Start monitoring deployments
   */
  startMonitoring() {
    console.log('Starting deployment monitoring...');
    
    setInterval(async () => {
      try {
        const deployments = await this.getDeployments(1);
        if (deployments.deployments && deployments.deployments.length > 0) {
          const latest = deployments.deployments[0];
          console.log(`Latest deployment: ${latest.url} - Status: ${latest.readyState}`);
        }
      } catch (error) {
        console.error('Monitoring error:', error.message);
      }
    }, 60000); // Check every minute
  }

  /**
   * Make API request to Vercel
   */
  makeRequest(method, path, data = null) {
    return new Promise((resolve, reject) => {
      const options = {
        hostname: this.baseUrl,
        path: path,
        method: method,
        headers: {
          'Authorization': `Bearer ${this.apiToken}`,
          'Content-Type': 'application/json'
        }
      };

      const req = https.request(options, (res) => {
        let responseData = '';

        res.on('data', (chunk) => {
          responseData += chunk;
        });

        res.on('end', () => {
          try {
            const parsed = JSON.parse(responseData);
            if (res.statusCode >= 200 && res.statusCode < 300) {
              resolve(parsed);
            } else {
              reject(new Error(`API Error: ${parsed.error?.message || responseData}`));
            }
          } catch (error) {
            reject(error);
          }
        });
      });

      req.on('error', reject);

      if (data) {
        req.write(JSON.stringify(data));
      }

      req.end();
    });
  }

  /**
   * Get domain information
   */
  async getDomains() {
    return this.makeRequest('GET', `/v9/projects/${this.projectId}/domains`);
  }

  /**
   * Add custom domain
   */
  async addDomain(domain) {
    return this.makeRequest('POST', `/v10/projects/${this.projectId}/domains`, {
      name: domain
    });
  }

  /**
   * Get analytics data
   */
  async getAnalytics(timeframe = '24h') {
    return this.makeRequest('GET', `/v1/analytics/${this.projectId}?timeframe=${timeframe}`);
  }

  /**
   * Check deployment logs
   */
  async getDeploymentLogs(deploymentId) {
    return this.makeRequest('GET', `/v2/deployments/${deploymentId}/events`);
  }
}

// Export for use in other modules
module.exports = VercelMCPServer;

// Run if called directly
if (require.main === module) {
  const configPath = path.join(__dirname, 'vercel-config.json');
  const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  
  const server = new VercelMCPServer(config);
  
  server.init()
    .then(() => {
      console.log('MCP Server initialized successfully');
    })
    .catch((error) => {
      console.error('Failed to initialize MCP Server:', error);
      process.exit(1);
    });
}
