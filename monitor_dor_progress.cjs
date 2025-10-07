/**
 * Real-Time DOR Code Assignment Progress Monitor
 * Shows live coverage percentage and grade updates
 */

const { createClient } = require('@supabase/supabase-js');

// Configuration
const SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co';
const SUPABASE_SERVICE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0';

const TARGET_COUNTY = 'DADE';
const REFRESH_INTERVAL = 10000; // Check every 10 seconds

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

function clearScreen() {
  process.stdout.write('\x1Bc'); // Clear console
}

function getGrade(coverage) {
  if (coverage >= 99.5) return { grade: '10/10', status: 'PERFECT', color: '\x1b[32m' };
  if (coverage >= 95) return { grade: '9/10', status: 'EXCELLENT', color: '\x1b[32m' };
  if (coverage >= 90) return { grade: '8/10', status: 'GOOD', color: '\x1b[36m' };
  if (coverage >= 80) return { grade: '7/10', status: 'ACCEPTABLE', color: '\x1b[33m' };
  if (coverage >= 50) return { grade: '6/10', status: 'NEEDS WORK', color: '\x1b[33m' };
  return { grade: '5/10', status: 'INCOMPLETE', color: '\x1b[31m' };
}

function getProgressBar(percentage, width = 50) {
  const filled = Math.round((percentage / 100) * width);
  const empty = width - filled;
  return '[' + '█'.repeat(filled) + '░'.repeat(empty) + ']';
}

async function getStats() {
  try {
    // Total
    const { count: total } = await supabase
      .from('florida_parcels')
      .select('*', { count: 'exact', head: true })
      .eq('year', 2025)
      .eq('county', TARGET_COUNTY);

    // With codes
    const { count: withCode } = await supabase
      .from('florida_parcels')
      .select('*', { count: 'exact', head: true })
      .eq('year', 2025)
      .eq('county', TARGET_COUNTY)
      .not('land_use_code', 'is', null)
      .neq('land_use_code', '')
      .neq('land_use_code', '99');

    // NULL/empty/99
    const { count: nullCount } = await supabase
      .from('florida_parcels')
      .select('*', { count: 'exact', head: true })
      .eq('year', 2025)
      .eq('county', TARGET_COUNTY)
      .is('land_use_code', null);

    const { count: emptyCount } = await supabase
      .from('florida_parcels')
      .select('*', { count: 'exact', head: true })
      .eq('year', 2025)
      .eq('county', TARGET_COUNTY)
      .eq('land_use_code', '');

    const { count: code99Count } = await supabase
      .from('florida_parcels')
      .select('*', { count: 'exact', head: true })
      .eq('year', 2025)
      .eq('county', TARGET_COUNTY)
      .eq('land_use_code', '99');

    const remaining = (nullCount || 0) + (emptyCount || 0) + (code99Count || 0);
    const coverage = total > 0 ? (withCode / total * 100) : 0;

    return { total, withCode, remaining, coverage };
  } catch (error) {
    return null;
  }
}

async function displayDashboard() {
  const stats = await getStats();

  if (!stats) {
    console.log('\n[ERROR] Failed to fetch stats from database\n');
    return;
  }

  const { total, withCode, remaining, coverage } = stats;
  const { grade, status, color } = getGrade(coverage);
  const progressBar = getProgressBar(coverage);
  const reset = '\x1b[0m';

  clearScreen();

  console.log('╔════════════════════════════════════════════════════════════════════════════╗');
  console.log('║                   DOR CODE ASSIGNMENT - LIVE MONITOR                      ║');
  console.log('╚════════════════════════════════════════════════════════════════════════════╝');
  console.log('');
  console.log(`  County: ${TARGET_COUNTY}`);
  console.log(`  Last Updated: ${new Date().toLocaleTimeString()}`);
  console.log('');
  console.log('────────────────────────────────────────────────────────────────────────────');
  console.log('  COVERAGE STATUS');
  console.log('────────────────────────────────────────────────────────────────────────────');
  console.log('');
  console.log(`  ${progressBar}  ${coverage.toFixed(2)}%`);
  console.log('');
  console.log(`  ${color}${grade} - ${status}${reset}`);
  console.log('');
  console.log('────────────────────────────────────────────────────────────────────────────');
  console.log('  STATISTICS');
  console.log('────────────────────────────────────────────────────────────────────────────');
  console.log('');
  console.log(`  Total Properties:        ${total.toLocaleString().padStart(12)}`);
  console.log(`  With DOR Codes:          ${withCode.toLocaleString().padStart(12)}`);
  console.log(`  Still Missing:           ${remaining.toLocaleString().padStart(12)}`);
  console.log('');
  console.log('────────────────────────────────────────────────────────────────────────────');
  console.log('  PROGRESS ESTIMATE');
  console.log('────────────────────────────────────────────────────────────────────────────');
  console.log('');

  const processed = withCode - 572621; // Starting point was 572,621
  const batchesCompleted = Math.floor(processed / 5000);
  const batchesRemaining = Math.ceil(remaining / 5000);
  const minutesRemaining = batchesRemaining * 1;

  console.log(`  Batches Completed:       ${batchesCompleted.toLocaleString().padStart(12)}`);
  console.log(`  Batches Remaining:       ${batchesRemaining.toLocaleString().padStart(12)}`);
  console.log(`  Est. Time Remaining:     ${minutesRemaining} minutes`);
  console.log('');
  console.log('────────────────────────────────────────────────────────────────────────────');
  console.log('');
  console.log('  Press Ctrl+C to stop monitoring');
  console.log('');
  console.log('════════════════════════════════════════════════════════════════════════════');
}

async function main() {
  console.log('\n🚀 Starting real-time DOR assignment monitor...\n');
  console.log('   Refreshing every 10 seconds\n');

  // Initial display
  await displayDashboard();

  // Update every 10 seconds
  setInterval(async () => {
    await displayDashboard();
  }, REFRESH_INTERVAL);
}

// Handle Ctrl+C gracefully
process.on('SIGINT', () => {
  console.log('\n\n✓ Monitor stopped\n');
  process.exit(0);
});

main().catch(error => {
  console.error('\n[FATAL ERROR]', error);
  process.exit(1);
});