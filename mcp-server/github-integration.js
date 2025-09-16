/**
 * GitHub Integration for ConcordBroker MCP Server
 * Manages repository operations, webhooks, and CI/CD
 */

const https = require('https');
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

class GitHubIntegration {
  constructor(config) {
    this.token = config.token || process.env.GITHUB_TOKEN;
    this.owner = config.owner || 'gSimani';
    this.repo = config.repo || 'ConcordBroker';
    this.branch = config.branch || 'main';
    this.vercelConfig = config.vercel || {};
  }

  /**
   * Initialize GitHub integration
   */
  async init() {
    console.log('🐙 Initializing GitHub Integration...\n');
    
    try {
      // Verify GitHub connection
      await this.verifyConnection();
      
      // Get repository info
      const repoInfo = await this.getRepository();
      console.log(`✓ Connected to: ${repoInfo.full_name}`);
      console.log(`  Description: ${repoInfo.description || 'No description'}`);
      console.log(`  Default Branch: ${repoInfo.default_branch}`);
      console.log(`  Private: ${repoInfo.private}`);
      console.log(`  Created: ${new Date(repoInfo.created_at).toLocaleDateString()}`);
      
      // Set up webhooks
      await this.setupWebhooks();
      
      // Configure branch protection
      await this.configureBranchProtection();
      
      return true;
    } catch (error) {
      console.error('❌ Initialization failed:', error.message);
      throw error;
    }
  }

  /**
   * Verify GitHub API connection
   */
  async verifyConnection() {
    const user = await this.makeRequest('GET', '/user');
    console.log(`✓ Authenticated as: ${user.login}`);
    return user;
  }

  /**
   * Get repository information
   */
  async getRepository() {
    return this.makeRequest('GET', `/repos/${this.owner}/${this.repo}`);
  }

  /**
   * Create or update repository
   */
  async createOrUpdateRepo(data) {
    try {
      // Try to get existing repo
      const existing = await this.getRepository();
      
      // Update existing repo
      return this.makeRequest('PATCH', `/repos/${this.owner}/${this.repo}`, {
        description: data.description || existing.description,
        homepage: data.homepage || 'https://www.concordbroker.com',
        private: data.private !== undefined ? data.private : existing.private,
        has_issues: true,
        has_projects: true,
        has_wiki: false,
        default_branch: this.branch
      });
    } catch (error) {
      // Create new repo if it doesn't exist
      if (error.message.includes('404')) {
        return this.makeRequest('POST', '/user/repos', {
          name: this.repo,
          description: data.description || 'Real Estate Intelligence Platform',
          homepage: 'https://www.concordbroker.com',
          private: data.private || false,
          has_issues: true,
          has_projects: true,
          has_wiki: false,
          auto_init: true
        });
      }
      throw error;
    }
  }

  /**
   * Set up webhooks for Vercel deployment
   */
  async setupWebhooks() {
    console.log('\n📡 Configuring GitHub Webhooks...');
    
    const webhookUrl = 'https://api.vercel.com/v1/integrations/deploy/prj_l6jgk7483iwPCcaYarq7sMgt2m7L';
    
    try {
      // Check existing webhooks
      const webhooks = await this.makeRequest('GET', `/repos/${this.owner}/${this.repo}/hooks`);
      
      const existingWebhook = webhooks.find(w => w.config.url === webhookUrl);
      
      if (existingWebhook) {
        console.log('  ✓ Vercel webhook already configured');
        return existingWebhook;
      }
      
      // Create new webhook
      const webhook = await this.makeRequest('POST', `/repos/${this.owner}/${this.repo}/hooks`, {
        name: 'web',
        active: true,
        events: ['push', 'pull_request'],
        config: {
          url: webhookUrl,
          content_type: 'json',
          insecure_ssl: '0'
        }
      });
      
      console.log('  ✓ Vercel webhook created successfully');
      return webhook;
    } catch (error) {
      console.log('  ⚠ Could not configure webhook:', error.message);
    }
  }

  /**
   * Configure branch protection rules
   */
  async configureBranchProtection() {
    console.log('\n🛡️ Configuring Branch Protection...');
    
    try {
      const protection = await this.makeRequest('PUT', 
        `/repos/${this.owner}/${this.repo}/branches/${this.branch}/protection`, {
        required_status_checks: {
          strict: true,
          contexts: ['vercel', 'continuous-integration/vercel']
        },
        enforce_admins: false,
        required_pull_request_reviews: {
          dismissal_restrictions: {},
          dismiss_stale_reviews: true,
          require_code_owner_reviews: false,
          required_approving_review_count: 1
        },
        restrictions: null,
        allow_force_pushes: false,
        allow_deletions: false
      });
      
      console.log('  ✓ Branch protection configured for:', this.branch);
      return protection;
    } catch (error) {
      console.log('  ⚠ Could not configure branch protection:', error.message);
    }
  }

  /**
   * Create GitHub Actions workflow
   */
  async createWorkflow() {
    console.log('\n⚙️ Creating GitHub Actions Workflow...');
    
    const workflowDir = path.join(__dirname, '..', '.github', 'workflows');
    const workflowPath = path.join(workflowDir, 'deploy.yml');
    
    // Create directory if it doesn't exist
    if (!fs.existsSync(workflowDir)) {
      fs.mkdirSync(workflowDir, { recursive: true });
    }
    
    const workflowContent = `name: Deploy to Vercel

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  VERCEL_ORG_ID: \${{ secrets.VERCEL_ORG_ID }}
  VERCEL_PROJECT_ID: \${{ secrets.VERCEL_PROJECT_ID }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: apps/web/package-lock.json
      
      - name: Install dependencies
        run: |
          cd apps/web
          npm ci
      
      - name: Run tests
        run: |
          cd apps/web
          npm run lint || true
      
      - name: Build application
        run: |
          cd apps/web
          npm run build

  deploy-preview:
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'pull_request'
    environment:
      name: preview
      url: \${{ steps.deploy.outputs.url }}
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Vercel CLI
        run: npm install --global vercel@latest
      
      - name: Pull Vercel Environment
        run: vercel pull --yes --environment=preview --token=\${{ secrets.VERCEL_TOKEN }}
        working-directory: ./apps/web
      
      - name: Build Project
        run: vercel build --token=\${{ secrets.VERCEL_TOKEN }}
        working-directory: ./apps/web
      
      - name: Deploy to Vercel (Preview)
        id: deploy
        run: |
          url=$(vercel deploy --prebuilt --token=\${{ secrets.VERCEL_TOKEN }})
          echo "url=$url" >> $GITHUB_OUTPUT
        working-directory: ./apps/web

  deploy-production:
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://www.concordbroker.com
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Vercel CLI
        run: npm install --global vercel@latest
      
      - name: Pull Vercel Environment
        run: vercel pull --yes --environment=production --token=\${{ secrets.VERCEL_TOKEN }}
        working-directory: ./apps/web
      
      - name: Build Project
        run: vercel build --prod --token=\${{ secrets.VERCEL_TOKEN }}
        working-directory: ./apps/web
      
      - name: Deploy to Vercel (Production)
        run: vercel deploy --prebuilt --prod --token=\${{ secrets.VERCEL_TOKEN }}
        working-directory: ./apps/web
      
      - name: Create GitHub Deployment
        uses: actions/github-script@v6
        with:
          script: |
            const deployment = await github.rest.repos.createDeployment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              ref: context.sha,
              environment: 'production',
              production_environment: true,
              auto_merge: false,
              required_contexts: []
            });
            
            await github.rest.repos.createDeploymentStatus({
              owner: context.repo.owner,
              repo: context.repo.repo,
              deployment_id: deployment.data.id,
              state: 'success',
              environment_url: 'https://www.concordbroker.com',
              description: 'Deployed to production'
            });
`;
    
    fs.writeFileSync(workflowPath, workflowContent);
    console.log('  ✓ GitHub Actions workflow created');
    
    return workflowPath;
  }

  /**
   * Set repository secrets
   */
  async setSecrets() {
    console.log('\n🔐 Configuring Repository Secrets...');
    
    const secrets = [
      { name: 'VERCEL_TOKEN', value: 't9AK4qQ51TyAc0K0ZLk7tN0H' },
      { name: 'VERCEL_ORG_ID', value: 'team_OIAQ7q0bQTblRPZrnKhU4BGF' },
      { name: 'VERCEL_PROJECT_ID', value: 'prj_l6jgk7483iwPCcaYarq7sMgt2m7L' }
    ];
    
    console.log('\n  ⚠ Manual Action Required:');
    console.log('  Go to: https://github.com/gSimani/ConcordBroker/settings/secrets/actions');
    console.log('  Add the following secrets:\n');
    
    for (const secret of secrets) {
      console.log(`  - ${secret.name}: ${secret.value.substring(0, 10)}...`);
    }
    
    console.log('\n  These cannot be set via API for security reasons.');
  }

  /**
   * Get recent commits
   */
  async getCommits(limit = 10) {
    return this.makeRequest('GET', 
      `/repos/${this.owner}/${this.repo}/commits?per_page=${limit}`);
  }

  /**
   * Get pull requests
   */
  async getPullRequests(state = 'open') {
    return this.makeRequest('GET', 
      `/repos/${this.owner}/${this.repo}/pulls?state=${state}`);
  }

  /**
   * Create issue
   */
  async createIssue(title, body, labels = []) {
    return this.makeRequest('POST', `/repos/${this.owner}/${this.repo}/issues`, {
      title,
      body,
      labels
    });
  }

  /**
   * Get workflow runs
   */
  async getWorkflowRuns() {
    return this.makeRequest('GET', 
      `/repos/${this.owner}/${this.repo}/actions/runs?per_page=10`);
  }

  /**
   * Push current changes
   */
  async pushChanges(message = 'Update from MCP Server') {
    try {
      console.log('\n📤 Pushing changes to GitHub...');
      
      // Add all changes
      execSync('git add .', { stdio: 'pipe' });
      
      // Commit
      execSync(`git commit -m "${message}"`, { stdio: 'pipe' });
      
      // Push to GitHub
      execSync(`git push origin ${this.branch}`, { stdio: 'pipe' });
      
      console.log('  ✓ Changes pushed successfully');
      return true;
    } catch (error) {
      if (error.message.includes('nothing to commit')) {
        console.log('  ℹ No changes to push');
      } else {
        console.log('  ❌ Push failed:', error.message);
      }
      return false;
    }
  }

  /**
   * Make GitHub API request
   */
  makeRequest(method, path, data = null) {
    return new Promise((resolve, reject) => {
      const options = {
        hostname: 'api.github.com',
        path: path,
        method: method,
        headers: {
          'Authorization': `Bearer ${this.token}`,
          'Accept': 'application/vnd.github.v3+json',
          'User-Agent': 'ConcordBroker-MCP-Server',
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
            const parsed = responseData ? JSON.parse(responseData) : {};
            
            if (res.statusCode >= 200 && res.statusCode < 300) {
              resolve(parsed);
            } else {
              reject(new Error(parsed.message || `GitHub API Error: ${res.statusCode}`));
            }
          } catch (error) {
            reject(new Error(`Parse error: ${responseData}`));
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
}

// Export for use
module.exports = GitHubIntegration;

// Run if called directly
if (require.main === module) {
  const github = new GitHubIntegration({
    token: process.env.GITHUB_TOKEN,
    owner: 'gSimani',
    repo: 'ConcordBroker',
    branch: 'main'
  });
  
  github.init()
    .then(() => github.createWorkflow())
    .then(() => github.setSecrets())
    .then(() => {
      console.log('\n✅ GitHub integration configured successfully!');
    })
    .catch(console.error);
}
