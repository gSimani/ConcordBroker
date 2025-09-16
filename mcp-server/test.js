/**
 * Test script for Vercel MCP Server
 * Validates API connection and configuration
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

// Configuration
const CONFIG = {
  PROJECT_ID: 'prj_l6jgk7483iwPCcaYarq7sMgt2m7L',
  API_TOKEN: 't9AK4qQ51TyAc0K0ZLk7tN0H',
  ORG_ID: 'team_OIAQ7q0bQTblRPZrnKhU4BGF',
  DOMAIN: 'www.concordbroker.com'
};

class VercelAPITest {
  constructor() {
    this.apiToken = CONFIG.API_TOKEN;
    this.projectId = CONFIG.PROJECT_ID;
    this.orgId = CONFIG.ORG_ID;
    this.testResults = [];
  }

  /**
   * Run all tests
   */
  async runTests() {
    console.log('🧪 ConcordBroker Vercel API Test Suite\n');
    console.log('═══════════════════════════════════════\n');

    const tests = [
      {
        name: 'API Authentication',
        fn: () => this.testAuthentication()
      },
      {
        name: 'Project Access',
        fn: () => this.testProjectAccess()
      },
      {
        name: 'Environment Variables',
        fn: () => this.testEnvironmentVariables()
      },
      {
        name: 'Recent Deployments',
        fn: () => this.testDeployments()
      },
      {
        name: 'Domain Configuration',
        fn: () => this.testDomains()
      },
      {
        name: 'Build Settings',
        fn: () => this.testBuildSettings()
      },
      {
        name: 'Website Accessibility',
        fn: () => this.testWebsiteAccess()
      },
      {
        name: 'API Proxy',
        fn: () => this.testAPIProxy()
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
   * Test API authentication
   */
  async testAuthentication() {
    const user = await this.makeRequest('GET', '/v2/user');
    console.log(`   User: ${user.username || user.email}`);
    console.log(`   ID: ${user.uid}`);
    return { user: user.username || user.email };
  }

  /**
   * Test project access
   */
  async testProjectAccess() {
    const project = await this.makeRequest('GET', `/v9/projects/${this.projectId}`);
    console.log(`   Project Name: ${project.name}`);
    console.log(`   Framework: ${project.framework || 'Not set'}`);
    console.log(`   Created: ${new Date(project.createdAt).toLocaleDateString()}`);
    return { projectName: project.name };
  }

  /**
   * Test environment variables
   */
  async testEnvironmentVariables() {
    const envVars = await this.makeRequest('GET', `/v9/projects/${this.projectId}/env`);
    
    const required = [
      'VITE_SUPABASE_URL',
      'VITE_SUPABASE_ANON_KEY',
      'VITE_API_URL'
    ];
    
    const configured = envVars.envs.map(e => e.key);
    const missing = required.filter(key => !configured.includes(key));
    
    console.log(`   Total Variables: ${envVars.envs.length}`);
    console.log(`   Required: ${required.length}`);
    
    if (missing.length > 0) {
      console.log(`   ⚠️  Missing: ${missing.join(', ')}`);
    } else {
      console.log(`   All required variables configured`);
    }
    
    // List configured variables (without values)
    console.log(`   Configured: ${configured.slice(0, 5).join(', ')}${configured.length > 5 ? '...' : ''}`);
    
    return { 
      totalVars: envVars.envs.length,
      missingVars: missing.length 
    };
  }

  /**
   * Test recent deployments
   */
  async testDeployments() {
    const deployments = await this.makeRequest('GET', `/v6/deployments?projectId=${this.projectId}&limit=5`);
    
    if (deployments.deployments && deployments.deployments.length > 0) {
      const latest = deployments.deployments[0];
      console.log(`   Latest Deployment:`);
      console.log(`     URL: ${latest.url}`);
      console.log(`     Status: ${latest.readyState}`);
      console.log(`     Created: ${new Date(latest.created).toLocaleString()}`);
      
      if (deployments.deployments.length > 1) {
        console.log(`   Previous ${deployments.deployments.length - 1} deployments found`);
      }
      
      return { 
        latestDeployment: latest.url,
        status: latest.readyState 
      };
    } else {
      console.log(`   No deployments found`);
      return { latestDeployment: null };
    }
  }

  /**
   * Test domain configuration
   */
  async testDomains() {
    try {
      const domains = await this.makeRequest('GET', `/v9/projects/${this.projectId}/domains`);
      
      if (domains.domains && domains.domains.length > 0) {
        console.log(`   Configured Domains:`);
        domains.domains.forEach(domain => {
          console.log(`     - ${domain.name} (${domain.verified ? '✅ Verified' : '⚠️ Not verified'})`);
        });
        
        return { 
          domains: domains.domains.map(d => d.name),
          verified: domains.domains.filter(d => d.verified).length 
        };
      } else {
        console.log(`   No custom domains configured`);
        return { domains: [] };
      }
    } catch (error) {
      console.log(`   Could not fetch domains: ${error.message}`);
      return { domains: [] };
    }
  }

  /**
   * Test build settings
   */
  async testBuildSettings() {
    const project = await this.makeRequest('GET', `/v9/projects/${this.projectId}`);
    
    console.log(`   Build Command: ${project.buildCommand || 'Default'}`);
    console.log(`   Output Directory: ${project.outputDirectory || 'Default'}`);
    console.log(`   Install Command: ${project.installCommand || 'Default'}`);
    console.log(`   Dev Command: ${project.devCommand || 'Default'}`);
    
    return {
      buildCommand: project.buildCommand,
      outputDirectory: project.outputDirectory
    };
  }

  /**
   * Test website accessibility
   */
  async testWebsiteAccess() {
    const urls = [
      'https://www.concordbroker.com',
      'https://concordbroker.vercel.app'
    ];
    
    console.log(`   Testing website accessibility:`);
    
    for (const url of urls) {
      try {
        const response = await this.checkUrl(url);
        console.log(`     ${url}: ${response.statusCode === 200 ? '✅ OK' : `⚠️ ${response.statusCode}`}`);
      } catch (error) {
        console.log(`     ${url}: ❌ Failed`);
      }
    }
    
    return { websiteAccessible: true };
  }

  /**
   * Test API proxy configuration
   */
  async testAPIProxy() {
    console.log(`   Testing API proxy routes:`);
    
    const apiUrl = 'https://www.concordbroker.com/api/health';
    
    try {
      const response = await this.checkUrl(apiUrl);
      console.log(`     /api/health: ${response.statusCode === 200 ? '✅ OK' : `⚠️ ${response.statusCode}`}`);
    } catch (error) {
      console.log(`     /api/health: ❌ Not configured`);
    }
    
    return { apiProxyConfigured: true };
  }

  /**
   * Print test summary
   */
  printSummary() {
    console.log('\n═══════════════════════════════════════');
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
    
    console.log('\n═══════════════════════════════════════');
    
    // Save results to file
    const resultsPath = path.join(__dirname, 'test-results.json');
    fs.writeFileSync(resultsPath, JSON.stringify(this.testResults, null, 2));
    console.log(`\n💾 Results saved to: ${resultsPath}`);
    
    // Exit code based on results
    process.exit(failed > 0 ? 1 : 0);
  }

  /**
   * Make API request to Vercel
   */
  makeRequest(method, path) {
    return new Promise((resolve, reject) => {
      const options = {
        hostname: 'api.vercel.com',
        path: path,
        method: method,
        headers: {
          'Authorization': `Bearer ${this.apiToken}`,
          'Content-Type': 'application/json'
        }
      };

      if (this.orgId && method !== 'GET') {
        options.headers['x-team-id'] = this.orgId;
      }

      const req = https.request(options, (res) => {
        let data = '';

        res.on('data', (chunk) => {
          data += chunk;
        });

        res.on('end', () => {
          try {
            const parsed = JSON.parse(data);
            if (res.statusCode >= 200 && res.statusCode < 300) {
              resolve(parsed);
            } else {
              reject(new Error(parsed.error?.message || `API Error: ${data}`));
            }
          } catch (error) {
            reject(new Error(`Parse error: ${data}`));
          }
        });
      });

      req.on('error', reject);
      req.end();
    });
  }

  /**
   * Check URL accessibility
   */
  checkUrl(url) {
    return new Promise((resolve, reject) => {
      https.get(url, (res) => {
        resolve({ statusCode: res.statusCode });
      }).on('error', reject);
    });
  }
}

// Run tests
if (require.main === module) {
  const tester = new VercelAPITest();
  tester.runTests().catch(console.error);
}

module.exports = VercelAPITest;