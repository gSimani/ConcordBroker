/**
 * DOR Code Conservative Parallel Assignment
 * Runs 3 counties in parallel with proper error handling and retries
 * Optimized for Supabase connection pool limits
 */

const { createClient } = require('@supabase/supabase-js');

// Configuration
const SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co';
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0';

const BATCH_SIZE = 5000;
const PARALLEL_WORKERS = 3; // Conservative for Supabase connection pool
const MAX_CALLS_PER_COUNTY = 200;
const RETRY_DELAY = 2000; // 2 second delay between retries
const MAX_RETRIES = 3;

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

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

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function processCountyBatchWithRetry(county, retryCount = 0) {
  try {
    const { data, error } = await supabase.rpc('assign_dor_codes_batch', {
      target_county: county,
      batch_size: BATCH_SIZE
    });

    if (error) throw error;
    return data[0];
  } catch (error) {
    if (retryCount < MAX_RETRIES && (error.message.includes('timeout') || error.message.includes('connection pool'))) {
      console.log(`[${county}] Retry ${retryCount + 1}/${MAX_RETRIES} after error: ${error.message}`);
      await sleep(RETRY_DELAY * (retryCount + 1));
      return processCountyBatchWithRetry(county, retryCount + 1);
    }
    console.error(`[${county}] ERROR after ${retryCount} retries: ${error.message}`);
    return null;
  }
}

async function processCounty(county, workerIndex) {
  console.log(`[Worker ${workerIndex}] 🏁 Starting ${county}`);

  let callCount = 0;
  let totalProcessed = 0;
  let lastRemaining = -1;
  let consecutiveFailures = 0;

  while (callCount < MAX_CALLS_PER_COUNTY) {
    callCount++;

    const result = await processCountyBatchWithRetry(county);

    if (!result) {
      consecutiveFailures++;
      if (consecutiveFailures >= 3) {
        console.log(`[Worker ${workerIndex}] ⚠️  ${county} - 3 consecutive failures, skipping for now`);
        break;
      }
      await sleep(1000); // Wait 1s before next attempt
      continue;
    }

    consecutiveFailures = 0;
    const { processed_count, remaining_count } = result;
    totalProcessed += processed_count;

    // Log progress every 20 calls
    if (callCount % 20 === 0) {
      console.log(`[Worker ${workerIndex}] ${county} - Call ${callCount}: ${totalProcessed.toLocaleString()} processed, ${remaining_count.toLocaleString()} remaining`);
    }

    // Stop if complete
    if (remaining_count === 0 || processed_count === 0) {
      console.log(`[Worker ${workerIndex}] ✅ ${county} COMPLETE - ${totalProcessed.toLocaleString()} properties in ${callCount} calls`);
      break;
    }

    // Stop if stuck
    if (lastRemaining !== -1 && remaining_count >= lastRemaining) {
      console.log(`[Worker ${workerIndex}] ⚠️  ${county} - Progress stalled at ${remaining_count.toLocaleString()} remaining`);
      break;
    }

    lastRemaining = remaining_count;

    // Small delay between calls
    await sleep(100);
  }

  return { county, totalProcessed, callCount };
}

async function getCountiesNeedingWork() {
  try {
    const { data, error } = await supabase.rpc('get_county_coverage_stats');
    if (error) throw error;

    // Return counties with <99% coverage, sorted by remaining properties (biggest first)
    return data
      .filter(c => c.coverage < 99)
      .sort((a, b) => (b.total_properties - b.coded_properties) - (a.total_properties - a.coded_properties))
      .map(c => c.county);
  } catch (error) {
    console.error('[ERROR] Failed to get county stats, using full county list');
    return ALL_COUNTIES;
  }
}

async function main() {
  console.log('='.repeat(100));
  console.log('DOR CODE CONSERVATIVE PARALLEL ASSIGNMENT - ALL COUNTIES');
  console.log('='.repeat(100));
  console.log(`Parallel Workers: ${PARALLEL_WORKERS} (optimized for Supabase connection pool)`);
  console.log(`Batch Size: ${BATCH_SIZE} properties per call`);
  console.log(`Max Retries: ${MAX_RETRIES} with exponential backoff`);
  console.log(`Started: ${new Date().toLocaleString()}`);
  console.log('='.repeat(100));

  // Get counties that need work
  const countiesNeedingWork = await getCountiesNeedingWork();

  console.log(`\n📋 Counties to process: ${countiesNeedingWork.length}`);
  console.log(`🚀 Processing ${PARALLEL_WORKERS} counties at a time\n`);

  const results = [];
  let completedCount = 0;
  let workerIndex = 0;

  // Process counties in parallel batches of 3
  for (let i = 0; i < countiesNeedingWork.length; i += PARALLEL_WORKERS) {
    const batch = countiesNeedingWork.slice(i, i + PARALLEL_WORKERS);

    console.log(`\n${'='.repeat(100)}`);
    console.log(`🔄 Batch ${Math.floor(i / PARALLEL_WORKERS) + 1}/${Math.ceil(countiesNeedingWork.length / PARALLEL_WORKERS)}: ${batch.join(', ')}`);
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

    // Small delay between batches to let connection pool recover
    if (i + PARALLEL_WORKERS < countiesNeedingWork.length) {
      console.log('⏸️  Waiting 5s before next batch...\n');
      await sleep(5000);
    }
  }

  // Final summary
  console.log('\n' + '='.repeat(100));
  console.log('PARALLEL PROCESSING COMPLETE');
  console.log('='.repeat(100));

  try {
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
  } catch (error) {
    console.error('Could not fetch final stats:', error.message);
  }

  console.log(`\nCompleted: ${new Date().toLocaleString()}`);
  console.log('='.repeat(100));
}

// Run it
main().catch(error => {
  console.error('\n[FATAL ERROR]', error);
  process.exit(1);
});
