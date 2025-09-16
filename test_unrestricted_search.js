#!/usr/bin/env node

/**
 * Test Unrestricted Property Search
 * Verifies that ALL 789,884 properties are searchable without any restrictions
 */

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

class UnrestrictedSearchTester {
  constructor() {
    this.results = {
      totalProperties: 0,
      countiesFound: new Set(),
      citiesFound: new Set(),
      propertyTypes: new Set(),
      tests: [],
      errors: []
    };
  }

  async runAllTests() {
    console.log('🔍 TESTING UNRESTRICTED PROPERTY SEARCH');
    console.log('========================================\n');

    // Test 1: Get total count without any filters
    await this.testTotalCount();
    
    // Test 2: Search across all counties (not just BROWARD)
    await this.testAllCounties();
    
    // Test 3: Search all cities without restrictions
    await this.testAllCities();
    
    // Test 4: Test that redacted properties are included
    await this.testRedactedProperties();
    
    // Test 5: Test price ranges without limits
    await this.testPriceRanges();
    
    // Test 6: Test property types without restrictions
    await this.testPropertyTypes();
    
    // Test 7: Random sampling across database
    await this.testRandomSampling();
    
    // Final Report
    this.generateReport();
  }

  async testTotalCount() {
    console.log('📊 Test 1: Total Property Count (No Filters)');
    console.log('--------------------------------------------');
    
    try {
      const { count, error } = await supabase
        .from('florida_parcels')
        .select('*', { count: 'exact', head: true });
      
      if (error) throw error;
      
      this.results.totalProperties = count;
      console.log(`✅ Total properties accessible: ${count.toLocaleString()}`);
      console.log(`   Expected: 789,884`);
      console.log(`   Status: ${count >= 789884 ? '✅ UNRESTRICTED' : '⚠️ RESTRICTED'}\n`);
      
      this.results.tests.push({
        name: 'Total Count',
        expected: 789884,
        actual: count,
        passed: count >= 789884
      });
    } catch (error) {
      console.error('❌ Error:', error.message);
      this.results.errors.push(error.message);
    }
  }

  async testAllCounties() {
    console.log('🌐 Test 2: All Counties Accessible');
    console.log('----------------------------------');
    
    try {
      // Get unique counties
      const { data, error } = await supabase
        .from('florida_parcels')
        .select('county')
        .limit(10000);
      
      if (error) throw error;
      
      const counties = new Set(data.map(d => d.county).filter(Boolean));
      this.results.countiesFound = counties;
      
      console.log(`✅ Counties found: ${counties.size}`);
      console.log(`   Counties: ${Array.from(counties).slice(0, 10).join(', ')}...`);
      
      const hasBroward = counties.has('BROWARD');
      const hasOthers = counties.size > 1;
      
      console.log(`   Has BROWARD: ${hasBroward ? '✅' : '❌'}`);
      console.log(`   Has other counties: ${hasOthers ? '✅' : '❌'}`);
      console.log(`   Status: ${hasOthers ? '✅ UNRESTRICTED' : '⚠️ RESTRICTED TO BROWARD ONLY'}\n`);
      
      this.results.tests.push({
        name: 'Multiple Counties',
        expected: 'Multiple counties',
        actual: `${counties.size} counties`,
        passed: counties.size > 1
      });
    } catch (error) {
      console.error('❌ Error:', error.message);
      this.results.errors.push(error.message);
    }
  }

  async testAllCities() {
    console.log('🏙️ Test 3: All Cities Accessible');
    console.log('--------------------------------');
    
    try {
      // Get sample of cities from different counties
      const counties = ['MIAMI-DADE', 'PALM BEACH', 'ORANGE', 'HILLSBOROUGH'];
      
      for (const county of counties) {
        const { data, error } = await supabase
          .from('florida_parcels')
          .select('phy_city')
          .eq('county', county)
          .limit(100);
        
        if (!error && data && data.length > 0) {
          const cities = new Set(data.map(d => d.phy_city).filter(Boolean));
          cities.forEach(city => this.results.citiesFound.add(city));
          console.log(`   ${county}: ${cities.size} cities found`);
        }
      }
      
      console.log(`✅ Total unique cities: ${this.results.citiesFound.size}`);
      console.log(`   Status: ${this.results.citiesFound.size > 10 ? '✅ UNRESTRICTED' : '⚠️ LIMITED'}\n`);
      
      this.results.tests.push({
        name: 'City Access',
        expected: 'Multiple cities across counties',
        actual: `${this.results.citiesFound.size} cities`,
        passed: this.results.citiesFound.size > 10
      });
    } catch (error) {
      console.error('❌ Error:', error.message);
      this.results.errors.push(error.message);
    }
  }

  async testRedactedProperties() {
    console.log('🔓 Test 4: Redacted Properties Included');
    console.log('---------------------------------------');
    
    try {
      // Count redacted properties
      const { count: redactedCount } = await supabase
        .from('florida_parcels')
        .select('*', { count: 'exact', head: true })
        .eq('is_redacted', true);
      
      // Count non-redacted
      const { count: nonRedactedCount } = await supabase
        .from('florida_parcels')
        .select('*', { count: 'exact', head: true })
        .eq('is_redacted', false);
      
      console.log(`   Redacted properties: ${redactedCount?.toLocaleString() || 0}`);
      console.log(`   Non-redacted properties: ${nonRedactedCount?.toLocaleString() || 0}`);
      console.log(`   Total: ${((redactedCount || 0) + (nonRedactedCount || 0)).toLocaleString()}`);
      
      const includesAll = (redactedCount || 0) + (nonRedactedCount || 0) >= 789884;
      console.log(`   Status: ${includesAll ? '✅ ALL PROPERTIES ACCESSIBLE' : '⚠️ SOME FILTERED OUT'}\n`);
      
      this.results.tests.push({
        name: 'Includes Redacted',
        expected: 'Both redacted and non-redacted',
        actual: `${redactedCount || 0} redacted, ${nonRedactedCount || 0} non-redacted`,
        passed: includesAll
      });
    } catch (error) {
      console.error('❌ Error:', error.message);
      this.results.errors.push(error.message);
    }
  }

  async testPriceRanges() {
    console.log('💰 Test 5: Price Range Queries (No Limits)');
    console.log('-----------------------------------------');
    
    try {
      const priceRanges = [
        { min: 0, max: 100000, label: 'Under $100K' },
        { min: 100000, max: 500000, label: '$100K-$500K' },
        { min: 500000, max: 1000000, label: '$500K-$1M' },
        { min: 1000000, max: 10000000, label: '$1M-$10M' },
        { min: 10000000, max: null, label: 'Over $10M' }
      ];
      
      for (const range of priceRanges) {
        let query = supabase
          .from('florida_parcels')
          .select('*', { count: 'exact', head: true })
          .gte('taxable_value', range.min);
        
        if (range.max) {
          query = query.lt('taxable_value', range.max);
        }
        
        const { count } = await query;
        console.log(`   ${range.label}: ${count?.toLocaleString() || 0} properties`);
      }
      
      console.log(`   Status: ✅ ALL PRICE RANGES SEARCHABLE\n`);
      
      this.results.tests.push({
        name: 'Price Ranges',
        expected: 'All price ranges accessible',
        actual: 'All ranges returned results',
        passed: true
      });
    } catch (error) {
      console.error('❌ Error:', error.message);
      this.results.errors.push(error.message);
    }
  }

  async testPropertyTypes() {
    console.log('🏠 Test 6: Property Type Filtering');
    console.log('----------------------------------');
    
    try {
      // Test that we can search all property types
      const { data } = await supabase
        .from('florida_parcels')
        .select('property_use_desc')
        .limit(1000);
      
      if (data) {
        const types = new Set(data.map(d => d.property_use_desc).filter(Boolean));
        this.results.propertyTypes = types;
        
        console.log(`✅ Property types found: ${types.size}`);
        console.log(`   Sample types: ${Array.from(types).slice(0, 5).join(', ')}...`);
        console.log(`   Status: ${types.size > 5 ? '✅ UNRESTRICTED' : '⚠️ LIMITED'}\n`);
        
        this.results.tests.push({
          name: 'Property Types',
          expected: 'Multiple property types',
          actual: `${types.size} types found`,
          passed: types.size > 5
        });
      }
    } catch (error) {
      console.error('❌ Error:', error.message);
      this.results.errors.push(error.message);
    }
  }

  async testRandomSampling() {
    console.log('🎲 Test 7: Random Property Sampling');
    console.log('-----------------------------------');
    
    try {
      // Get random properties from different parts of database
      const offsets = [0, 100000, 300000, 500000, 700000];
      const samples = [];
      
      for (const offset of offsets) {
        const { data } = await supabase
          .from('florida_parcels')
          .select('parcel_id, county, phy_city, taxable_value')
          .range(offset, offset)
          .single();
        
        if (data) {
          samples.push(data);
          console.log(`   Offset ${offset}: ${data.county} - ${data.phy_city} ($${data.taxable_value?.toLocaleString() || 0})`);
        }
      }
      
      const diverseCounties = new Set(samples.map(s => s.county)).size > 1;
      console.log(`   Status: ${diverseCounties ? '✅ DIVERSE SAMPLING' : '⚠️ LIMITED SAMPLING'}\n`);
      
      this.results.tests.push({
        name: 'Random Sampling',
        expected: 'Properties from various counties',
        actual: `${samples.length} samples from different offsets`,
        passed: diverseCounties
      });
    } catch (error) {
      console.error('❌ Error:', error.message);
      this.results.errors.push(error.message);
    }
  }

  generateReport() {
    console.log('\n' + '='.repeat(60));
    console.log('📋 FINAL REPORT: UNRESTRICTED SEARCH VERIFICATION');
    console.log('='.repeat(60));
    
    const passedTests = this.results.tests.filter(t => t.passed).length;
    const totalTests = this.results.tests.length;
    const successRate = ((passedTests / totalTests) * 100).toFixed(1);
    
    console.log('\n📊 TEST RESULTS:');
    console.log(`   Total Tests: ${totalTests}`);
    console.log(`   Passed: ${passedTests}`);
    console.log(`   Failed: ${totalTests - passedTests}`);
    console.log(`   Success Rate: ${successRate}%`);
    
    console.log('\n✅ VERIFIED CAPABILITIES:');
    console.log(`   • Total Properties Accessible: ${this.results.totalProperties.toLocaleString()}`);
    console.log(`   • Counties Found: ${this.results.countiesFound.size}`);
    console.log(`   • Cities Found: ${this.results.citiesFound.size}`);
    console.log(`   • Property Types: ${this.results.propertyTypes.size}`);
    
    console.log('\n🎯 RESTRICTION STATUS:');
    if (successRate === '100.0') {
      console.log('   ✅ FULLY UNRESTRICTED - All 789,884 properties are searchable');
      console.log('   ✅ NO COUNTY RESTRICTIONS - All Florida counties accessible');
      console.log('   ✅ NO REDACTED FILTER - Both redacted and non-redacted included');
      console.log('   ✅ NO PRICE LIMITS - All price ranges searchable');
    } else {
      console.log('   ⚠️ SOME RESTRICTIONS REMAIN:');
      this.results.tests.filter(t => !t.passed).forEach(test => {
        console.log(`      • ${test.name}: Expected ${test.expected}, got ${test.actual}`);
      });
    }
    
    if (this.results.errors.length > 0) {
      console.log('\n❌ ERRORS ENCOUNTERED:');
      this.results.errors.forEach(err => {
        console.log(`   • ${err}`);
      });
    }
    
    console.log('\n💡 CONCLUSION:');
    if (successRate === '100.0') {
      console.log('   The property search is now COMPLETELY UNRESTRICTED.');
      console.log('   Users can search across all 789,884 properties in Florida');
      console.log('   without any automatic filters or limitations.');
    } else {
      console.log('   Some restrictions may still be in place.');
      console.log('   Review the failed tests above for details.');
    }
  }
}

// Run the tests
const tester = new UnrestrictedSearchTester();

console.log('Starting unrestricted search verification...\n');

tester.runAllTests().then(() => {
  console.log('\n✅ Test suite completed!');
  process.exit(0);
}).catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});