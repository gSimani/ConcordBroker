/**
 * Florida Data Sync Service (FIXED VERSION)
 *
 * Downloads and imports Florida property data with correct URL patterns
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const schedule = require('node-schedule');
const AdmZip = require('adm-zip');
const csv = require('csv-parser');
const { createClient } = require('@supabase/supabase-js');

require('dotenv').config({ path: '.env.mcp' });

// Supabase configuration
const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
);

// Configuration
const CONFIG = {
  DOWNLOAD_BASE: 'C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\TEMP\\DOWNLOADS',
  EXTRACT_BASE: 'C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\TEMP\\DATABASE PROPERTY APP',
  LOGS_BASE: 'C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\logs',
  DAILY_SCHEDULE: '0 3 * * *', // 3:00 AM EST daily
  MAX_CONCURRENT: 3,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 2000,
  BATCH_SIZE: 1000
};

// County mapping with correct codes for URL construction
const FLORIDA_COUNTIES = {
  'ALACHUA': '01', 'BAKER': '02', 'BAY': '03', 'BRADFORD': '04', 'BREVARD': '05',
  'BROWARD': '16', 'CALHOUN': '07', 'CHARLOTTE': '08', 'CITRUS': '09', 'CLAY': '10',
  'COLLIER': '11', 'COLUMBIA': '12', 'MIAMI-DADE': '13', 'DESOTO': '14', 'DIXIE': '15',
  'DUVAL': '06', 'ESCAMBIA': '17', 'FLAGLER': '18', 'FRANKLIN': '19', 'GADSDEN': '20',
  'GILCHRIST': '21', 'GLADES': '22', 'GULF': '23', 'HAMILTON': '24', 'HARDEE': '25',
  'HENDRY': '26', 'HERNANDO': '27', 'HIGHLANDS': '28', 'HILLSBOROUGH': '29',
  'HOLMES': '30', 'INDIAN RIVER': '31', 'JACKSON': '32', 'JEFFERSON': '33',
  'LAFAYETTE': '34', 'LAKE': '35', 'LEE': '36', 'LEON': '37', 'LEVY': '38',
  'LIBERTY': '39', 'MADISON': '40', 'MANATEE': '41', 'MARION': '42', 'MARTIN': '43',
  'MONROE': '44', 'NASSAU': '45', 'OKALOOSA': '46', 'OKEECHOBEE': '47', 'ORANGE': '48',
  'OSCEOLA': '49', 'PALM BEACH': '50', 'PASCO': '51', 'PINELLAS': '52', 'POLK': '53',
  'PUTNAM': '54', 'ST. JOHNS': '55', 'ST. LUCIE': '56', 'SANTA ROSA': '57',
  'SARASOTA': '58', 'SEMINOLE': '59', 'SUMTER': '60', 'SUWANNEE': '61', 'TAYLOR': '62',
  'UNION': '63', 'VOLUSIA': '64', 'WAKULLA': '65', 'WALTON': '66', 'WASHINGTON': '67'
};

class FloridaDataSyncService {
  constructor() {
    this.logger = this.createLogger();
    this.ensure_directories();
  }

  createLogger() {
    return {
      info: (msg, data = null) => {
        const timestamp = new Date().toISOString();
        const logMsg = data ? `[${timestamp}] INFO: ${msg}\n  Data: ${JSON.stringify(data, null, 2)}` : `[${timestamp}] INFO: ${msg}`;
        console.log(logMsg);
        this.writeLog('info', msg, data);
      },
      warn: (msg, data = null) => {
        const timestamp = new Date().toISOString();
        const logMsg = data ? `[${timestamp}] WARN: ${msg}\n  Data: ${JSON.stringify(data, null, 2)}` : `[${timestamp}] WARN: ${msg}`;
        console.log(logMsg);
        this.writeLog('warn', msg, data);
      },
      error: (msg, data = null) => {
        const timestamp = new Date().toISOString();
        const logMsg = data ? `[${timestamp}] ERROR: ${msg}\n  Data: ${JSON.stringify(data, null, 2)}` : `[${timestamp}] ERROR: ${msg}`;
        console.error(logMsg);
        this.writeLog('error', msg, data);
      },
      success: (msg, data = null) => {
        const timestamp = new Date().toISOString();
        const logMsg = data ? `[${timestamp}] SUCCESS: ${msg}` : `[${timestamp}] SUCCESS: ${msg}`;
        console.log(logMsg);
        this.writeLog('success', msg, data);
      }
    };
  }

  writeLog(level, message, data) {
    if (!fs.existsSync(CONFIG.LOGS_BASE)) {
      fs.mkdirSync(CONFIG.LOGS_BASE, { recursive: true });
    }

    const logFile = path.join(CONFIG.LOGS_BASE, `sync-${new Date().toISOString().split('T')[0]}.log`);
    const logEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      data: data || null
    };

    fs.appendFileSync(logFile, JSON.stringify(logEntry) + '\n');
  }

  ensure_directories() {
    [CONFIG.DOWNLOAD_BASE, CONFIG.EXTRACT_BASE, CONFIG.LOGS_BASE].forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    });
  }

  // Generate correct download URLs using Florida DOR patterns
  generateDownloadUrls(county, countyCode, fileType = 'SDF') {
    const baseUrl = `https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/${fileType}/2025P`;

    // Convert county name to proper format for URLs
    let countyName = county;
    if (county === 'MIAMI-DADE') countyName = 'Miami-Dade';
    else if (county === 'ST. JOHNS') countyName = 'St.%20Johns';
    else if (county === 'ST. LUCIE') countyName = 'St.%20Lucie';
    else if (county === 'SANTA ROSA') countyName = 'Santa%20Rosa';
    else if (county === 'INDIAN RIVER') countyName = 'Indian%20River';
    else {
      // Convert to proper case for other counties
      countyName = county.charAt(0).toUpperCase() + county.slice(1).toLowerCase();
    }

    // URL encode spaces as %20
    const encodedCountyName = countyName.replace(/ /g, '%20');

    // Correct Florida DOR filename pattern
    const filename = `${encodedCountyName}%20${countyCode}%20Preliminary%20${fileType}%202025.zip`;

    return [
      {
        type: 'preliminary',
        url: `${baseUrl}/${filename}`,
        filename: filename.replace(/%20/g, ' '), // Clean filename for local storage
        localPath: path.join(CONFIG.DOWNLOAD_BASE, filename.replace(/%20/g, '_'))
      }
    ];
  }

  // Download file with retry logic
  async downloadFile(url, localPath, attempt = 1) {
    return new Promise((resolve, reject) => {
      const file = fs.createWriteStream(localPath);

      https.get(url, (response) => {
        if (response.statusCode === 200) {
          response.pipe(file);
          file.on('finish', () => {
            file.close();
            const stats = fs.statSync(localPath);

            // Check if file is actually a valid ZIP (not an HTML error page)
            if (stats.size < 50000) { // Files smaller than 50KB are likely error pages
              const content = fs.readFileSync(localPath, 'utf8');
              if (content.includes('<!DOCTYPE html') || content.includes('<html>')) {
                fs.unlinkSync(localPath); // Delete HTML error file
                reject(new Error(`Downloaded HTML error page instead of ZIP file`));
                return;
              }
            }

            resolve(stats.size);
          });
          file.on('error', (err) => {
            fs.unlink(localPath, () => {});
            reject(err);
          });
        } else {
          file.close();
          fs.unlink(localPath, () => {});
          reject(new Error(`HTTP ${response.statusCode}: ${response.statusMessage}`));
        }
      }).on('error', (err) => {
        file.close();
        fs.unlink(localPath, () => {});
        reject(err);
      });
    });
  }

  // Extract ZIP file
  async extractZip(zipPath, extractDir) {
    try {
      const zip = new AdmZip(zipPath);
      zip.extractAllTo(extractDir, true);
      this.logger.success(`Extracted: ${path.basename(zipPath)}`);
      return true;
    } catch (error) {
      this.logger.error(`Extraction failed: ${error.message}`);
      throw error;
    }
  }

  // Process a single county
  async processCounty(county, countyCode) {
    this.logger.info(`Processing ${county} County (${countyCode})`);

    const urls = this.generateDownloadUrls(county, countyCode);

    for (const { type, url, localPath } of urls) {
      let attempt = 1;
      let success = false;

      while (attempt <= CONFIG.RETRY_ATTEMPTS && !success) {
        try {
          this.logger.info(`Downloading (attempt ${attempt}): ${path.basename(localPath)}`);

          const fileSize = await this.downloadFile(url, localPath, attempt);
          this.logger.success(`Downloaded: ${path.basename(localPath)} (${(fileSize / 1024 / 1024).toFixed(2)} MB)`);

          // Extract ZIP file
          const countyDir = path.join(CONFIG.EXTRACT_BASE, county);
          const sdfDir = path.join(countyDir, 'SDF');

          if (!fs.existsSync(sdfDir)) {
            fs.mkdirSync(sdfDir, { recursive: true });
          }

          this.logger.info(`Extracting: ${path.basename(localPath)}`);
          await this.extractZip(localPath, sdfDir);

          // Import to database
          await this.importSdfToDatabase(county, countyCode, sdfDir);

          success = true;

        } catch (error) {
          this.logger.warn(`Download attempt ${attempt} failed: ${error.message}`);

          if (attempt < CONFIG.RETRY_ATTEMPTS) {
            await new Promise(resolve => setTimeout(resolve, CONFIG.RETRY_DELAY * attempt));
          }
          attempt++;
        }
      }

      if (success) {
        return { county, status: 'success' };
      }
    }

    throw new Error(`All download sources failed for ${county}`);
  }

  // Import SDF data to Supabase
  async importSdfToDatabase(county, countyCode, sdfDir) {
    const csvFiles = fs.readdirSync(sdfDir).filter(file => file.toLowerCase().endsWith('.csv'));

    if (csvFiles.length === 0) {
      this.logger.warn(`No CSV files found in ${sdfDir}`);
      return;
    }

    for (const csvFile of csvFiles) {
      const csvPath = path.join(sdfDir, csvFile);
      this.logger.info(`Importing: ${csvFile}`);

      const records = [];

      await new Promise((resolve, reject) => {
        fs.createReadStream(csvPath)
          .pipe(csv())
          .on('data', (row) => {
            // Parse SDF record
            const record = this.parseSdfRecord(row, countyCode, county);
            if (record.parcel_id && record.sale_year && record.sale_price > 0) {
              records.push(record);
            }
          })
          .on('end', resolve)
          .on('error', reject);
      });

      if (records.length > 0) {
        this.logger.info(`Importing ${records.length} records to Supabase`);

        // Import in batches
        for (let i = 0; i < records.length; i += CONFIG.BATCH_SIZE) {
          const batch = records.slice(i, i + CONFIG.BATCH_SIZE);

          const { error } = await supabase
            .from('property_sales_history')
            .upsert(batch, {
              onConflict: 'parcel_id,county_no,sale_year,sale_month,sale_id',
              ignoreDuplicates: true
            });

          if (error) {
            this.logger.error(`Batch import failed: ${error.message}`);
          } else {
            this.logger.info(`Imported batch: ${i + batch.length}/${records.length}`);
          }
        }
      }
    }
  }

  // Parse SDF record from CSV
  parseSdfRecord(row, countyCode, countyName) {
    return {
      parcel_id: (row.PARCEL_ID || '').toString().replace(/"/g, '').trim(),
      county_no: countyCode,
      county_name: countyName,
      sale_year: parseInt(row.SALE_YR) || null,
      sale_month: parseInt(row.SALE_MO) || null,
      sale_day: null,
      sale_price: parseFloat(row.SALE_PRC) || 0,
      or_book: (row.OR_BOOK || '').toString().trim(),
      or_page: (row.OR_PAGE || '').toString().trim(),
      clerk_no: (row.CLERK_NO || '').toString().trim(),
      quality_code: (row.QUAL_CD || '').toString().trim(),
      verification_code: (row.VI_CD || '').toString().trim(),
      deed_type: (row.QUAL_CD === 'Q') ? 'WD' : 'QC',
      multi_parcel_sale: (row.MULTI_PAR_SAL || '').toString().trim(),
      sale_id: (row.SALE_ID_CD || '').toString().trim(),
      sale_change_code: (row.SAL_CHG_CD || '').toString().trim(),
      state_parcel_id: (row.STATE_PARCEL_ID || '').toString().trim()
    };
  }

  // Process counties in chunks with limited concurrency
  async syncAllCounties() {
    this.logger.info('Starting Florida data synchronization');

    const counties = Object.entries(FLORIDA_COUNTIES);
    const chunkSize = CONFIG.MAX_CONCURRENT;
    const results = [];

    for (let i = 0; i < counties.length; i += chunkSize) {
      const chunk = counties.slice(i, i + chunkSize);

      const chunkPromises = chunk.map(async ([county, code]) => {
        try {
          const result = await this.processCounty(county, code);
          return result;
        } catch (error) {
          this.logger.error(`County processing failed: ${county}`, { error: error.message });
          return { county, status: 'failed', error: error.message };
        }
      });

      const chunkResults = await Promise.all(chunkPromises);
      results.push(...chunkResults);

      this.logger.info(`Chunk complete. Progress: ${Math.min(i + chunkSize, counties.length)}/${counties.length}`);
    }

    // Generate summary report
    const successful = results.filter(r => r.status === 'success').length;
    const failed = results.filter(r => r.status === 'failed').length;

    this.logger.info('Synchronization complete!', {
      total: counties.length,
      successful,
      failed,
      successRate: `${Math.round((successful / counties.length) * 100)}%`
    });

    return results;
  }

  // Start scheduled synchronization
  startScheduledSync() {
    this.logger.info('Starting scheduled Florida data sync service');
    this.logger.info(`Schedule: Daily at 3:00 AM EST (${CONFIG.DAILY_SCHEDULE})`);

    const job = schedule.scheduleJob(CONFIG.DAILY_SCHEDULE, async () => {
      this.logger.info('Scheduled sync starting...');
      try {
        await this.syncAllCounties();
        this.logger.success('Scheduled sync completed successfully');
      } catch (error) {
        this.logger.error('Scheduled sync failed', { error: error.message });
      }
    });

    this.logger.info('Sync service is now running. Press Ctrl+C to stop.');

    // Keep process alive
    process.on('SIGINT', () => {
      this.logger.info('Stopping sync service...');
      job.destroy();
      process.exit(0);
    });

    return job;
  }
}

// CLI interface
async function main() {
  const service = new FloridaDataSyncService();
  const args = process.argv.slice(2);

  if (args.includes('--schedule')) {
    service.startScheduledSync();
  } else if (args.includes('--test-broward')) {
    // Test with just Broward county (known to work)
    console.log('Testing sync service with Broward County only...');
    try {
      const result = await service.processCounty('BROWARD', '16');
      console.log('Test result:', result);
    } catch (error) {
      console.error('Test failed:', error.message);
    }
  } else {
    console.log('Running one-time synchronization');
    await service.syncAllCounties();
  }
}

if (require.main === module) {
  main().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

module.exports = { FloridaDataSyncService };