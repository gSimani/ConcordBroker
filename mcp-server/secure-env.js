/**
 * Environment Security Helper
 * Helps generate secure tokens and manage secrets
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

class EnvSecurityHelper {
  constructor() {
    this.rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
  }

  /**
   * Main menu
   */
  async run() {
    console.log('\n🔐 ConcordBroker Environment Security Helper\n');
    console.log('═══════════════════════════════════════════\n');
    
    const choice = await this.prompt(
      'What would you like to do?\n' +
      '1. Generate secure tokens\n' +
      '2. Check .env file security\n' +
      '3. Create secure .env from template\n' +
      '4. Rotate secrets in Vercel\n' +
      '5. Exit\n\n' +
      'Choice (1-5): '
    );

    switch (choice) {
      case '1':
        await this.generateTokens();
        break;
      case '2':
        await this.checkEnvSecurity();
        break;
      case '3':
        await this.createSecureEnv();
        break;
      case '4':
        await this.rotateVercelSecrets();
        break;
      case '5':
        console.log('\nGoodbye! Stay secure! 🔒\n');
        process.exit(0);
      default:
        console.log('\nInvalid choice. Please try again.');
        await this.run();
    }

    // Ask if user wants to continue
    const again = await this.prompt('\nWould you like to do something else? (y/n): ');
    if (again.toLowerCase() === 'y') {
      await this.run();
    } else {
      console.log('\nGoodbye! Stay secure! 🔒\n');
      process.exit(0);
    }
  }

  /**
   * Generate secure tokens
   */
  async generateTokens() {
    console.log('\n🎲 Generating Secure Tokens\n');
    
    const tokens = {
      'JWT_SECRET (64 chars)': this.generateToken(64),
      'SESSION_SECRET (32 chars)': this.generateToken(32),
      'API_KEY (32 chars)': this.generateToken(32),
      'DATABASE_PASSWORD (24 chars)': this.generatePassword(24),
      'ADMIN_PASSWORD (20 chars)': this.generatePassword(20)
    };

    console.log('Here are your secure tokens:\n');
    for (const [name, value] of Object.entries(tokens)) {
      console.log(`${name}:`);
      console.log(`  ${value}`);
      console.log('');
    }

    console.log('⚠️  IMPORTANT: Copy these values immediately.');
    console.log('    They will not be shown again!\n');
  }

  /**
   * Generate a secure token
   */
  generateToken(length = 32) {
    return crypto.randomBytes(length).toString('hex').slice(0, length);
  }

  /**
   * Generate a secure password
   */
  generatePassword(length = 20) {
    const charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{}|;:,.<>?';
    let password = '';
    
    // Ensure at least one of each type
    password += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[Math.floor(Math.random() * 26)];
    password += 'abcdefghijklmnopqrstuvwxyz'[Math.floor(Math.random() * 26)];
    password += '0123456789'[Math.floor(Math.random() * 10)];
    password += '!@#$%^&*()_+-='[Math.floor(Math.random() * 14)];
    
    // Fill the rest randomly
    for (let i = password.length; i < length; i++) {
      password += charset[Math.floor(Math.random() * charset.length)];
    }
    
    // Shuffle the password
    return password.split('').sort(() => 0.5 - Math.random()).join('');
  }

  /**
   * Check .env file security
   */
  async checkEnvSecurity() {
    console.log('\n🔍 Checking .env File Security\n');
    
    const envPath = path.join(__dirname, '..', '.env');
    
    if (!fs.existsSync(envPath)) {
      console.log('❌ No .env file found in project root.\n');
      return;
    }

    // Check file permissions (Windows doesn't have Unix permissions)
    const stats = fs.statSync(envPath);
    console.log('File Information:');
    console.log(`  Created: ${stats.birthtime.toLocaleDateString()}`);
    console.log(`  Modified: ${stats.mtime.toLocaleDateString()}`);
    console.log(`  Size: ${stats.size} bytes`);
    
    // Check if in .gitignore
    const gitignorePath = path.join(__dirname, '..', '.gitignore');
    if (fs.existsSync(gitignorePath)) {
      const gitignore = fs.readFileSync(gitignorePath, 'utf8');
      if (gitignore.includes('.env')) {
        console.log('  ✅ File is in .gitignore');
      } else {
        console.log('  ❌ File is NOT in .gitignore - HIGH RISK!');
      }
    }

    // Check for weak values
    const content = fs.readFileSync(envPath, 'utf8');
    const lines = content.split('\n');
    let weakValues = 0;
    
    for (const line of lines) {
      if (line.includes('=')) {
        const [key, value] = line.split('=');
        if (value && (
          value.includes('password') ||
          value.includes('123456') ||
          value.includes('admin') ||
          value.includes('test') ||
          value.includes('demo') ||
          value.includes('example') ||
          value.length < 8
        )) {
          weakValues++;
        }
      }
    }

    if (weakValues > 0) {
      console.log(`  ⚠️  Found ${weakValues} potentially weak values`);
    } else {
      console.log('  ✅ No obviously weak values detected');
    }

    console.log('\n');
  }

  /**
   * Create secure .env from template
   */
  async createSecureEnv() {
    console.log('\n📝 Creating Secure .env File\n');
    
    const templatePath = path.join(__dirname, '..', '.env.example.secure');
    const envPath = path.join(__dirname, '..', '.env.generated');
    
    if (!fs.existsSync(templatePath)) {
      console.log('❌ Template file .env.example.secure not found.\n');
      return;
    }

    console.log('This will create a new .env.generated file with secure random values.\n');
    
    const proceed = await this.prompt('Continue? (y/n): ');
    if (proceed.toLowerCase() !== 'y') {
      return;
    }

    let content = fs.readFileSync(templatePath, 'utf8');
    
    // Replace placeholder values with secure ones
    const replacements = {
      'generate-a-secure-64-character-random-string-here': this.generateToken(64),
      'generate-another-secure-random-string-here': this.generateToken(32),
      'your-secure-password-here': this.generatePassword(20),
      'your-postgres-user': 'postgres_' + this.generateToken(8),
      'your-supabase-jwt-secret-here': this.generateToken(64),
      'your-vercel-api-token-here': 't9AK4qQ51TyAc0K0ZLk7tN0H', // Keep actual token
      'prj_your-project-id': 'prj_l6jgk7483iwPCcaYarq7sMgt2m7L', // Keep actual ID
      'team_your-org-id': 'team_OIAQ7q0bQTblRPZrnKhU4BGF' // Keep actual ID
    };

    for (const [placeholder, value] of Object.entries(replacements)) {
      content = content.replace(new RegExp(placeholder, 'g'), value);
    }

    fs.writeFileSync(envPath, content);
    console.log('\n✅ Created .env.generated with secure values.');
    console.log('   Review and rename to .env when ready.\n');
  }

  /**
   * Rotate Vercel secrets
   */
  async rotateVercelSecrets() {
    console.log('\n🔄 Rotating Vercel Secrets\n');
    console.log('This will generate new values for sensitive environment variables.\n');
    
    const secrets = [
      { key: 'JWT_SECRET', value: this.generateToken(64) },
      { key: 'SESSION_SECRET', value: this.generateToken(32) },
      { key: 'SUPABASE_JWT_SECRET', value: this.generateToken(64) }
    ];

    console.log('New secret values generated:\n');
    for (const secret of secrets) {
      console.log(`${secret.key}: ${secret.value.substring(0, 10)}...`);
    }

    console.log('\nTo update in Vercel:');
    console.log('1. Go to: https://vercel.com/westbocaexecs-projects/concord-broker/settings/environment-variables');
    console.log('2. Update each secret with the new values');
    console.log('3. Redeploy your application\n');
    
    const save = await this.prompt('Save these values to secrets.txt? (y/n): ');
    if (save.toLowerCase() === 'y') {
      const content = secrets.map(s => `${s.key}=${s.value}`).join('\n');
      fs.writeFileSync('secrets.txt', content);
      console.log('\n✅ Saved to secrets.txt - DELETE THIS FILE after updating Vercel!\n');
    }
  }

  /**
   * Prompt helper
   */
  prompt(question) {
    return new Promise(resolve => {
      this.rl.question(question, answer => {
        resolve(answer);
      });
    });
  }
}

// Run the helper
if (require.main === module) {
  const helper = new EnvSecurityHelper();
  helper.run().catch(console.error);
}

module.exports = EnvSecurityHelper;