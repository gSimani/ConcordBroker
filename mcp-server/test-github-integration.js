/**
 * Test GitHub-Vercel Integration
 * Validates the complete CI/CD pipeline setup
 */

const https = require('https');
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

class GitHubVercelTest {
  constructor() {
    this.githubToken = process.env.GITHUB_TOKEN;
    this.vercelToken = process.env.VERCEL_API_TOKEN;
    this.owner = 'gSimani';
    this.repo = 'ConcordBroker';
    this.testResults = [];
  }

  /**
   * Run all integration tests
   */
  async runTests() {
    console.log('🧪 GitHub-Vercel Integration Test Suite\n');
    console.log('═══════════════════════════════════════\n');

    const tests = [
      {
        name: 'GitHub Repository Access',
        fn: () => this.testGitHubAccess()
      },
      {
        name: 'GitHub Actions Workflow',
        fn: () => this.testWorkflow()
      },
      {
        name: 'Webhook Configuration',
        fn: () => this.testWebhooks()
      },
      {
        name: 'Vercel Project Link',
        fn: () => this.testVercelLink()
      },
      {
        name: 'Recent Commits',
        fn: () => this.testCommits()
      },
      {
        name: 'Branch Protection',
        fn: () => this.testBranchProtection()
      },
      {
        name: 'Deployment Status',
        fn: () => this.testDeploymentStatus()
      },
      {
        name: 'Git Configuration',
        fn: () => this.testGitConfig()
      }
    ];

    for (const test of tests) {
      console.log(`📝 Testing: ${test.name}`);
      try {
        const result = await test.fn();
        this.testResults.push({ name: test.name, status: 'PASSED', ...result });
        console.log(`   ✅ PASSED\n`);
      } catch (error) {
        this.testResults.push({ name: test.name, status: 'FAILED', error: error.message });
        console.log(`   ❌ FAILED: ${error.message}\n`);
      }
    }

    this.printSummary();
  }

  /**
   * Test GitHub repository access
   */
  async testGitHubAccess() {
    const repo = await this.makeGitHubRequest('GET', `/repos/${this.owner}/${this.repo}`);
    
    console.log(`   Repository: ${repo.full_name}`);
    console.log(`   Default Branch: ${repo.default_branch}`);
    console.log(`   Created: ${new Date(repo.created_at).toLocaleDateString()}`);
    console.log(`   Stars: ${repo.stargazers_count}`);
    console.log(`   Open Issues: ${repo.open_issues_count}`);
    
    return {
      repository: repo.full_name,
      defaultBranch: repo.default_branch
    };
  }

  /**
   * Test GitHub Actions workflow
   */
  async testWorkflow() {
    const workflowPath = path.join(__dirname, '..', '.github', 'workflows', 'deploy.yml');
    
    if (!fs.existsSync(workflowPath)) {
      throw new Error('Workflow file not found');
    }
    
    const content = fs.readFileSync(workflowPath, 'utf8');
    
    // Check for required jobs
    const hasTestJob = content.includes('jobs:') && content.includes('test:');
    const hasDeployPreview = content.includes('deploy-preview:');
    const hasDeployProduction = content.includes('deploy-production:');
    
    console.log(`   Test Job: ${hasTestJob ? '✓' : '✗'}`);
    console.log(`   Preview Deploy: ${hasDeployPreview ? '✓' : '✗'}`);
    console.log(`   Production Deploy: ${hasDeployProduction ? '✓' : '✗'}`);
    
    // Check workflow runs
    try {
      const runs = await this.makeGitHubRequest('GET', 
        `/repos/${this.owner}/${this.repo}/actions/runs?per_page=5`);
      
      if (runs.workflow_runs && runs.workflow_runs.length > 0) {
        console.log(`   Recent Runs: ${runs.workflow_runs.length}`);
        const latest = runs.workflow_runs[0];
        console.log(`   Latest: ${latest.status} (${latest.conclusion || 'in progress'})`);
      } else {
        console.log(`   No workflow runs yet`);
      }
    } catch (error) {
      console.log(`   Could not fetch workflow runs`);
    }
    
    return { workflowConfigured: hasTestJob && hasDeployPreview && hasDeployProduction };
  }

  /**
   * Test webhook configuration
   */
  async testWebhooks() {
    const webhooks = await this.makeGitHubRequest('GET', 
      `/repos/${this.owner}/${this.repo}/hooks`);
    
    console.log(`   Total Webhooks: ${webhooks.length}`);
    
    const vercelWebhook = webhooks.find(w => 
      w.config.url && w.config.url.includes('vercel.com'));
    
    if (vercelWebhook) {
      console.log(`   Vercel Webhook: ✓ Configured`);
      console.log(`   Events: ${vercelWebhook.events.join(', ')}`);
      console.log(`   Active: ${vercelWebhook.active ? 'Yes' : 'No'}`);
      
      // Test webhook
      try {
        const test = await this.makeGitHubRequest('POST', 
          `/repos/${this.owner}/${this.repo}/hooks/${vercelWebhook.id}/tests`);
        console.log(`   Test Ping: Sent`);
      } catch (error) {
        console.log(`   Test Ping: Could not send`);
      }
    } else {
      console.log(`   Vercel Webhook: Not found`);
    }
    
    return { webhookConfigured: !!vercelWebhook };
  }

  /**
   * Test Vercel project link
   */
  async testVercelLink() {
    // Check if Vercel is linked by testing deployment status
    const deployments = await this.makeVercelRequest('GET', 
      '/v6/deployments?projectId=prj_l6jgk7483iwPCcaYarq7sMgt2m7L&limit=5');
    
    console.log(`   Vercel Deployments: ${deployments.deployments?.length || 0}`);
    
    if (deployments.deployments && deployments.deployments.length > 0) {
      const latest = deployments.deployments[0];
      
      // Check if deployment was triggered by GitHub
      if (latest.meta?.githubCommitRef) {
        console.log(`   GitHub Integration: ✓ Active`);
        console.log(`   Last Deploy from: ${latest.meta.githubCommitRef}`);
        console.log(`   Commit: ${latest.meta.githubCommitSha?.substring(0, 7)}`);
      } else {
        console.log(`   GitHub Integration: Manual deployments only`);
      }
      
      console.log(`   Latest Deploy: ${latest.url}`);
      console.log(`   Status: ${latest.readyState}`);
    }
    
    return { vercelLinked: deployments.deployments?.length > 0 };
  }

  /**
   * Test recent commits
   */
  async testCommits() {
    const commits = await this.makeGitHubRequest('GET', 
      `/repos/${this.owner}/${this.repo}/commits?per_page=5`);
    
    console.log(`   Recent Commits: ${commits.length}`);
    
    if (commits.length > 0) {
      const latest = commits[0];
      console.log(`   Latest: ${latest.commit.message.split('\n')[0]}`);
      console.log(`   Author: ${latest.commit.author.name}`);
      console.log(`   Date: ${new Date(latest.commit.author.date).toLocaleString()}`);
    }
    
    return { hasCommits: commits.length > 0 };
  }

  /**
   * Test branch protection
   */
  async testBranchProtection() {
    try {
      const protection = await this.makeGitHubRequest('GET', 
        `/repos/${this.owner}/${this.repo}/branches/main/protection`);
      
      console.log(`   Protection Enabled: ✓`);
      console.log(`   Required Reviews: ${protection.required_pull_request_reviews?.required_approving_review_count || 0}`);
      console.log(`   Status Checks: ${protection.required_status_checks?.contexts?.length || 0}`);
      
      return { protectionEnabled: true };
    } catch (error) {
      console.log(`   Protection Enabled: ✗ (${error.message.includes('404') ? 'Not configured' : error.message})`);
      return { protectionEnabled: false };
    }
  }

  /**
   * Test deployment status
   */
  async testDeploymentStatus() {
    try {
      // Check GitHub deployments
      const deployments = await this.makeGitHubRequest('GET', 
        `/repos/${this.owner}/${this.repo}/deployments?per_page=5`);
      
      console.log(`   GitHub Deployments: ${deployments.length}`);
      
      if (deployments.length > 0) {
        const latest = deployments[0];
        console.log(`   Latest Environment: ${latest.environment}`);
        console.log(`   Created: ${new Date(latest.created_at).toLocaleString()}`);
        
        // Get deployment status
        const statuses = await this.makeGitHubRequest('GET', 
          `/repos/${this.owner}/${this.repo}/deployments/${latest.id}/statuses`);
        
        if (statuses.length > 0) {
          console.log(`   Status: ${statuses[0].state}`);
        }
      }
      
      // Check Vercel deployment
      const vercelDeploys = await this.makeVercelRequest('GET', 
        '/v6/deployments?projectId=prj_l6jgk7483iwPCcaYarq7sMgt2m7L&limit=1');
      
      if (vercelDeploys.deployments && vercelDeploys.deployments.length > 0) {
        const vercel = vercelDeploys.deployments[0];
        console.log(`   Vercel Status: ${vercel.readyState}`);
        console.log(`   URL: https://${vercel.url}`);
      }
      
      return { deploymentsConfigured: true };
    } catch (error) {
      console.log(`   Could not fetch deployment status`);
      return { deploymentsConfigured: false };
    }
  }

  /**
   * Test Git configuration
   */
  async testGitConfig() {
    try {
      const remote = execSync('git remote get-url origin', { encoding: 'utf8' }).trim();
      console.log(`   Remote URL: ${remote}`);
      
      const branch = execSync('git branch --show-current', { encoding: 'utf8' }).trim();
      console.log(`   Current Branch: ${branch}`);
      
      const status = execSync('git status --porcelain', { encoding: 'utf8' });
      const changes = status.split('\n').filter(line => line.trim()).length;
      console.log(`   Uncommitted Changes: ${changes}`);
      
      return { gitConfigured: remote.includes('github.com') };
    } catch (error) {
      console.log(`   Git not properly configured`);
      return { gitConfigured: false };
    }
  }

  /**
   * Make GitHub API request
   */
  makeGitHubRequest(method, path, data = null) {
    return new Promise((resolve, reject) => {
      const options = {
        hostname: 'api.github.com',
        path: path,
        method: method,
        headers: {
          'Authorization': `Bearer ${this.githubToken}`,
          'Accept': 'application/vnd.github.v3+json',
          'User-Agent': 'ConcordBroker-Test'
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
              reject(new Error(parsed.message || `Status ${res.statusCode}`));
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
   * Make Vercel API request
   */
  makeVercelRequest(method, path) {
    return new Promise((resolve, reject) => {
      const options = {
        hostname: 'api.vercel.com',
        path: path,
        method: method,
        headers: {
          'Authorization': `Bearer ${this.vercelToken}`,
          'Content-Type': 'application/json'
        }
      };

      const req = https.request(options, (res) => {
        let data = '';

        res.on('data', (chunk) => {
          data += chunk;
        });

        res.on('end', () => {
          try {
            resolve(JSON.parse(data));
          } catch (error) {
            reject(error);
          }
        });
      });

      req.on('error', reject);
      req.end();
    });
  }

  /**
   * Print test summary
   */
  printSummary() {
    console.log('═══════════════════════════════════════');
    console.log('📊 Test Summary\n');
    
    const passed = this.testResults.filter(r => r.status === 'PASSED').length;
    const failed = this.testResults.filter(r => r.status === 'FAILED').length;
    const total = this.testResults.length;
    
    console.log(`   Total Tests: ${total}`);
    console.log(`   ✅ Passed: ${passed}`);
    console.log(`   ❌ Failed: ${failed}`);
    console.log(`   Success Rate: ${((passed / total) * 100).toFixed(1)}%`);
    
    if (failed > 0) {
      console.log('\n   Failed Tests:');
      this.testResults
        .filter(r => r.status === 'FAILED')
        .forEach(r => {
          console.log(`     - ${r.name}: ${r.error}`);
        });
    }
    
    console.log('\n📋 Action Items:');
    console.log('   1. Add secrets to GitHub repository settings');
    console.log('   2. Enable branch protection rules');
    console.log('   3. Configure Vercel GitHub integration in dashboard');
    console.log('   4. Test deployment by pushing to main branch');
    
    console.log('\n═══════════════════════════════════════');
  }
}

// Run tests
if (require.main === module) {
  const tester = new GitHubVercelTest();
  tester.runTests().catch(console.error);
}

module.exports = GitHubVercelTest;
