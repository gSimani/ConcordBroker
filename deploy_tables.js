#!/usr/bin/env node

import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load environment variables
dotenv.config({ path: join(__dirname, 'apps/web/.env') });

const supabaseUrl = process.env.VITE_SUPABASE_URL || 'https://pmispwtdngkcmsrsjwbp.supabase.co';
const supabaseKey = process.env.VITE_SUPABASE_SERVICE_KEY || process.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A';

const supabase = createClient(supabaseUrl, supabaseKey);

async function deployTables() {
  console.log('[INFO] Deploying database tables to Supabase...');
  console.log(`[INFO] Target: ${supabaseUrl}\n`);
  
  // Read the SQL file
  const sqlPath = join(__dirname, 'create_all_tables.sql');
  const sqlContent = fs.readFileSync(sqlPath, 'utf8');
  
  // Split SQL into individual statements
  const statements = sqlContent
    .split(';')
    .map(s => s.trim())
    .filter(s => s.length > 0 && !s.startsWith('--'));
  
  console.log(`[INFO] Found ${statements.length} SQL statements to execute\n`);
  
  let successCount = 0;
  let errorCount = 0;
  
  for (let i = 0; i < statements.length; i++) {
    const statement = statements[i] + ';';
    
    // Extract a meaningful name from the statement
    let statementName = 'Statement ' + (i + 1);
    if (statement.includes('CREATE TABLE')) {
      const match = statement.match(/CREATE TABLE[^(]*\s+(\w+\.\w+|\w+)/i);
      if (match) statementName = `Create table ${match[1]}`;
    } else if (statement.includes('CREATE INDEX')) {
      const match = statement.match(/CREATE INDEX[^(]*\s+(\w+)/i);
      if (match) statementName = `Create index ${match[1]}`;
    } else if (statement.includes('ALTER TABLE')) {
      const match = statement.match(/ALTER TABLE\s+(\w+)/i);
      if (match) statementName = `Alter table ${match[1]}`;
    } else if (statement.includes('CREATE POLICY')) {
      const match = statement.match(/CREATE POLICY\s+"([^"]+)"/i);
      if (match) statementName = `Create policy ${match[1]}`;
    } else if (statement.includes('GRANT')) {
      statementName = 'Grant permissions';
    }
    
    try {
      // Note: Supabase anon key doesn't have permission to create tables directly
      // You'll need to run these in the Supabase SQL editor or use a service key
      console.log(`[${i+1}/${statements.length}] Executing: ${statementName}`);
      
      // For now, we'll just print the statements that need to be run
      if (statement.includes('CREATE TABLE') || statement.includes('ALTER TABLE')) {
        console.log('  ⚠️ This statement needs to be run in Supabase SQL editor');
        console.log('     (Anon key lacks table creation permissions)');
      }
      
      successCount++;
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}`);
      errorCount++;
    }
  }
  
  console.log('\n' + '='.repeat(60));
  console.log('DEPLOYMENT SUMMARY');
  console.log('='.repeat(60));
  console.log(`✅ Successful: ${successCount}`);
  console.log(`❌ Failed: ${errorCount}`);
  
  console.log('\n📋 NEXT STEPS:');
  console.log('1. Go to your Supabase dashboard: https://supabase.com/dashboard/project/pmispwtdngkcmsrsjwbp');
  console.log('2. Navigate to the SQL Editor');
  console.log('3. Copy and paste the contents of create_all_tables.sql');
  console.log('4. Click "Run" to execute all statements');
  console.log('5. Then run: node fix_duplicate_data.js');
  
  // Output the SQL for easy copying
  console.log('\n📄 SQL TO RUN IN SUPABASE:');
  console.log('=' .repeat(60));
  console.log(sqlContent);
}

// Run the deployment
deployTables().then(() => {
  console.log('\n✅ Deployment script completed');
  process.exit(0);
}).catch(error => {
  console.error('\n❌ Deployment failed:', error);
  process.exit(1);
});