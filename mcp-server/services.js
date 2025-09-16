/**
 * Service Classes for MCP Server
 * Individual service implementations for all integrated platforms
 */

const axios = require('axios');

// Axios instance with x-request-id propagation
const http = axios.create();
http.interceptors.request.use((config) => {
  const rid = `${Date.now()}-${Math.floor(Math.random()*1e6)}`;
  config.headers = config.headers || {};
  if (!config.headers['x-request-id']) config.headers['x-request-id'] = rid;
  return config;
});

// Vercel Service
class VercelService {
  constructor(apiToken, projectId) {
    this.apiToken = apiToken;
    this.projectId = projectId;
    this.baseUrl = 'https://api.vercel.com';
  }

  async getDeployments(limit = 10) {
    const response = await http.get(
      `${this.baseUrl}/v6/deployments?projectId=${this.projectId}&limit=${limit}`,
      {
        headers: { 'Authorization': `Bearer ${this.apiToken}` }
      }
    );
    return response.data;
  }

  async triggerDeploy() {
    const response = await http.post(
      `${this.baseUrl}/v13/deployments`,
      {
        name: 'concord-broker',
        project: this.projectId,
        target: 'production'
      },
      {
        headers: { 'Authorization': `Bearer ${this.apiToken}` }
      }
    );
    return response.data;
  }

  async getProject() {
    const response = await http.get(
      `${this.baseUrl}/v9/projects/${this.projectId}`,
      {
        headers: { 'Authorization': `Bearer ${this.apiToken}` }
      }
    );
    return response.data;
  }

  async getDomains() {
    const response = await http.get(
      `${this.baseUrl}/v9/projects/${this.projectId}/domains`,
      {
        headers: { 'Authorization': `Bearer ${this.apiToken}` }
      }
    );
    return response.data;
  }
}

// Railway Service
class RailwayService {
  constructor(apiToken, projectId) {
    this.apiToken = apiToken;
    this.projectId = projectId;
    this.baseUrl = 'https://backboard.railway.app/graphql/v2';
  }

  async getStatus() {
    const response = await http.post(
      this.baseUrl,
      {
        query: `
          query GetProject($id: String!) {
            project(id: $id) {
              id
              name
              environments {
                edges {
                  node {
                    id
                    name
                    deployments {
                      edges {
                        node {
                          id
                          status
                          createdAt
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        `,
        variables: { id: this.projectId }
      },
      {
        headers: {
          'Authorization': `Bearer ${this.apiToken}`,
          'Content-Type': 'application/json'
        }
      }
    );
    return response.data;
  }

  async getEnvironments() {
    const response = await http.post(
      this.baseUrl,
      {
        query: `
          query GetEnvironments($projectId: String!) {
            project(id: $projectId) {
              environments {
                edges {
                  node {
                    id
                    name
                    variables
                  }
                }
              }
            }
          }
        `,
        variables: { projectId: this.projectId }
      },
      {
        headers: {
          'Authorization': `Bearer ${this.apiToken}`,
          'Content-Type': 'application/json'
        }
      }
    );
    return response.data;
  }

  async triggerDeployment(environmentId) {
    const response = await http.post(
      this.baseUrl,
      {
        query: `
          mutation TriggerDeployment($environmentId: String!) {
            deploymentTriggerCreate(input: {
              environmentId: $environmentId
            }) {
              id
              status
            }
          }
        `,
        variables: { environmentId }
      },
      {
        headers: {
          'Authorization': `Bearer ${this.apiToken}`,
          'Content-Type': 'application/json'
        }
      }
    );
    return response.data;
  }
}

// Supabase Service
class SupabaseService {
  constructor(url, anonKey, serviceKey) {
    this.url = url;
    this.anonKey = anonKey;
    this.serviceKey = serviceKey;
  }

  async query(sql) {
    // For safety, raw SQL execution is disabled by default.
    // Enable only if you have a constrained, vetted RPC on the backend.
    if (process.env.SUPABASE_ENABLE_SQL !== 'true') {
      throw new Error('Direct SQL execution is disabled. Use vetted RPCs or PostgREST filters.');
    }
    const response = await http.post(
      `${this.url}/rest/v1/rpc/execute_sql`,
      { query: sql },
      {
        headers: {
          'apikey': this.serviceKey,
          'Authorization': `Bearer ${this.serviceKey}`,
          'Content-Type': 'application/json'
        }
      }
    );
    return response.data;
  }

  async getFromTable(table, filters = {}) {
    let url = `${this.url}/rest/v1/${table}`;
    const params = new URLSearchParams(filters);
    if (params.toString()) url += `?${params}`;
    
    const response = await http.get(url, {
      headers: {
        'apikey': this.anonKey,
        'Authorization': `Bearer ${this.anonKey}`
      }
    });
    return response.data;
  }

  async insertIntoTable(table, data) {
    const response = await http.post(
      `${this.url}/rest/v1/${table}`,
      data,
      {
        headers: {
          'apikey': this.serviceKey,
          'Authorization': `Bearer ${this.serviceKey}`,
          'Content-Type': 'application/json',
          'Prefer': 'return=representation'
        }
      }
    );
    return response.data;
  }

  async updateTable(table, id, data) {
    const response = await http.patch(
      `${this.url}/rest/v1/${table}?id=eq.${id}`,
      data,
      {
        headers: {
          'apikey': this.serviceKey,
          'Authorization': `Bearer ${this.serviceKey}`,
          'Content-Type': 'application/json'
        }
      }
    );
    return response.data;
  }

  async deleteFromTable(table, id) {
    const response = await http.delete(
      `${this.url}/rest/v1/${table}?id=eq.${id}`,
      {
        headers: {
          'apikey': this.serviceKey,
          'Authorization': `Bearer ${this.serviceKey}`
        }
      }
    );
    return response.data;
  }

  async subscribeToTable(table, callback) {
    // Realtime subscription would go here
    // This is a placeholder for WebSocket connection to Supabase Realtime
    console.log(`Subscribing to ${table} table changes`);
  }
}

// HuggingFace Service
class HuggingFaceService {
  constructor(apiToken) {
    this.apiToken = apiToken;
    this.baseUrl = 'https://api-inference.huggingface.co';
  }

  async inference(model, inputs, options = {}) {
    const response = await http.post(
      `${this.baseUrl}/models/${model}`,
      { inputs, ...options },
      {
        headers: {
          'Authorization': `Bearer ${this.apiToken}`,
          'Content-Type': 'application/json'
        }
      }
    );
    return response.data;
  }

  async getModelInfo(model) {
    const response = await http.get(
      `https://huggingface.co/api/models/${model}`,
      {
        headers: {
          'Authorization': `Bearer ${this.apiToken}`
        }
      }
    );
    return response.data;
  }

  async textGeneration(prompt, model = 'gpt2') {
    return this.inference(model, prompt, {
      parameters: {
        max_new_tokens: 100,
        temperature: 0.7,
        do_sample: true
      }
    });
  }

  async textClassification(text, model = 'distilbert-base-uncased-finetuned-sst-2-english') {
    return this.inference(model, text);
  }

  async questionAnswering(question, context, model = 'distilbert-base-cased-distilled-squad') {
    return this.inference(model, { question, context });
  }

  async summarization(text, model = 'facebook/bart-large-cnn') {
    return this.inference(model, text, {
      parameters: {
        max_length: 130,
        min_length: 30,
        do_sample: false
      }
    });
  }
}

// OpenAI Service
class OpenAIService {
  constructor(apiKey) {
    this.apiKey = apiKey;
    this.baseUrl = 'https://api.openai.com/v1';
  }

  async complete(prompt, options = {}) {
    const response = await http.post(
      `${this.baseUrl}/chat/completions`,
      {
        model: options.model || 'gpt-4o',
        messages: [{ role: 'user', content: prompt }],
        temperature: options.temperature || 0.7,
        max_tokens: options.maxTokens || 150,
        ...options
      },
      {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        }
      }
    );
    return response.data;
  }

  async generateEmbedding(text, model = 'text-embedding-3-small') {
    const response = await http.post(
      `${this.baseUrl}/embeddings`,
      {
        input: text,
        model: model
      },
      {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        }
      }
    );
    return response.data;
  }

  async generateImage(prompt, options = {}) {
    const response = await http.post(
      `${this.baseUrl}/images/generations`,
      {
        prompt,
        n: options.n || 1,
        size: options.size || '1024x1024',
        ...options
      },
      {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        }
      }
    );
    return response.data;
  }

  async moderateContent(input) {
    const response = await http.post(
      `${this.baseUrl}/moderations`,
      { input },
      {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        }
      }
    );
    return response.data;
  }
}

// GitHub Service
class GitHubService {
  constructor(apiToken) {
    this.apiToken = apiToken;
    this.baseUrl = 'https://api.github.com';
    this.repo = 'gSimani/ConcordBroker';
  }

  async getCommits(branch = 'main', limit = 10) {
    const response = await http.get(
      `${this.baseUrl}/repos/${this.repo}/commits?sha=${branch}&per_page=${limit}`,
      {
        headers: {
          'Authorization': `token ${this.apiToken}`,
          'Accept': 'application/vnd.github.v3+json'
        }
      }
    );
    return response.data;
  }

  async createIssue(title, body, labels = []) {
    const response = await http.post(
      `${this.baseUrl}/repos/${this.repo}/issues`,
      { title, body, labels },
      {
        headers: {
          'Authorization': `token ${this.apiToken}`,
          'Accept': 'application/vnd.github.v3+json'
        }
      }
    );
    return response.data;
  }

  async createPullRequest(title, head, base, body) {
    const response = await http.post(
      `${this.baseUrl}/repos/${this.repo}/pulls`,
      { title, head, base, body },
      {
        headers: {
          'Authorization': `token ${this.apiToken}`,
          'Accept': 'application/vnd.github.v3+json'
        }
      }
    );
    return response.data;
  }

  async getWorkflowRuns(workflowId) {
    const response = await http.get(
      `${this.baseUrl}/repos/${this.repo}/actions/workflows/${workflowId}/runs`,
      {
        headers: {
          'Authorization': `token ${this.apiToken}`,
          'Accept': 'application/vnd.github.v3+json'
        }
      }
    );
    return response.data;
  }

  async triggerWorkflow(workflowId, ref = 'main', inputs = {}) {
    const response = await http.post(
      `${this.baseUrl}/repos/${this.repo}/actions/workflows/${workflowId}/dispatches`,
      { ref, inputs },
      {
        headers: {
          'Authorization': `token ${this.apiToken}`,
          'Accept': 'application/vnd.github.v3+json'
        }
      }
    );
    return response.data;
  }

  async getBranches() {
    const response = await http.get(
      `${this.baseUrl}/repos/${this.repo}/branches`,
      {
        headers: {
          'Authorization': `token ${this.apiToken}`,
          'Accept': 'application/vnd.github.v3+json'
        }
      }
    );
    return response.data;
  }

  async createBranch(branchName, sha) {
    const response = await http.post(
      `${this.baseUrl}/repos/${this.repo}/git/refs`,
      {
        ref: `refs/heads/${branchName}`,
        sha: sha
      },
      {
        headers: {
          'Authorization': `token ${this.apiToken}`,
          'Accept': 'application/vnd.github.v3+json'
        }
      }
    );
    return response.data;
  }
}

module.exports = {
  VercelService,
  RailwayService,
  SupabaseService,
  HuggingFaceService,
  OpenAIService,
  GitHubService
};
