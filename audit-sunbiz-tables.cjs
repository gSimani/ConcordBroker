/**
 * Sunbiz Tables Audit Script
 * Comprehensive analysis of Sunbiz data relationships with:
 * - Property owners (florida_parcels)
 * - Officers
 * - Addresses
 * - Entities
 */

const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

const supabase = createClient(
  process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.VITE_SUPABASE_ANON_KEY
);

async function auditSunbizTables() {
  console.log('🔍 Starting Sunbiz Tables Audit...\n');
  console.log('=' .repeat(80));

  const results = {
    tables: [],
    relationships: [],
    dataQuality: [],
    recommendations: []
  };

  try {
    // Step 1: Identify all Sunbiz-related tables
    console.log('\n📊 STEP 1: Identifying Sunbiz Tables\n');

    const tablesToCheck = [
      'sunbiz_corporate',
      'florida_entities',
      'sunbiz_entities',
      'sunbiz_corporations',
      'sunbiz_fictitious_names',
      'sunbiz_registered_agents',
      'sunbiz_officer_contacts',
      'sunbiz_entity_search',
      'tax_deed_entity_matches'
    ];

    for (const tableName of tablesToCheck) {
      try {
        const { count, error } = await supabase
          .from(tableName)
          .select('*', { count: 'exact', head: true });

        if (!error) {
          console.log(`✅ ${tableName.padEnd(35)} - ${(count || 0).toLocaleString()} records`);
          results.tables.push({ name: tableName, count: count || 0, exists: true });
        } else {
          console.log(`❌ ${tableName.padEnd(35)} - Table not found or no access`);
          results.tables.push({ name: tableName, exists: false, error: error.message });
        }
      } catch (err) {
        console.log(`❌ ${tableName.padEnd(35)} - Error: ${err.message}`);
        results.tables.push({ name: tableName, exists: false, error: err.message });
      }
    }

    // Step 2: Analyze florida_entities structure
    console.log('\n' + '='.repeat(80));
    console.log('\n📋 STEP 2: Analyzing florida_entities Structure\n');

    const { data: entitiesSample, error: entitiesError } = await supabase
      .from('florida_entities')
      .select('*')
      .limit(5);

    if (!entitiesError && entitiesSample) {
      console.log(`Sample record columns: ${Object.keys(entitiesSample[0] || {}).join(', ')}`);

      // Get entity type distribution
      const { data: entityTypes } = await supabase
        .from('florida_entities')
        .select('entity_type')
        .limit(1000);

      if (entityTypes) {
        const typeCounts = {};
        entityTypes.forEach(e => {
          typeCounts[e.entity_type || 'NULL'] = (typeCounts[e.entity_type || 'NULL'] || 0) + 1;
        });
        console.log('\nEntity Type Distribution (sample of 1000):');
        Object.entries(typeCounts).forEach(([type, count]) => {
          console.log(`  ${type.padEnd(30)} - ${count} records`);
        });
      }
    }

    // Step 3: Analyze sunbiz_corporate structure
    console.log('\n' + '='.repeat(80));
    console.log('\n📋 STEP 3: Analyzing sunbiz_corporate Structure\n');

    const { data: corporateSample, error: corpError } = await supabase
      .from('sunbiz_corporate')
      .select('*')
      .limit(5);

    if (!corpError && corporateSample && corporateSample.length > 0) {
      console.log(`Sample record columns: ${Object.keys(corporateSample[0]).join(', ')}`);

      // Get status distribution
      const { data: statuses } = await supabase
        .from('sunbiz_corporate')
        .select('status')
        .limit(1000);

      if (statuses) {
        const statusCounts = {};
        statuses.forEach(s => {
          statusCounts[s.status || 'NULL'] = (statusCounts[s.status || 'NULL'] || 0) + 1;
        });
        console.log('\nStatus Distribution (sample of 1000):');
        Object.entries(statusCounts).forEach(([status, count]) => {
          console.log(`  ${status.padEnd(30)} - ${count} records`);
        });
      }
    }

    // Step 4: Link entities to property owners
    console.log('\n' + '='.repeat(80));
    console.log('\n🔗 STEP 4: Linking Entities to Property Owners\n');

    const { data: parcels, error: parcelsError } = await supabase
      .from('florida_parcels')
      .select('parcel_id, owner_name, county')
      .not('owner_name', 'is', null)
      .limit(100);

    if (!parcelsError && parcels) {
      console.log(`✅ Retrieved ${parcels.length} property owner samples`);

      // Try to match property owners to entities
      let matchCount = 0;
      const matchedExamples = [];

      for (const parcel of parcels.slice(0, 20)) {
        const ownerName = parcel.owner_name.toUpperCase().trim();

        // Check in florida_entities
        const { data: entityMatch } = await supabase
          .from('florida_entities')
          .select('entity_id, entity_name, entity_type')
          .ilike('entity_name', `%${ownerName}%`)
          .limit(1);

        if (entityMatch && entityMatch.length > 0) {
          matchCount++;
          if (matchedExamples.length < 5) {
            matchedExamples.push({
              parcel: parcel.parcel_id,
              owner: parcel.owner_name,
              entity: entityMatch[0].entity_name,
              type: entityMatch[0].entity_type
            });
          }
        }
      }

      console.log(`\nMatched ${matchCount} out of 20 property owners to entities`);
      console.log(`Match rate: ${((matchCount / 20) * 100).toFixed(1)}%`);

      if (matchedExamples.length > 0) {
        console.log('\nExample matches:');
        matchedExamples.forEach((m, i) => {
          console.log(`  ${i + 1}. Property Owner: ${m.owner}`);
          console.log(`     Entity Match: ${m.entity} (${m.type})`);
        });
      }

      results.relationships.push({
        type: 'property_owner_to_entity',
        matchRate: (matchCount / 20) * 100,
        sampleSize: 20,
        examples: matchedExamples
      });
    }

    // Step 5: Analyze officer contacts if table exists
    console.log('\n' + '='.repeat(80));
    console.log('\n👥 STEP 5: Analyzing Officer Contacts\n');

    const officerTable = results.tables.find(t => t.name === 'sunbiz_officer_contacts');
    if (officerTable && officerTable.exists) {
      const { data: officers, error: officersError } = await supabase
        .from('sunbiz_officer_contacts')
        .select('entity_name, officer_name, officer_email, officer_phone')
        .not('officer_email', 'is', null)
        .limit(10);

      if (!officersError && officers) {
        console.log(`✅ Found ${officers.length} officers with contact information`);
        console.log('\nSample officers:');
        officers.slice(0, 5).forEach((o, i) => {
          console.log(`  ${i + 1}. ${o.officer_name} (${o.entity_name})`);
          console.log(`     Email: ${o.officer_email || 'N/A'} | Phone: ${o.officer_phone || 'N/A'}`);
        });
      }
    } else {
      console.log('❌ sunbiz_officer_contacts table not found');
    }

    // Step 6: Analyze address relationships
    console.log('\n' + '='.repeat(80));
    console.log('\n🏢 STEP 6: Analyzing Address Relationships\n');

    // Check if sunbiz_corporate has address fields
    if (!corpError && corporateSample && corporateSample.length > 0) {
      const addressFields = Object.keys(corporateSample[0]).filter(k =>
        k.includes('address') || k.includes('city') || k.includes('state') || k.includes('zip')
      );

      console.log(`Address-related fields in sunbiz_corporate: ${addressFields.join(', ')}`);

      // Sample address data
      const { data: addressSample } = await supabase
        .from('sunbiz_corporate')
        .select('entity_name, principal_address, principal_city, principal_state, principal_zip, mailing_address')
        .not('principal_address', 'is', null)
        .limit(5);

      if (addressSample) {
        console.log('\nSample addresses:');
        addressSample.forEach((a, i) => {
          console.log(`  ${i + 1}. ${a.entity_name}`);
          console.log(`     Principal: ${a.principal_address}, ${a.principal_city}, ${a.principal_state} ${a.principal_zip}`);
          if (a.mailing_address) {
            console.log(`     Mailing: ${a.mailing_address}`);
          }
        });
      }
    }

    // Step 7: Data quality analysis
    console.log('\n' + '='.repeat(80));
    console.log('\n✅ STEP 7: Data Quality Analysis\n');

    // Check for null values in critical fields
    if (!corpError && corporateSample) {
      const { count: totalCorp } = await supabase
        .from('sunbiz_corporate')
        .select('*', { count: 'exact', head: true });

      const { count: noAddress } = await supabase
        .from('sunbiz_corporate')
        .select('*', { count: 'exact', head: true })
        .is('principal_address', null);

      const { count: noEmail } = await supabase
        .from('sunbiz_officer_contacts')
        .select('*', { count: 'exact', head: true })
        .is('officer_email', null);

      console.log('Data Completeness:');
      console.log(`  sunbiz_corporate with addresses: ${(((totalCorp - noAddress) / totalCorp) * 100).toFixed(1)}%`);
      console.log(`  Officers with email addresses: ${((1 - (noEmail / officerTable?.count || 1)) * 100).toFixed(1)}%`);

      results.dataQuality.push({
        table: 'sunbiz_corporate',
        addressCompleteness: ((totalCorp - noAddress) / totalCorp) * 100
      });
    }

    // Step 8: Generate recommendations
    console.log('\n' + '='.repeat(80));
    console.log('\n💡 STEP 8: Recommendations\n');

    const recommendations = [];

    // Check if linking tables exist
    const linkingTable = results.tables.find(t => t.name === 'tax_deed_entity_matches');
    if (!linkingTable || !linkingTable.exists) {
      recommendations.push({
        priority: 'HIGH',
        issue: 'Missing linking table',
        recommendation: 'Create tax_deed_entity_matches table to link properties to entities'
      });
    }

    // Check officer contacts
    const officersTable = results.tables.find(t => t.name === 'sunbiz_officer_contacts');
    if (officersTable && officersTable.exists && officersTable.count > 0) {
      recommendations.push({
        priority: 'MEDIUM',
        issue: 'Officer contacts available',
        recommendation: 'Implement UI to display officer contacts in property detail views'
      });
    }

    // Check entity matching
    if (results.relationships.length > 0) {
      const matchRate = results.relationships[0].matchRate;
      if (matchRate < 50) {
        recommendations.push({
          priority: 'HIGH',
          issue: `Low entity match rate: ${matchRate.toFixed(1)}%`,
          recommendation: 'Implement fuzzy matching algorithm to improve owner-to-entity linkage'
        });
      }
    }

    recommendations.forEach((rec, i) => {
      console.log(`${i + 1}. [${rec.priority}] ${rec.issue}`);
      console.log(`   → ${rec.recommendation}\n`);
    });

    results.recommendations = recommendations;

    // Final summary
    console.log('\n' + '='.repeat(80));
    console.log('\n📝 AUDIT SUMMARY\n');
    console.log(`Tables Found: ${results.tables.filter(t => t.exists).length}/${results.tables.length}`);
    console.log(`Relationships Analyzed: ${results.relationships.length}`);
    console.log(`Quality Issues: ${results.dataQuality.length}`);
    console.log(`Recommendations: ${results.recommendations.length}`);

    // Save report
    const fs = require('fs');
    fs.writeFileSync(
      'SUNBIZ_AUDIT_REPORT.json',
      JSON.stringify(results, null, 2)
    );
    console.log('\n✅ Full audit report saved to: SUNBIZ_AUDIT_REPORT.json');

  } catch (error) {
    console.error('\n❌ Audit failed:', error.message);
    console.error(error.stack);
  }
}

// Run audit
auditSunbizTables();
