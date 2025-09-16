#!/usr/bin/env node

import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load environment variables
dotenv.config({ path: join(__dirname, 'apps/web/.env') });

const supabaseUrl = process.env.VITE_SUPABASE_URL || 'https://pmispwtdngkcmsrsjwbp.supabase.co';
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A';

const supabase = createClient(supabaseUrl, supabaseKey);

async function populateSunbizData() {
  console.log('[INFO] Populating Sunbiz corporate data...');
  console.log(`[INFO] Target: ${supabaseUrl}\n`);
  
  try {
    // Create sunbiz_corporate table if it doesn't exist
    console.log('[1] Creating sunbiz_corporate table if needed...');
    
    // Sample Sunbiz data with officers matching our property owners
    const sunbizData = [
      {
        document_number: 'L24000111111',
        corporate_name: 'SMITH FAMILY INVESTMENTS LLC',
        status: 'ACTIVE',
        filing_type: 'Florida Limited Liability',
        date_filed: '2024-01-10',
        state: 'FL',
        principal_address: '1234 SAMPLE ST, FORT LAUDERDALE, FL 33301',
        mailing_address: 'PO BOX 1234, FORT LAUDERDALE, FL 33301',
        registered_agent_name: 'REGISTERED AGENTS INC',
        registered_agent_address: '100 AGENT ST, MIAMI, FL 33131',
        officers: JSON.stringify([
          {name: 'SMITH JOHN', title: 'Managing Member'},
          {name: 'SMITH MARY', title: 'Member'}
        ])
      },
      {
        document_number: 'L23000222222',
        corporate_name: 'JR HOLDINGS CORPORATION',
        status: 'ACTIVE',
        filing_type: 'Florida Profit Corporation',
        date_filed: '2023-03-15',
        state: 'FL',
        principal_address: '500 BUSINESS PARK DR, FORT LAUDERDALE, FL 33301',
        mailing_address: '500 BUSINESS PARK DR, FORT LAUDERDALE, FL 33301',
        registered_agent_name: 'JOHNSON ROBERT',
        registered_agent_address: '1236 SAMPLE ST, FORT LAUDERDALE, FL 33301',
        officers: JSON.stringify([
          {name: 'JOHNSON ROBERT', title: 'President'},
          {name: 'JOHNSON SARAH', title: 'Secretary'},
          {name: 'JOHNSON MICHAEL', title: 'Treasurer'}
        ])
      },
      {
        document_number: 'L24000333333',
        corporate_name: 'SUNSHINE INVESTMENTS CORP',
        status: 'ACTIVE',
        filing_type: 'Florida Profit Corporation',
        date_filed: '2024-01-15',
        state: 'FL',
        principal_address: '5678 EXAMPLE AVE, PEMBROKE PINES, FL 33028',
        mailing_address: 'PO BOX 12345, MIAMI, FL 33101',
        registered_agent_name: 'CORPORATE SERVICES LLC',
        registered_agent_address: '200 AGENT AVE, MIAMI, FL 33131',
        officers: JSON.stringify([
          {name: 'SUNSHINE DAVID', title: 'CEO'},
          {name: 'SUNSHINE PATRICIA', title: 'CFO'},
          {name: 'INVESTMENTS MANAGER', title: 'COO'}
        ])
      },
      {
        document_number: 'L22000444444',
        corporate_name: 'BEACH PROPERTIES LLC',
        status: 'ACTIVE',
        filing_type: 'Florida Limited Liability',
        date_filed: '2022-06-20',
        state: 'FL',
        principal_address: '789 OCEAN BLVD, FORT LAUDERDALE, FL 33308',
        mailing_address: '100 CORPORATE BLVD, MIAMI, FL 33131',
        registered_agent_name: 'BEACH PROPERTIES AGENT',
        registered_agent_address: '100 CORPORATE BLVD, MIAMI, FL 33131',
        officers: JSON.stringify([
          {name: 'BEACH THOMAS', title: 'Manager'},
          {name: 'OCEAN JENNIFER', title: 'Member'}
        ])
      },
      {
        document_number: 'L21000555555',
        corporate_name: 'MARTINEZ FAMILY TRUST LLC',
        status: 'ACTIVE',
        filing_type: 'Florida Limited Liability',
        date_filed: '2021-09-10',
        state: 'FL',
        principal_address: '456 PALM AVE, HOLLYWOOD, FL 33020',
        mailing_address: '456 PALM AVE, HOLLYWOOD, FL 33020',
        registered_agent_name: 'MARTINEZ JUAN',
        registered_agent_address: '456 PALM AVE, HOLLYWOOD, FL 33020',
        officers: JSON.stringify([
          {name: 'MARTINEZ JUAN', title: 'Trustee'},
          {name: 'MARTINEZ MARIA', title: 'Beneficiary'}
        ])
      },
      {
        document_number: 'L20000666666',
        corporate_name: 'OFFICE PARK HOLDINGS',
        status: 'ACTIVE',
        filing_type: 'Florida Profit Corporation',
        date_filed: '2020-12-01',
        state: 'FL',
        principal_address: '2100 CORPORATE DR, DAVIE, FL 33324',
        mailing_address: '1000 BRICKELL AVE, MIAMI, FL 33131',
        registered_agent_name: 'COMMERCIAL AGENTS LLC',
        registered_agent_address: '1000 BRICKELL AVE, MIAMI, FL 33131',
        officers: JSON.stringify([
          {name: 'PARK WILLIAM', title: 'President'},
          {name: 'HOLDINGS ELIZABETH', title: 'Vice President'}
        ])
      },
      // Additional companies where our individual owners are officers
      {
        document_number: 'L23000777777',
        corporate_name: 'FORT LAUDERDALE REAL ESTATE GROUP LLC',
        status: 'ACTIVE',
        filing_type: 'Florida Limited Liability',
        date_filed: '2023-07-01',
        state: 'FL',
        principal_address: '999 COMMERCIAL BLVD, FORT LAUDERDALE, FL 33308',
        mailing_address: '999 COMMERCIAL BLVD, FORT LAUDERDALE, FL 33308',
        registered_agent_name: 'FL AGENTS INC',
        registered_agent_address: '100 AGENT ST, MIAMI, FL 33131',
        officers: JSON.stringify([
          {name: 'SMITH JOHN', title: 'Member'},  // Same person who owns 064210010010
          {name: 'JOHNSON ROBERT', title: 'Member'},  // Same person who owns 064210010011
          {name: 'WILLIAMS JAMES', title: 'Managing Member'}
        ])
      },
      {
        document_number: 'L22000888888',
        corporate_name: 'SOUTH FLORIDA PROPERTY VENTURES INC',
        status: 'ACTIVE',
        filing_type: 'Florida Profit Corporation',
        date_filed: '2022-11-15',
        state: 'FL',
        principal_address: '777 VENTURE WAY, MIAMI, FL 33131',
        mailing_address: '777 VENTURE WAY, MIAMI, FL 33131',
        registered_agent_name: 'VENTURE AGENTS',
        registered_agent_address: '777 VENTURE WAY, MIAMI, FL 33131',
        officers: JSON.stringify([
          {name: 'SMITH MARY', title: 'Secretary'},  // Co-owner of 064210010010
          {name: 'MARTINEZ JUAN', title: 'Director'},  // Owner of 514228131130
          {name: 'ANDERSON PAUL', title: 'President'}
        ])
      }
    ];
    
    console.log('[2] Inserting Sunbiz corporate data...');
    
    for (const corp of sunbizData) {
      try {
        // Check if already exists
        const { data: existing } = await supabase
          .from('sunbiz_corporate')
          .select('document_number')
          .eq('document_number', corp.document_number)
          .single();
        
        if (existing) {
          // Update existing
          const { error } = await supabase
            .from('sunbiz_corporate')
            .update(corp)
            .eq('document_number', corp.document_number);
          
          if (error) throw error;
          console.log(`  ✅ Updated: ${corp.corporate_name}`);
        } else {
          // Insert new
          const { error } = await supabase
            .from('sunbiz_corporate')
            .insert(corp);
          
          if (error) throw error;
          console.log(`  ✅ Inserted: ${corp.corporate_name}`);
        }
        
        // Parse and display officers
        const officers = JSON.parse(corp.officers);
        console.log(`     Officers: ${officers.map(o => `${o.name} (${o.title})`).join(', ')}`);
        
      } catch (e) {
        console.log(`  ⚠️ Error with ${corp.corporate_name}: ${e.message}`);
      }
    }
    
    console.log('\n[3] Testing Sunbiz matching...');
    
    // Test the matching for our property owners
    const testOwners = [
      { name: 'SMITH JOHN & MARY', parcel: '064210010010' },
      { name: 'JOHNSON ROBERT', parcel: '064210010011' },
      { name: 'MARTINEZ FAMILY TRUST', parcel: '514228131130' }
    ];
    
    for (const owner of testOwners) {
      console.log(`\nTesting owner: ${owner.name} (${owner.parcel})`);
      
      // Test company name search
      const { data: companyMatches } = await supabase
        .from('sunbiz_corporate')
        .select('*')
        .ilike('corporate_name', `%${owner.name.replace(/[^a-zA-Z0-9\s]/g, '')}%`)
        .limit(5);
      
      if (companyMatches && companyMatches.length > 0) {
        console.log(`  Found ${companyMatches.length} companies by name`);
      }
      
      // Test officer search
      const individualName = owner.name.split(/[&,]/)[0]?.trim();
      if (individualName) {
        const { data: officerMatches } = await supabase
          .from('sunbiz_corporate')
          .select('*')
          .ilike('officers', `%${individualName}%`)
          .limit(5);
        
        if (officerMatches && officerMatches.length > 0) {
          console.log(`  Found ${officerMatches.length} companies where owner is officer`);
          officerMatches.forEach(match => {
            console.log(`    - ${match.corporate_name}`);
          });
        }
      }
    }
    
    console.log('\n✅ Sunbiz data population completed!');
    console.log('\n💡 TESTING THE IMPROVED MATCHING:');
    console.log('1. Navigate to a property owned by an individual:');
    console.log('   http://localhost:5175/property/064210010010 (SMITH JOHN & MARY)');
    console.log('   http://localhost:5175/property/064210010011 (JOHNSON ROBERT)');
    console.log('\n2. Check the Sunbiz Info tab - it should now show:');
    console.log('   - Companies where the owner is an officer');
    console.log('   - Not just companies with matching addresses');
    console.log('\n3. For company-owned properties, it will show the company directly:');
    console.log('   http://localhost:5175/property/064210015020 (SUNSHINE INVESTMENTS CORP)');
    
  } catch (e) {
    console.error('\n❌ Error:', e);
  }
}

// Run the function
populateSunbizData().then(() => {
  console.log('\n✅ Script completed');
  process.exit(0);
}).catch(error => {
  console.error('\n❌ Script failed:', error);
  process.exit(1);
});