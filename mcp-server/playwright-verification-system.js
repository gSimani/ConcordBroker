/**
 * Playwright MCP Verification System
 * Automated testing and verification of work
 */

const { chromium } = require('playwright');
const fs = require('fs').promises;
const path = require('path');

class PlaywrightVerificationSystem {
  constructor() {
    this.browser = null;
    this.context = null;
    this.verificationHistory = [];
    this.screenshotsPath = path.join(__dirname, '../.memory/screenshots');
  }

  async initialize() {
    console.log('🎭 Initializing Playwright Verification System...');

    try {
      await fs.mkdir(this.screenshotsPath, { recursive: true });
    } catch (error) {
      // Directory exists
    }

    console.log('✅ Playwright Verification System ready');
  }

  async startBrowser() {
    if (!this.browser) {
      this.browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
      });
      this.context = await this.browser.newContext();
    }
  }

  async closeBrowser() {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
      this.context = null;
    }
  }

  async verifyFrontend(url = 'http://localhost:5191') {
    console.log(`🔍 Verifying frontend at ${url}...`);

    await this.startBrowser();
    const page = await this.context.newPage();

    const verification = {
      type: 'frontend',
      timestamp: new Date().toISOString(),
      url,
      checks: {}
    };

    try {
      // Check if page loads
      const response = await page.goto(url, { timeout: 30000 });
      verification.checks.loads = response.status() === 200;

      // Check for console errors
      const consoleErrors = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          consoleErrors.push(msg.text());
        }
      });

      await page.waitForTimeout(2000);
      verification.checks.noConsoleErrors = consoleErrors.length === 0;
      verification.checks.consoleErrors = consoleErrors;

      // Check if React hydrated
      const hasReactRoot = await page.evaluate(() => {
        return document.querySelector('#root') !== null;
      });
      verification.checks.reactRoot = hasReactRoot;

      // Take screenshot
      const screenshotName = `frontend-${Date.now()}.png`;
      await page.screenshot({
        path: path.join(this.screenshotsPath, screenshotName)
      });
      verification.screenshot = screenshotName;

      // Check for specific elements
      const propertySearchExists = await page.$('input[placeholder*="Search" i], input[type="search"]');
      verification.checks.searchBarExists = propertySearchExists !== null;

      verification.passed = verification.checks.loads &&
                           verification.checks.noConsoleErrors &&
                           verification.checks.reactRoot;

      console.log(`✅ Frontend verification: ${verification.passed ? 'PASSED' : 'FAILED'}`);

    } catch (error) {
      verification.passed = false;
      verification.error = error.message;
      console.log(`❌ Frontend verification failed: ${error.message}`);
    } finally {
      await page.close();
    }

    this.verificationHistory.push(verification);
    return verification;
  }

  async verifyMCPServer(url = 'http://localhost:3001') {
    console.log(`🔍 Verifying MCP Server at ${url}...`);

    await this.startBrowser();
    const page = await this.context.newPage();

    const verification = {
      type: 'mcp-server',
      timestamp: new Date().toISOString(),
      url,
      checks: {}
    };

    try {
      // Check health endpoint
      const healthResponse = await page.goto(`${url}/health`, { timeout: 10000 });
      verification.checks.healthEndpoint = healthResponse.status() === 200;

      const healthData = await healthResponse.json();
      verification.checks.healthData = healthData;

      // Check services status
      if (healthData && healthData.services) {
        const services = healthData.services;
        verification.checks.servicesHealthy = Object.values(services).filter(
          s => s.status === 'healthy' || s.status === 'configured'
        ).length;
        verification.checks.totalServices = Object.keys(services).length;
      }

      // Check docs endpoint
      const docsResponse = await page.goto(`${url}/docs`, { timeout: 10000 });
      verification.checks.docsEndpoint = docsResponse.status() === 200;

      verification.passed = verification.checks.healthEndpoint &&
                           verification.checks.docsEndpoint &&
                           verification.checks.servicesHealthy > 0;

      console.log(`✅ MCP Server verification: ${verification.passed ? 'PASSED' : 'FAILED'}`);

    } catch (error) {
      verification.passed = false;
      verification.error = error.message;
      console.log(`❌ MCP Server verification failed: ${error.message}`);
    } finally {
      await page.close();
    }

    this.verificationHistory.push(verification);
    return verification;
  }

  async verifyPropertySearch() {
    console.log('🔍 Verifying property search functionality...');

    await this.startBrowser();
    const page = await this.context.newPage();

    const verification = {
      type: 'property-search',
      timestamp: new Date().toISOString(),
      checks: {}
    };

    try {
      await page.goto('http://localhost:5191', { timeout: 30000 });

      // Find search input
      const searchInput = await page.$('input[type="search"], input[placeholder*="Search" i]');
      verification.checks.searchInputFound = searchInput !== null;

      if (searchInput) {
        // Type a search query
        await searchInput.type('BROWARD');
        await page.waitForTimeout(1000);

        // Check if results appear
        const resultsExist = await page.$$eval(
          '[data-testid*="property"], .property-card, [class*="property"]',
          elements => elements.length > 0
        );
        verification.checks.resultsAppear = resultsExist;

        // Take screenshot
        const screenshotName = `property-search-${Date.now()}.png`;
        await page.screenshot({
          path: path.join(this.screenshotsPath, screenshotName)
        });
        verification.screenshot = screenshotName;
      }

      verification.passed = verification.checks.searchInputFound &&
                           verification.checks.resultsAppear;

      console.log(`✅ Property search verification: ${verification.passed ? 'PASSED' : 'FAILED'}`);

    } catch (error) {
      verification.passed = false;
      verification.error = error.message;
      console.log(`❌ Property search verification failed: ${error.message}`);
    } finally {
      await page.close();
    }

    this.verificationHistory.push(verification);
    return verification;
  }

  async runAllVerifications() {
    console.log('🎯 Running all verifications...');

    const results = {
      timestamp: new Date().toISOString(),
      verifications: {}
    };

    results.verifications.mcpServer = await this.verifyMCPServer();
    results.verifications.frontend = await this.verifyFrontend();
    results.verifications.propertySearch = await this.verifyPropertySearch();

    results.passed = Object.values(results.verifications).every(v => v.passed);
    results.passedCount = Object.values(results.verifications).filter(v => v.passed).length;
    results.totalCount = Object.values(results.verifications).length;

    console.log(`\n📊 Verification Summary:`);
    console.log(`   Passed: ${results.passedCount}/${results.totalCount}`);
    console.log(`   Overall: ${results.passed ? '✅ PASSED' : '❌ FAILED'}\n`);

    await this.closeBrowser();
    return results;
  }

  getVerificationHistory(count = 10) {
    return this.verificationHistory.slice(-count);
  }

  async shutdown() {
    await this.closeBrowser();
  }
}

module.exports = PlaywrightVerificationSystem;
