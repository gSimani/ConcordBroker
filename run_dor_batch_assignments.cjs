/**
 * DOR Code Batch Assignment Runner
 * Calls the assign_dor_codes_batch stored procedure repeatedly using service role
 */

const { createClient } = require('@supabase/supabase-js');

// Configuration
const SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co';
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0';

const TARGET_COUNTY = 'DADE';
const BATCH_SIZE = 5000;
const CALLS_PER_UPDATE = 10; // Show progress every 10 calls
const MAX_CALLS = 200; // Safety limit (1M properties)

// Initialize Supabase client with service role
const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

async function callBatchFunction() {
  try {
    const { data, error } = await supabase.rpc('assign_dor_codes_batch', {
      target_county: TARGET_COUNTY,
      batch_size: BATCH_SIZE
    });

    if (error) {
      throw error;
    }

    return data[0]; // Returns { processed_count, remaining_count }
  } catch (error) {
    console.error(`    [ERROR] Batch call failed: ${error.message}`);
    return null;
  }
}

async function getDADECoverage() {
  try {
    // Get total
    const { count: total } = await supabase
      .from('florida_parcels')
      .select('*', { count: 'exact', head: true })
      .eq('year', 2025)
      .eq('county', TARGET_COUNTY);

    // Get with codes
    const { count: withCode } = await supabase
      .from('florida_parcels')
      .select('*', { count: 'exact', head: true })
      .eq('year', 2025)
      .eq('county', TARGET_COUNTY)
      .not('land_use_code', 'is', null)
      .neq('land_use_code', '')
      .neq('land_use_code', '99');

    const coverage = total > 0 ? (withCode / total * 100).toFixed(2) : 0;

    return { total, withCode, coverage };
  } catch (error) {
    console.error(`[ERROR] Coverage check failed: ${error.message}`);
    return { total: 0, withCode: 0, coverage: 0 };
  }
}

async function main() {
  console.log('='.repeat(80));
  console.log('DOR CODE BATCH ASSIGNMENT RUNNER');
  console.log('='.repeat(80));
  console.log(`Target County: ${TARGET_COUNTY}`);
  console.log(`Batch Size: ${BATCH_SIZE} properties per call`);
  console.log(`Started: ${new Date().toLocaleString()}`);
  console.log('='.repeat(80));

  // Initial stats
  const initialStats = await getDADECoverage();
  console.log(`\n[STATUS] Initial coverage: ${initialStats.withCode.toLocaleString()}/${initialStats.total.toLocaleString()} (${initialStats.coverage}%)`);

  let callCount = 0;
  let totalProcessed = 0;
  let lastRemaining = -1;

  while (callCount < MAX_CALLS) {
    callCount++;

    console.log(`\n[Call ${callCount}] Calling assign_dor_codes_batch...`);

    const result = await callBatchFunction();

    if (!result) {
      console.log(`[Call ${callCount}] Failed - stopping`);
      break;
    }

    const { processed_count, remaining_count } = result;

    console.log(`[Call ${callCount}] Processed: ${processed_count.toLocaleString()}, Remaining: ${remaining_count.toLocaleString()}`);

    totalProcessed += processed_count;

    // Stop if no more properties to process
    if (remaining_count === 0 || processed_count === 0) {
      console.log(`\n[COMPLETE] No more properties to process!`);
      break;
    }

    // Stop if remaining count isn't decreasing (stuck)
    if (lastRemaining !== -1 && remaining_count >= lastRemaining) {
      console.log(`\n[WARNING] Remaining count not decreasing - may be stuck`);
      break;
    }

    lastRemaining = remaining_count;

    // Show progress update every N calls
    if (callCount % CALLS_PER_UPDATE === 0) {
      const currentStats = await getDADECoverage();
      console.log('\n' + '-'.repeat(80));
      console.log(`[PROGRESS UPDATE] After ${callCount} calls:`);
      console.log(`  Total processed this session: ${totalProcessed.toLocaleString()}`);
      console.log(`  Current coverage: ${currentStats.withCode.toLocaleString()}/${currentStats.total.toLocaleString()} (${currentStats.coverage}%)`);
      console.log(`  Estimated calls remaining: ${Math.ceil(remaining_count / BATCH_SIZE)}`);
      console.log('-'.repeat(80));
    }

    // Small delay to be nice to the database
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  // Final stats
  console.log('\n' + '='.repeat(80));
  console.log('BATCH ASSIGNMENT COMPLETE');
  console.log('='.repeat(80));

  const finalStats = await getDADECoverage();

  console.log(`\nTotal calls made: ${callCount}`);
  console.log(`Total properties processed: ${totalProcessed.toLocaleString()}`);
  console.log(`\nFinal DADE Coverage:`);
  console.log(`  Total: ${finalStats.total.toLocaleString()}`);
  console.log(`  With Codes: ${finalStats.withCode.toLocaleString()}`);
  console.log(`  Coverage: ${finalStats.coverage}%`);
  console.log(`\nCompleted: ${new Date().toLocaleString()}`);
  console.log('='.repeat(80));

  // Grade the result
  const coverage = parseFloat(finalStats.coverage);
  let grade, status;

  if (coverage >= 99.5) {
    grade = '10/10';
    status = 'PERFECT';
  } else if (coverage >= 95) {
    grade = '9/10';
    status = 'EXCELLENT';
  } else if (coverage >= 90) {
    grade = '8/10';
    status = 'GOOD';
  } else if (coverage >= 80) {
    grade = '7/10';
    status = 'ACCEPTABLE';
  } else if (coverage >= 50) {
    grade = '6/10';
    status = 'NEEDS WORK';
  } else {
    grade = '5/10';
    status = 'INCOMPLETE';
  }

  console.log(`\nGRADE: ${grade} - ${status}`);
  console.log('='.repeat(80));
}

// Run it
main().catch(error => {
  console.error('\n[FATAL ERROR]', error);
  process.exit(1);
});