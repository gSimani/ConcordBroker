/**
 * DOR Code Parallel Assignment - ALL COUNTIES
 * Runs 10 counties in parallel using Railway Pro resources
 * Processes all 67 Florida counties with aggressive concurrency
 */

const { createClient } = require('@supabase/supabase-js');
const { Worker } = require('worker_threads');
const fs = require('fs');

// Configuration
const SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co';
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0';

const BATCH_SIZE = 5000;
const PARALLEL_WORKERS = 10; // Railway Pro can handle 10+ parallel workers
const MAX_CALLS_PER_COUNTY = 200;

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

// All 67 Florida counties
const ALL_COUNTIES = [
  'ALACHUA', 'BAKER', 'BAY', 'BRADFORD', 'BREVARD', 'BROWARD', 'CALHOUN',
  'CHARLOTTE', 'CITRUS', 'CLAY', 'COLLIER', 'COLUMBIA', 'DESOTO', 'DIXIE',
  'DUVAL', 'ESCAMBIA', 'FLAGLER', 'FRANKLIN', 'GADSDEN', 'GILCHRIST', 'GLADES',
  'GULF', 'HAMILTON', 'HARDEE', 'HENDRY', 'HERNANDO', 'HIGHLANDS', 'HILLSBOROUGH',
  'HOLMES', 'INDIAN RIVER', 'JACKSON', 'JEFFERSON', 'LAFAYETTE', 'LAKE', 'LEE',
  'LEON', 'LEVY', 'LIBERTY', 'MADISON', 'MANATEE', 'MARION', 'MARTIN', 'DADE',
  'MONROE', 'NASSAU', 'OKALOOSA', 'OKEECHOBEE', 'ORANGE', 'OSCEOLA', 'PALM BEACH',
  'PASCO', 'PINELLAS', 'POLK', 'PUTNAM', 'SANTA ROSA', 'SARASOTA', 'SEMINOLE',
  'ST JOHNS', 'ST LUCIE', 'SUMTER', 'SUWANNEE', 'TAYLOR', 'UNION', 'VOLUSIA',
  'WAKULLA', 'WALTON', 'WASHINGTON'
];

async function getCountiesNeedingWork() {
  try {
    const { data, error } = await supabase.rpc('get_county_coverage_stats');

    if (error) throw error;

    // Return counties with <99.5% coverage, sorted by number of properties (biggest first)
    return data
      .filter(c => c.coverage < 99.5)
      .sort((a, b) => (b.total_properties - b.coded_properties) - (a.total_properties - a.coded_properties))
      .map(c => c.county);
  } catch (error) {
    console.error('[ERROR] Failed to get county stats:', error.message);
    return ALL_COUNTIES;
  }
}

async function processCountyBatch(county) {
  try {
    const { data, error } = await supabase.rpc('assign_dor_codes_batch', {
      target_county: county,
      batch_size: BATCH_SIZE
    });

    if (error) throw error;
    return data[0];
  } catch (error) {
    console.error(`[${county}] ERROR: ${error.message}`);
    return null;
  }
}

async function processCounty(county, workerIndex) {
  console.log(`[Worker ${workerIndex}] Starting ${county}`);

  let callCount = 0;
  let totalProcessed = 0;
  let lastRemaining = -1;

  while (callCount < MAX_CALLS_PER_COUNTY) {
    callCount++;

    const result = await processCountyBatch(county);

    if (!result) {
      console.log(`[Worker ${workerIndex}] ${county} - Call ${callCount} failed, stopping`);
      break;
    }

    const { processed_count, remaining_count } = result;
    totalProcessed += processed_count;

    // Log progress every 10 calls
    if (callCount % 10 === 0) {
      console.log(`[Worker ${workerIndex}] ${county} - Call ${callCount}: Processed ${totalProcessed.toLocaleString()}, Remaining ${remaining_count.toLocaleString()}`);
    }

    // Stop if complete
    if (remaining_count === 0 || processed_count === 0) {
      console.log(`[Worker ${workerIndex}] ✅ ${county} COMPLETE - Processed ${totalProcessed.toLocaleString()} properties in ${callCount} calls`);
      break;
    }

    // Stop if stuck
    if (lastRemaining !== -1 && remaining_count >= lastRemaining) {
      console.log(`[Worker ${workerIndex}] ⚠️  ${county} - Progress stalled, moving to next county`);
      break;
    }

    lastRemaining = remaining_count;

    // Small delay to be nice to the database
    await new Promise(resolve => setTimeout(resolve, 50));
  }

  return { county, totalProcessed, callCount };
}

async function main() {
  console.log('='.repeat(100));
  console.log('DOR CODE PARALLEL ASSIGNMENT - ALL 67 FLORIDA COUNTIES');
  console.log('='.repeat(100));
  console.log(`Parallel Workers: ${PARALLEL_WORKERS}`);
  console.log(`Batch Size: ${BATCH_SIZE} properties per call`);
  console.log(`Railway Pro: ENABLED`);
  console.log(`Started: ${new Date().toLocaleString()}`);
  console.log('='.repeat(100));

  // Get counties that need work
  const countiesNeedingWork = await getCountiesNeedingWork();

  console.log(`\n📋 Counties to process: ${countiesNeedingWork.length}`);
  console.log(`🚀 Processing ${Math.min(PARALLEL_WORKERS, countiesNeedingWork.length)} counties at a time\n`);

  const results = [];
  let completedCount = 0;
  let workerIndex = 0;

  // Process counties in parallel batches
  for (let i = 0; i < countiesNeedingWork.length; i += PARALLEL_WORKERS) {
    const batch = countiesNeedingWork.slice(i, i + PARALLEL_WORKERS);

    console.log(`\n${'='.repeat(100)}`);
    console.log(`🔄 Processing batch ${Math.floor(i / PARALLEL_WORKERS) + 1}: ${batch.join(', ')}`);
    console.log('='.repeat(100));

    // Process this batch in parallel
    const batchPromises = batch.map((county, idx) =>
      processCounty(county, workerIndex + idx)
    );

    const batchResults = await Promise.all(batchPromises);
    results.push(...batchResults);
    completedCount += batch.length;
    workerIndex += batch.length;

    console.log(`\n✅ Completed ${completedCount}/${countiesNeedingWork.length} counties\n`);
  }

  // Final summary
  console.log('\n' + '='.repeat(100));
  console.log('PARALLEL PROCESSING COMPLETE - ALL COUNTIES');
  console.log('='.repeat(100));

  const finalStats = await supabase.rpc('get_county_coverage_stats');

  if (finalStats.data) {
    const totalProps = finalStats.data.reduce((sum, c) => sum + c.total_properties, 0);
    const codedProps = finalStats.data.reduce((sum, c) => sum + c.coded_properties, 0);
    const overallCoverage = (codedProps / totalProps * 100).toFixed(2);

    console.log(`\n📊 Overall Florida Coverage:`);
    console.log(`  Total Properties: ${totalProps.toLocaleString()}`);
    console.log(`  Coded Properties: ${codedProps.toLocaleString()}`);
    console.log(`  Coverage: ${overallCoverage}%`);

    const perfect = finalStats.data.filter(c => c.coverage >= 99.5).length;
    const excellent = finalStats.data.filter(c => c.coverage >= 95 && c.coverage < 99.5).length;
    const good = finalStats.data.filter(c => c.coverage >= 90 && c.coverage < 95).length;

    console.log(`\n🏆 County Grades:`);
    console.log(`  10/10 PERFECT: ${perfect} counties`);
    console.log(`  9/10 EXCELLENT: ${excellent} counties`);
    console.log(`  8/10 GOOD: ${good} counties`);
  }

  console.log(`\nCompleted: ${new Date().toLocaleString()}`);
  console.log('='.repeat(100));
}

// Run it
main().catch(error => {
  console.error('\n[FATAL ERROR]', error);
  process.exit(1);
});
