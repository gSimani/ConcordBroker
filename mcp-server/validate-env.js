/**
 * Environment Variable Security Validator
 * Ensures all sensitive data is properly configured and secure
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

class EnvValidator {
  constructor() {
    this.errors = [];
    this.warnings = [];
    this.sensitivePatterns = [
      { name: 'API Key', pattern: /api[_-]?key/i },
      { name: 'Secret', pattern: /secret/i },
      { name: 'Token', pattern: /token/i },
      { name: 'Password', pattern: /pass(word)?/i },
      { name: 'Private Key', pattern: /private[_-]?key/i },
      { name: 'Database URL', pattern: /(database|db)[_-]?url/i },
      { name: 'Connection String', pattern: /conn(ection)?[_-]?str(ing)?/i }
    ];
  }

  /**
   * Validate all environment files
   */
  async validateAll() {
    console.log('🔐 Environment Security Validator\n');
    console.log('═══════════════════════════════════════\n');

    // Find all .env files
    const envFiles = this.findEnvFiles();
    
    console.log(`Found ${envFiles.length} environment files to check:\n`);

    for (const file of envFiles) {
      await this.validateFile(file);
    }

    this.printReport();
  }

  /**
   * Find all .env files in the project
   */
  findEnvFiles() {
    const files = [];
    const rootDir = path.join(__dirname, '..');
    
    function searchDir(dir) {
      if (dir.includes('node_modules') || dir.includes('.git')) return;
      
      try {
        const items = fs.readdirSync(dir);
        for (const item of items) {
          const fullPath = path.join(dir, item);
          const stat = fs.statSync(fullPath);
          
          if (stat.isDirectory()) {
            searchDir(fullPath);
          } else if (item.startsWith('.env')) {
            files.push(fullPath);
          }
        }
      } catch (error) {
        // Skip directories we can't read
      }
    }
    
    searchDir(rootDir);
    return files;
  }

  /**
   * Validate a single environment file
   */
  async validateFile(filePath) {
    const fileName = path.basename(filePath);
    const relPath = path.relative(path.join(__dirname, '..'), filePath);
    
    console.log(`📄 Checking: ${relPath}`);

    // Check if it's an example file
    if (fileName.includes('example') || fileName.includes('template')) {
      console.log('   ✓ Template file (skipping sensitive data check)\n');
      return;
    }

    // Check if file should be in .gitignore
    await this.checkGitIgnore(filePath);

    // Read and parse the file
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      const lines = content.split('\n');
      
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (line && !line.startsWith('#')) {
          await this.validateLine(line, i + 1, filePath);
        }
      }
    } catch (error) {
      this.errors.push(`Cannot read file: ${relPath}`);
    }

    console.log('');
  }

  /**
   * Validate a single line from an env file
   */
  async validateLine(line, lineNumber, filePath) {
    const [key, ...valueParts] = line.split('=');
    const value = valueParts.join('=');
    
    if (!key || !value) return;

    // Check for sensitive keys
    const isSensitive = this.sensitivePatterns.some(p => p.pattern.test(key));
    
    if (isSensitive) {
      // Check value security
      this.checkValueSecurity(key.trim(), value.trim(), lineNumber, filePath);
    }

    // Check for common issues
    this.checkCommonIssues(key.trim(), value.trim(), lineNumber, filePath);
  }

  /**
   * Check if value is secure
   */
  checkValueSecurity(key, value, lineNumber, filePath) {
    const fileName = path.basename(filePath);
    
    // Remove quotes if present
    const cleanValue = value.replace(/^["']|["']$/g, '');
    
    // Check for placeholder values
    if (cleanValue === 'your-api-key-here' || 
        cleanValue === 'xxx' || 
        cleanValue === 'TODO' ||
        cleanValue.includes('your-') ||
        cleanValue.includes('example')) {
      this.warnings.push(`${fileName}:${lineNumber} - ${key} contains placeholder value`);
    }

    // Check for exposed tokens in non-example files
    if (!fileName.includes('example')) {
      // Check if it looks like a real token/key
      if (this.looksLikeRealToken(cleanValue)) {
        console.log(`   ⚠️  Line ${lineNumber}: ${key} contains what appears to be a real token`);
        
        // Check entropy (randomness) of the value
        const entropy = this.calculateEntropy(cleanValue);
        if (entropy > 4.5) {
          console.log(`      High entropy detected (${entropy.toFixed(2)}) - likely a real secret`);
        }
      }
    }

    // Check for common weak patterns
    if (key.toLowerCase().includes('password')) {
      if (cleanValue.length < 12) {
        this.warnings.push(`${fileName}:${lineNumber} - Password is too short (< 12 chars)`);
      }
      if (!/[A-Z]/.test(cleanValue) || !/[a-z]/.test(cleanValue) || !/[0-9]/.test(cleanValue)) {
        this.warnings.push(`${fileName}:${lineNumber} - Password lacks complexity`);
      }
    }
  }

  /**
   * Check for common configuration issues
   */
  checkCommonIssues(key, value, lineNumber, filePath) {
    const fileName = path.basename(filePath);
    const cleanValue = value.replace(/^["']|["']$/g, '');
    
    // Check for localhost in production files
    if (fileName.includes('production') && cleanValue.includes('localhost')) {
      this.errors.push(`${fileName}:${lineNumber} - ${key} contains localhost in production file`);
    }

    // Check for http instead of https in production
    if (fileName.includes('production') && cleanValue.startsWith('http://') && !cleanValue.includes('localhost')) {
      this.warnings.push(`${fileName}:${lineNumber} - ${key} uses HTTP instead of HTTPS`);
    }

    // Check for trailing whitespace
    if (value !== value.trim()) {
      this.warnings.push(`${fileName}:${lineNumber} - ${key} has trailing whitespace`);
    }

    // Check for empty values
    if (!cleanValue) {
      this.warnings.push(`${fileName}:${lineNumber} - ${key} is empty`);
    }
  }

  /**
   * Check if file is in .gitignore
   */
  async checkGitIgnore(filePath) {
    const fileName = path.basename(filePath);
    const relPath = path.relative(path.join(__dirname, '..'), filePath);
    
    // Skip example files
    if (fileName.includes('example') || fileName.includes('template')) {
      return;
    }

    // Check if file is tracked in git
    try {
      const { execSync } = require('child_process');
      execSync(`git ls-files --error-unmatch "${relPath.replace(/\\/g, '/')}"`, {
        cwd: path.join(__dirname, '..'),
        stdio: 'pipe'
      });
      
      // File is tracked - this is bad for non-example env files
      this.errors.push(`CRITICAL: ${relPath} is tracked in Git!`);
      console.log(`   ❌ CRITICAL: File is tracked in Git repository!`);
    } catch (error) {
      // File is not tracked - this is good
      console.log(`   ✓ Not tracked in Git`);
    }
  }

  /**
   * Check if a value looks like a real token
   */
  looksLikeRealToken(value) {
    // Common token patterns
    const patterns = [
      /^sk-[a-zA-Z0-9]{48}$/,  // OpenAI
      /^ghp_[a-zA-Z0-9]{36}$/,  // GitHub
      /^[a-f0-9]{64}$/,         // SHA-256 hash
      /^[A-Za-z0-9+/]{40,}={0,2}$/, // Base64
      /^Bearer\s+[A-Za-z0-9\-._~+/]+$/, // Bearer token
    ];
    
    return patterns.some(pattern => pattern.test(value)) || 
           (value.length > 20 && /^[a-zA-Z0-9\-._~]+$/.test(value));
  }

  /**
   * Calculate Shannon entropy of a string
   */
  calculateEntropy(str) {
    const frequencies = {};
    for (const char of str) {
      frequencies[char] = (frequencies[char] || 0) + 1;
    }
    
    let entropy = 0;
    for (const char in frequencies) {
      const p = frequencies[char] / str.length;
      entropy -= p * Math.log2(p);
    }
    
    return entropy;
  }

  /**
   * Print validation report
   */
  printReport() {
    console.log('═══════════════════════════════════════\n');
    console.log('📊 Validation Report\n');
    
    if (this.errors.length === 0 && this.warnings.length === 0) {
      console.log('✅ All environment files passed security checks!\n');
    } else {
      if (this.errors.length > 0) {
        console.log(`❌ Errors (${this.errors.length}):`);
        this.errors.forEach(error => console.log(`   - ${error}`));
        console.log('');
      }
      
      if (this.warnings.length > 0) {
        console.log(`⚠️  Warnings (${this.warnings.length}):`);
        this.warnings.forEach(warning => console.log(`   - ${warning}`));
        console.log('');
      }
    }

    console.log('📝 Recommendations:');
    console.log('   1. Never commit .env files to Git');
    console.log('   2. Use strong, unique passwords and tokens');
    console.log('   3. Rotate secrets regularly');
    console.log('   4. Use environment-specific configurations');
    console.log('   5. Enable 2FA on all service accounts');
    console.log('   6. Use secret management services in production');
    
    // Exit with error code if critical issues found
    if (this.errors.length > 0) {
      process.exit(1);
    }
  }
}

// Run validator
if (require.main === module) {
  const validator = new EnvValidator();
  validator.validateAll().catch(console.error);
}

module.exports = EnvValidator;