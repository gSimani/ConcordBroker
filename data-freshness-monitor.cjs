/**
 * Florida Data Freshness Monitor
 *
 * Monitors the freshness of Florida property data and alerts when updates are needed
 */

const fs = require('fs');
const path = require('path');
const { createClient } = require('@supabase/supabase-js');
require('dotenv').config({ path: '.env.mcp' });

const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);

const CONFIG = {
  DATA_BASE: 'C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\TEMP\\DATABASE PROPERTY APP',
  LOGS_BASE: 'C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\logs',
  MAX_AGE_HOURS: 24, // Alert if data is older than 24 hours
  ALERT_EMAIL: null, // Configure for email alerts
};

// Create monitoring dashboard
async function generateDataFreshnessDashboard() {
  console.log('🔍 Florida Data Freshness Monitor');
  console.log('='.repeat(50));

  const report = {
    timestamp: new Date().toISOString(),
    counties: {},
    summary: {
      total: 67,
      fresh: 0,
      stale: 0,
      missing: 0,
      lastSync: null
    },
    database: {
      totalRecords: 0,
      latestSale: null,
      oldestSale: null
    }
  };

  // Check file freshness
  console.log('\n📁 Checking local file freshness...');

  const counties = fs.readdirSync(CONFIG.DATA_BASE, { withFileTypes: true })
    .filter(dirent => dirent.isDirectory())
    .map(dirent => dirent.name);

  for (const county of counties) {
    const sdfPath = path.join(CONFIG.DATA_BASE, county, 'SDF');

    if (!fs.existsSync(sdfPath)) {
      report.counties[county] = { status: 'missing', lastUpdate: null };
      report.summary.missing++;
      continue;
    }

    const files = fs.readdirSync(sdfPath);
    if (files.length === 0) {
      report.counties[county] = { status: 'missing', lastUpdate: null };
      report.summary.missing++;
      continue;
    }

    // Get newest file modification time
    let newestTime = 0;
    for (const file of files) {
      const filePath = path.join(sdfPath, file);
      const stats = fs.statSync(filePath);
      newestTime = Math.max(newestTime, stats.mtime.getTime());
    }

    const ageHours = (Date.now() - newestTime) / (1000 * 60 * 60);
    const status = ageHours > CONFIG.MAX_AGE_HOURS ? 'stale' : 'fresh';

    report.counties[county] = {
      status,
      lastUpdate: new Date(newestTime).toISOString(),
      ageHours: Math.round(ageHours * 10) / 10,
      files: files.length
    };

    if (status === 'fresh') {
      report.summary.fresh++;
    } else {
      report.summary.stale++;
    }
  }

  // Check database stats
  console.log('\n🗄️  Checking database statistics...');

  try {
    const { count } = await supabase
      .from('property_sales_history')
      .select('*', { count: 'exact', head: true });

    const { data: latestSale } = await supabase
      .from('property_sales_history')
      .select('sale_date, county_name, sale_price')
      .order('created_at', { ascending: false })
      .limit(1);

    const { data: oldestSale } = await supabase
      .from('property_sales_history')
      .select('sale_date, county_name, sale_price')
      .order('created_at', { ascending: true })
      .limit(1);

    report.database.totalRecords = count || 0;
    report.database.latestSale = latestSale?.[0] || null;
    report.database.oldestSale = oldestSale?.[0] || null;

  } catch (error) {
    console.error('Database check failed:', error.message);
    report.database.error = error.message;
  }

  // Display report
  console.log('\n📊 DATA FRESHNESS REPORT');
  console.log('='.repeat(50));
  console.log(`📅 Generated: ${new Date().toLocaleString()}`);
  console.log(`🏢 Counties: ${report.summary.fresh} fresh, ${report.summary.stale} stale, ${report.summary.missing} missing`);
  console.log(`🗄️  Database: ${report.database.totalRecords.toLocaleString()} total records`);

  if (report.database.latestSale) {
    console.log(`📈 Latest Sale: ${report.database.latestSale.sale_date} - $${report.database.latestSale.sale_price.toLocaleString()} (${report.database.latestSale.county_name})`);
  }

  console.log('\n🚨 ALERTS:');
  if (report.summary.stale > 0) {
    console.log(`⚠️  ${report.summary.stale} counties have stale data (>24h old)`);
  }
  if (report.summary.missing > 0) {
    console.log(`❌ ${report.summary.missing} counties are missing SDF files`);
  }
  if (report.summary.stale === 0 && report.summary.missing === 0) {
    console.log('✅ All data is fresh and up to date!');
  }

  // Show stale counties
  if (report.summary.stale > 0) {
    console.log('\n⏰ STALE COUNTIES:');
    Object.entries(report.counties)
      .filter(([_, data]) => data.status === 'stale')
      .sort((a, b) => b[1].ageHours - a[1].ageHours)
      .slice(0, 10)
      .forEach(([county, data]) => {
        console.log(`   ${county}: ${data.ageHours}h old (${data.lastUpdate})`);
      });
  }

  // Save report
  const reportPath = path.join(CONFIG.LOGS_BASE, `freshness-report-${new Date().toISOString().split('T')[0]}.json`);
  if (!fs.existsSync(CONFIG.LOGS_BASE)) {
    fs.mkdirSync(CONFIG.LOGS_BASE, { recursive: true });
  }
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

  console.log(`\n📋 Report saved: ${reportPath}`);

  return report;
}

// Quick status check
async function quickStatus() {
  try {
    const { count } = await supabase
      .from('property_sales_history')
      .select('*', { count: 'exact', head: true });

    const { data: recentSales } = await supabase
      .from('property_sales_history')
      .select('created_at')
      .order('created_at', { ascending: false })
      .limit(1);

    const lastUpdate = recentSales?.[0]?.created_at;
    const hoursAgo = lastUpdate ? Math.round((Date.now() - new Date(lastUpdate).getTime()) / (1000 * 60 * 60)) : null;

    console.log('🔍 Quick Status Check');
    console.log('='.repeat(30));
    console.log(`📊 Total Records: ${count?.toLocaleString() || 'N/A'}`);
    console.log(`⏰ Last Update: ${lastUpdate ? `${hoursAgo}h ago` : 'Unknown'}`);

    if (hoursAgo > 24) {
      console.log('🚨 Data may be stale - consider running sync');
    } else {
      console.log('✅ Data appears fresh');
    }

  } catch (error) {
    console.error('Status check failed:', error.message);
  }
}

// Main CLI
async function main() {
  const args = process.argv.slice(2);

  if (args.includes('--quick')) {
    await quickStatus();
  } else {
    await generateDataFreshnessDashboard();
  }
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = { generateDataFreshnessDashboard, quickStatus };