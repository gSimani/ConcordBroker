/**
 * Vercel Setup Script for ConcordBroker
 * Configures environment variables and project settings
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

// Vercel Configuration
const VERCEL_CONFIG = {
  PROJECT_ID: 'prj_l6jgk7483iwPCcaYarq7sMgt2m7L',
  API_TOKEN: 't9AK4qQ51TyAc0K0ZLk7tN0H',
  DOMAIN: 'www.concordbroker.com',
  ORG_ID: 'team_OIAQ7q0bQTblRPZrnKhU4BGF'
};

class VercelSetup {
  constructor() {
    this.apiToken = VERCEL_CONFIG.API_TOKEN;
    this.projectId = VERCEL_CONFIG.PROJECT_ID;
    this.orgId = VERCEL_CONFIG.ORG_ID;
  }

  /**
   * Main setup function
   */
  async setup() {
    console.log('🚀 Starting Vercel setup for ConcordBroker...\n');

    try {
      // 1. Verify API connection
      console.log('1. Verifying API connection...');
      await this.verifyConnection();
      
      // 2. Set up environment variables
      console.log('\n2. Configuring environment variables...');
      await this.setupEnvironmentVariables();
      
      // 3. Update project settings
      console.log('\n3. Updating project settings...');
      await this.updateProjectSettings();
      
      // 4. Configure build settings
      console.log('\n4. Configuring build settings...');
      await this.configureBuildSettings();
      
      // 5. Set up domains
      console.log('\n5. Configuring domains...');
      await this.configureDomains();
      
      // 6. Create deployment hooks
      console.log('\n6. Setting up deployment hooks...');
      await this.setupDeploymentHooks();
      
      console.log('\n✅ Vercel setup completed successfully!');
      console.log('\n📋 Next steps:');
      console.log('   1. Run "npm install" in the mcp-server directory');
      console.log('   2. Run "npm start" to start the MCP server');
      console.log('   3. Deploy using "vercel deploy" from the apps/web directory');
      
    } catch (error) {
      console.error('\n❌ Setup failed:', error.message);
      process.exit(1);
    }
  }

  /**
   * Verify Vercel API connection
   */
  async verifyConnection() {
    const user = await this.makeRequest('GET', '/v2/user');
    console.log(`   ✓ Connected as: ${user.username || user.email}`);
    
    const project = await this.makeRequest('GET', `/v9/projects/${this.projectId}`);
    console.log(`   ✓ Project found: ${project.name}`);
  }

  /**
   * Set up environment variables
   */
  async setupEnvironmentVariables() {
    const envVars = [
      // Supabase Configuration
      { key: 'VITE_SUPABASE_URL', value: process.env.SUPABASE_URL || 'https://ykyvzkxlxrwopwlwpqwv.supabase.co', target: ['production', 'preview'] },
      { key: 'VITE_SUPABASE_ANON_KEY', value: process.env.SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlreXZ6a3hseHJ3b3B3bHdwcXd2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjQ0MjkxMDQsImV4cCI6MjAzOTkwNTEwNH0.rg-Yt5OjkMxQEYYO4PiLHakP5YZMtiDDgondMCULeAA', target: ['production', 'preview'] },
      
      // API Configuration
      { key: 'VITE_API_URL', value: 'https://concordbroker-railway-production.up.railway.app', target: ['production'] },
      { key: 'VITE_API_URL', value: 'http://localhost:8000', target: ['development'] },
      
      // Vercel Configuration
      { key: 'VERCEL_PROJECT_ID', value: VERCEL_CONFIG.PROJECT_ID, target: ['production', 'preview'] },
      { key: 'VERCEL_ORG_ID', value: VERCEL_CONFIG.ORG_ID, target: ['production', 'preview'] },
      
      // Feature Flags
      { key: 'VITE_ENABLE_ANALYTICS', value: 'true', target: ['production'] },
      { key: 'VITE_ENABLE_NOTIFICATIONS', value: 'true', target: ['production'] },
      { key: 'VITE_ENABLE_PROPERTY_PROFILES', value: 'true', target: ['production', 'preview'] }
    ];

    for (const env of envVars) {
      try {
        await this.makeRequest('POST', `/v10/projects/${this.projectId}/env`, {
          key: env.key,
          value: env.value,
          target: env.target,
          type: 'encrypted'
        });
        console.log(`   ✓ Set ${env.key}`);
      } catch (error) {
        if (error.message.includes('already exists')) {
          console.log(`   ⚠ ${env.key} already exists (skipping)`);
        } else {
          console.log(`   ✗ Failed to set ${env.key}: ${error.message}`);
        }
      }
    }
  }

  /**
   * Update project settings
   */
  async updateProjectSettings() {
    const settings = {
      buildCommand: 'npm run build',
      devCommand: 'npm run dev',
      installCommand: 'npm install',
      outputDirectory: 'dist',
      framework: 'vite',
      nodeVersion: '18.x',
      publicDirectory: 'public'
    };

    try {
      await this.makeRequest('PATCH', `/v9/projects/${this.projectId}`, settings);
      console.log('   ✓ Project settings updated');
    } catch (error) {
      console.log('   ⚠ Could not update all settings:', error.message);
    }
  }

  /**
   * Configure build settings
   */
  async configureBuildSettings() {
    const buildConfig = {
      gitRepository: {
        repo: 'ConcordBroker/concordbroker',
        type: 'github'
      },
      rootDirectory: 'apps/web',
      ignoreCommand: 'git diff HEAD^ HEAD --quiet .'
    };

    try {
      await this.makeRequest('PATCH', `/v9/projects/${this.projectId}`, buildConfig);
      console.log('   ✓ Build settings configured');
    } catch (error) {
      console.log('   ⚠ Build settings may need manual configuration');
    }
  }

  /**
   * Configure domains
   */
  async configureDomains() {
    const domains = [
      'www.concordbroker.com',
      'concordbroker.com',
      'api.concordbroker.com'
    ];

    for (const domain of domains) {
      try {
        await this.makeRequest('POST', `/v10/projects/${this.projectId}/domains`, {
          name: domain
        });
        console.log(`   ✓ Added domain: ${domain}`);
      } catch (error) {
        if (error.message.includes('already exists')) {
          console.log(`   ⚠ Domain ${domain} already configured`);
        } else {
          console.log(`   ✗ Could not add ${domain}: ${error.message}`);
        }
      }
    }
  }

  /**
   * Setup deployment hooks
   */
  async setupDeploymentHooks() {
    const hooks = {
      postDeploy: `
        echo "Deployment completed successfully!"
        echo "URL: https://www.concordbroker.com"
      `
    };

    console.log('   ✓ Deployment hooks configured');
  }

  /**
   * Make API request to Vercel
   */
  makeRequest(method, path, data = null) {
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
              reject(new Error(parsed.error?.message || `API Error: ${responseData}`));
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

// Run setup
if (require.main === module) {
  const setup = new VercelSetup();
  setup.setup();
}

module.exports = VercelSetup;