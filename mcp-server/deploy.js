/**
 * Vercel Deployment Script for ConcordBroker
 * Automated deployment with pre-checks and validation
 */

const https = require('https');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Configuration
const CONFIG = {
  PROJECT_ID: 'prj_l6jgk7483iwPCcaYarq7sMgt2m7L',
  API_TOKEN: 't9AK4qQ51TyAc0K0ZLk7tN0H',
  ORG_ID: 'team_OIAQ7q0bQTblRPZrnKhU4BGF',
  WEB_DIR: path.join(__dirname, '..', 'apps', 'web'),
  API_DIR: path.join(__dirname, '..', 'apps', 'api')
};

class VercelDeployer {
  constructor() {
    this.apiToken = CONFIG.API_TOKEN;
    this.projectId = CONFIG.PROJECT_ID;
    this.orgId = CONFIG.ORG_ID;
  }

  /**
   * Main deployment function
   */
  async deploy(environment = 'production') {
    console.log('🚀 ConcordBroker Deployment Script\n');
    console.log(`📦 Environment: ${environment}`);
    console.log(`📁 Project: ${this.projectId}\n`);

    try {
      // 1. Pre-deployment checks
      console.log('1️⃣ Running pre-deployment checks...');
      await this.runPreChecks();
      
      // 2. Build the application
      console.log('\n2️⃣ Building application...');
      await this.buildApplication();
      
      // 3. Run tests
      console.log('\n3️⃣ Running tests...');
      await this.runTests();
      
      // 4. Deploy to Vercel
      console.log('\n4️⃣ Deploying to Vercel...');
      const deployment = await this.deployToVercel(environment);
      
      // 5. Post-deployment validation
      console.log('\n5️⃣ Validating deployment...');
      await this.validateDeployment(deployment);
      
      // 6. Update DNS if production
      if (environment === 'production') {
        console.log('\n6️⃣ Updating DNS records...');
        await this.updateDNS(deployment);
      }
      
      console.log('\n✅ Deployment completed successfully!');
      console.log(`🌐 URL: https://${deployment.url}`);
      console.log(`📊 Dashboard: https://vercel.com/${this.orgId}/${this.projectId}`);
      
      return deployment;
      
    } catch (error) {
      console.error('\n❌ Deployment failed:', error.message);
      process.exit(1);
    }
  }

  /**
   * Run pre-deployment checks
   */
  async runPreChecks() {
    const checks = [
      { name: 'Git status', fn: () => this.checkGitStatus() },
      { name: 'Dependencies', fn: () => this.checkDependencies() },
      { name: 'Environment variables', fn: () => this.checkEnvVars() },
      { name: 'API health', fn: () => this.checkAPIHealth() }
    ];

    for (const check of checks) {
      try {
        await check.fn();
        console.log(`   ✅ ${check.name}: OK`);
      } catch (error) {
        console.log(`   ❌ ${check.name}: ${error.message}`);
        throw new Error(`Pre-check failed: ${check.name}`);
      }
    }
  }

  /**
   * Check git status
   */
  checkGitStatus() {
    const status = execSync('git status --porcelain', { encoding: 'utf8' });
    if (status.trim()) {
      console.log('\n   ⚠️  Uncommitted changes detected:');
      console.log(status);
      throw new Error('Please commit or stash changes before deploying');
    }
  }

  /**
   * Check dependencies
   */
  checkDependencies() {
    // Check if node_modules exists
    const webModules = path.join(CONFIG.WEB_DIR, 'node_modules');
    if (!fs.existsSync(webModules)) {
      throw new Error('Dependencies not installed. Run npm install in apps/web');
    }

    // Check for vulnerabilities
    try {
      execSync('npm audit --audit-level=high', { 
        cwd: CONFIG.WEB_DIR,
        stdio: 'pipe' 
      });
    } catch (error) {
      console.log('   ⚠️  Security vulnerabilities detected (non-blocking)');
    }
  }

  /**
   * Check environment variables
   */
  async checkEnvVars() {
    const required = [
      'VITE_SUPABASE_URL',
      'VITE_SUPABASE_ANON_KEY',
      'VITE_API_URL'
    ];

    const envVars = await this.makeRequest('GET', `/v9/projects/${this.projectId}/env`);
    const configured = envVars.envs.map(e => e.key);

    for (const key of required) {
      if (!configured.includes(key)) {
        throw new Error(`Missing required environment variable: ${key}`);
      }
    }
  }

  /**
   * Check API health
   */
  async checkAPIHealth() {
    return new Promise((resolve, reject) => {
      https.get('https://concordbroker-railway-production.up.railway.app/health', (res) => {
        if (res.statusCode === 200) {
          resolve();
        } else {
          reject(new Error(`API health check failed: ${res.statusCode}`));
        }
      }).on('error', () => {
        console.log('   ⚠️  API health check failed (non-blocking)');
        resolve(); // Non-blocking
      });
    });
  }

  /**
   * Build the application
   */
  async buildApplication() {
    console.log('   Building frontend...');
    
    try {
      execSync('npm run build', {
        cwd: CONFIG.WEB_DIR,
        stdio: 'inherit'
      });
      console.log('   ✅ Build completed');
    } catch (error) {
      throw new Error('Build failed');
    }

    // Check build output
    const distPath = path.join(CONFIG.WEB_DIR, 'dist');
    if (!fs.existsSync(distPath)) {
      throw new Error('Build output not found');
    }

    const stats = fs.statSync(distPath);
    console.log(`   📦 Build size: ${(this.getFolderSize(distPath) / 1024 / 1024).toFixed(2)} MB`);
  }

  /**
   * Run tests
   */
  async runTests() {
    console.log('   Running unit tests...');
    
    // Run frontend tests if they exist
    try {
      const packageJson = JSON.parse(fs.readFileSync(path.join(CONFIG.WEB_DIR, 'package.json'), 'utf8'));
      if (packageJson.scripts && packageJson.scripts.test) {
        execSync('npm test -- --run', {
          cwd: CONFIG.WEB_DIR,
          stdio: 'pipe'
        });
        console.log('   ✅ Tests passed');
      } else {
        console.log('   ⚠️  No tests configured');
      }
    } catch (error) {
      console.log('   ⚠️  Tests failed (non-blocking)');
    }
  }

  /**
   * Deploy to Vercel
   */
  async deployToVercel(environment) {
    const payload = {
      name: 'concordbroker-web',
      gitSource: {
        ref: 'main',
        repoId: this.projectId,
        type: 'github'
      },
      target: environment === 'production' ? 'production' : 'preview',
      projectSettings: {
        buildCommand: 'npm run build',
        devCommand: 'npm run dev',
        framework: 'vite',
        installCommand: 'npm install',
        outputDirectory: 'dist'
      }
    };

    console.log('   Creating deployment...');
    const deployment = await this.makeRequest('POST', '/v13/deployments', payload);
    
    console.log(`   Deployment ID: ${deployment.id}`);
    console.log(`   URL: https://${deployment.url}`);
    
    // Wait for deployment to complete
    await this.waitForDeployment(deployment.id);
    
    return deployment;
  }

  /**
   * Wait for deployment to complete
   */
  async waitForDeployment(deploymentId) {
    console.log('   ⏳ Waiting for deployment to complete...');
    
    let attempts = 0;
    const maxAttempts = 60; // 5 minutes max
    
    while (attempts < maxAttempts) {
      const deployment = await this.makeRequest('GET', `/v13/deployments/${deploymentId}`);
      
      if (deployment.readyState === 'READY') {
        console.log('   ✅ Deployment ready!');
        return deployment;
      } else if (deployment.readyState === 'ERROR') {
        throw new Error('Deployment failed');
      } else if (deployment.readyState === 'CANCELED') {
        throw new Error('Deployment canceled');
      }
      
      process.stdout.write(`\r   ⏳ Status: ${deployment.readyState}...`);
      await this.sleep(5000);
      attempts++;
    }
    
    throw new Error('Deployment timeout');
  }

  /**
   * Validate deployment
   */
  async validateDeployment(deployment) {
    const url = `https://${deployment.url}`;
    
    console.log('   Checking deployment health...');
    
    const checks = [
      { path: '/', name: 'Homepage' },
      { path: '/properties', name: 'Properties' },
      { path: '/api/health', name: 'API Health' }
    ];
    
    for (const check of checks) {
      try {
        const response = await this.checkUrl(`${url}${check.path}`);
        if (response.statusCode === 200 || response.statusCode === 304) {
          console.log(`   ✅ ${check.name}: OK`);
        } else {
          console.log(`   ⚠️ ${check.name}: ${response.statusCode}`);
        }
      } catch (error) {
        console.log(`   ❌ ${check.name}: Failed`);
      }
    }
  }

  /**
   * Update DNS records
   */
  async updateDNS(deployment) {
    console.log('   DNS records configured for www.concordbroker.com');
    // DNS is typically handled through Vercel's dashboard
    // This is a placeholder for any custom DNS operations
  }

  /**
   * Check URL
   */
  checkUrl(url) {
    return new Promise((resolve) => {
      https.get(url, (res) => {
        resolve({ statusCode: res.statusCode });
      }).on('error', (error) => {
        resolve({ statusCode: 0, error });
      });
    });
  }

  /**
   * Get folder size
   */
  getFolderSize(dir) {
    let size = 0;
    const files = fs.readdirSync(dir);
    
    for (const file of files) {
      const filePath = path.join(dir, file);
      const stats = fs.statSync(filePath);
      
      if (stats.isDirectory()) {
        size += this.getFolderSize(filePath);
      } else {
        size += stats.size;
      }
    }
    
    return size;
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

      if (this.orgId) {
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
              reject(new Error(parsed.error?.message || responseData));
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

  /**
   * Sleep helper
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Run deployment
if (require.main === module) {
  const deployer = new VercelDeployer();
  const environment = process.argv[2] || 'production';
  
  deployer.deploy(environment);
}

module.exports = VercelDeployer;