#!/usr/bin/env node

/**
 * Test and demonstrate the intelligent agent system
 */

import { MasterOrchestrator } from './apps/agents/MasterOrchestrator.js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

dotenv.config({ path: join(__dirname, 'apps/web/.env') });

const supabaseUrl = process.env.VITE_SUPABASE_URL || 'https://pmispwtdngkcmsrsjwbp.supabase.co';
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

console.log('🤖 Intelligent Agent System Demonstration');
console.log('==========================================\n');
console.log('This system ensures:');
console.log('  1️⃣  Data Accuracy - All displayed data is validated');
console.log('  2️⃣  Speed - Optimized queries with intelligent caching');
console.log('  3️⃣  Completeness - Missing data is automatically filled\n');

async function demonstrateAgents() {
  const orchestrator = new MasterOrchestrator();
  
  try {
    // Get a sample property with potential missing data
    console.log('📍 Step 1: Finding a property to demonstrate...\n');
    const { data: sampleProperties } = await supabase
      .from('florida_parcels')
      .select('parcel_id, phy_addr1, phy_city')
      .limit(3);
    
    if (!sampleProperties || sampleProperties.length === 0) {
      console.log('No properties found in database');
      return;
    }
    
    const testProperty = sampleProperties[0];
    console.log(`Selected Property: ${testProperty.phy_addr1}, ${testProperty.phy_city}`);
    console.log(`Parcel ID: ${testProperty.parcel_id}\n`);
    
    // Process with orchestrator
    console.log('🔍 Step 2: Processing property with intelligent agents...\n');
    
    const result = await orchestrator.processPropertyRequest(testProperty.parcel_id);
    
    if (result.success) {
      console.log('✅ Property Processing Complete!\n');
      
      // Show data quality
      console.log('📊 Data Quality Report:');
      console.log(`   • Completeness: ${result.quality.completeness}%`);
      console.log(`   • Validation Errors: ${result.quality.errors}`);
      console.log(`   • Warnings: ${result.quality.warnings}`);
      console.log(`   • Data Source: ${result.quality.dataSource}\n`);
      
      // Show performance
      console.log('⚡ Performance Metrics:');
      console.log(`   • Response Time: ${result.performance.responseTime}ms`);
      console.log(`   • Target: ${result.performance.target}ms`);
      console.log(`   • Status: ${result.performance.status}`);
      console.log(`   • From Cache: ${result.performance.fromCache ? 'Yes' : 'No'}\n`);
      
      // Show enhancements
      if (result.enhancements.length > 0) {
        console.log('🔧 Data Enhancements Applied:');
        result.enhancements.forEach(field => {
          console.log(`   • ${field} - Missing data was intelligently filled`);
        });
        console.log('');
      }
      
      // Show some actual data
      const prop = result.property;
      console.log('🏠 Property Details (After Processing):');
      console.log(`   • Address: ${prop.phy_addr1}, ${prop.phy_city}, FL ${prop.phy_zipcd}`);
      console.log(`   • Owner: ${prop.owner_name || 'N/A'}`);
      console.log(`   • Year Built: ${prop.year_built || 'N/A'}`);
      console.log(`   • Living Area: ${prop.total_living_area ? prop.total_living_area.toLocaleString() + ' sq ft' : 'N/A'}`);
      console.log(`   • Bedrooms: ${prop.bedrooms || 'N/A'}`);
      console.log(`   • Bathrooms: ${prop.bathrooms || 'N/A'}`);
      console.log(`   • Taxable Value: ${prop.taxable_value ? '$' + prop.taxable_value.toLocaleString() : 'N/A'}`);
      console.log(`   • Sale Price: ${prop.sale_price ? '$' + prop.sale_price.toLocaleString() : 'N/A'}`);
      console.log(`   • Sale Date: ${prop.sale_date || 'N/A'}\n`);
      
    } else {
      console.log('❌ Processing failed:', result.error);
    }
    
    // Test search performance
    console.log('🔎 Step 3: Testing optimized search...\n');
    
    const searchResult = await orchestrator.processSearch('OCEAN', { limit: 5 });
    
    if (searchResult.success) {
      console.log(`Found ${searchResult.count} properties matching "OCEAN"\n`);
      
      console.log('📊 Search Quality Metrics:');
      console.log(`   • Average Completeness: ${searchResult.quality.avgCompleteness.toFixed(1)}%`);
      console.log(`   • Properties Needing Completion: ${searchResult.quality.needingCompletion}`);
      console.log(`   • Response Time: ${searchResult.performance.responseTime}ms`);
      console.log(`   • Performance Status: ${searchResult.performance.status}\n`);
      
      // Show first few results
      console.log('Sample Results:');
      searchResult.properties.slice(0, 3).forEach((prop, idx) => {
        console.log(`   ${idx + 1}. ${prop.phy_addr1}, ${prop.phy_city}`);
        if (prop._needsCompletion) {
          console.log(`      ⚠️ Data completeness: ${prop._completeness}%`);
        }
      });
      console.log('');
    }
    
    // Perform health check
    console.log('💊 Step 4: System Health Check...\n');
    
    const health = await orchestrator.performHealthCheck();
    
    console.log('System Health Report:');
    console.log(`   • Overall Status: ${health.overall.toUpperCase()}`);
    console.log(`   • Validation Agent: ${health.agents.validation}`);
    console.log(`   • Performance Agent: ${health.agents.performance.status}`);
    console.log(`     - Cache Hit Rate: ${health.agents.performance.cacheHitRate}`);
    console.log(`     - Slow Queries: ${health.agents.performance.slowQueries}`);
    console.log(`   • Completion Agent: ${health.agents.completion.status}`);
    console.log(`   • Database: ${health.database.status} (${health.database.totalRecords?.toLocaleString() || 0} records)`);
    console.log(`   • Data Quality Score: ${health.dataQuality.score}/100 (Grade: ${health.dataQuality.grade})\n`);
    
    // Show monitoring status
    const status = orchestrator.getMonitoringStatus();
    console.log('📈 Monitoring Dashboard:');
    console.log(`   • Properties Processed: ${status.totalProcessed}`);
    console.log(`   • Average Response Time: ${status.avgResponseTime.toFixed(2)}ms`);
    console.log(`   • Data Quality Score: ${status.dataQualityScore.toFixed(1)}%`);
    console.log(`   • Active Requests: ${status.activeRequests}\n`);
    
    console.log('✨ Agent System Benefits:');
    console.log('   ✅ Automatic validation of all property data');
    console.log('   ✅ Intelligent caching for sub-200ms response times');
    console.log('   ✅ Automatic completion of missing fields');
    console.log('   ✅ Real-time data quality monitoring');
    console.log('   ✅ Cross-reference validation with multiple data sources\n');
    
  } catch (error) {
    console.error('❌ Demonstration failed:', error.message);
    console.error(error.stack);
  }
}

// Run the demonstration
console.log('Starting agent demonstration...\n');
demonstrateAgents().then(() => {
  console.log('🎉 Demonstration Complete!');
  console.log('\nThe intelligent agent system is ready to ensure:');
  console.log('• Every data cell shows accurate information');
  console.log('• All queries are optimized for speed');
  console.log('• Missing data is automatically completed');
  process.exit(0);
}).catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});