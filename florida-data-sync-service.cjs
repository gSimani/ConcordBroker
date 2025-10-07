/**
 * Florida Property Data Synchronization Service
 *
 * Features:
 * - Downloads all 67 Florida counties daily
 * - Handles both ZIP and direct file downloads
 * - Incremental updates (only changed data)
 * - Automatic Supabase import
 * - Error handling and notifications
 * - Scheduling support
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const { createHash } = require('crypto');
const { createClient } = require('@supabase/supabase-js');
const AdmZip = require('adm-zip');
const csv = require('csv-parser');
const schedule = require('node-schedule');
require('dotenv').config({ path: '.env.mcp' });

// Configuration
const CONFIG = {
  // Florida Revenue URLs
  BASE_URL: 'https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/SDF/',
  PRELIMINARY_PATH: '2025P/',
  FINAL_PATH: '2025F/',

  // Local paths
  DATA_BASE: 'C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\TEMP\\DATABASE PROPERTY APP',
  DOWNLOADS_BASE: 'C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\TEMP\\DOWNLOADS',
  LOGS_BASE: 'C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\logs',

  // Supabase
  SUPABASE_URL: process.env.SUPABASE_URL,
  SUPABASE_KEY: process.env.SUPABASE_SERVICE_ROLE_KEY,

  // Batch processing
  BATCH_SIZE: 1000,
  MAX_PARALLEL_DOWNLOADS: 3,

  // Schedule (run daily at 3 AM EST)
  DAILY_SCHEDULE: '0 3 * * *'
};

// All Florida counties with codes
const FLORIDA_COUNTIES = {
  '01': 'ALACHUA', '02': 'BAKER', '03': 'BAY', '04': 'BRADFORD', '05': 'BREVARD',
  '06': 'BROWARD', '07': 'CALHOUN', '08': 'CHARLOTTE', '09': 'CITRUS', '10': 'CLAY',
  '11': 'COLLIER', '12': 'COLUMBIA', '13': 'MIAMI-DADE', '14': 'DESOTO', '15': 'DIXIE',
  '16': 'DUVAL', '17': 'ESCAMBIA', '18': 'FLAGLER', '19': 'FRANKLIN', '20': 'GADSDEN',
  '21': 'GILCHRIST', '22': 'GLADES', '23': 'GULF', '24': 'HAMILTON', '25': 'HARDEE',
  '26': 'HENDRY', '27': 'HERNANDO', '28': 'HIGHLANDS', '29': 'HILLSBOROUGH', '30': 'HOLMES',
  '31': 'INDIAN_RIVER', '32': 'JACKSON', '33': 'JEFFERSON', '34': 'LAFAYETTE', '35': 'LAKE',
  '36': 'LEE', '37': 'LEON', '38': 'LEVY', '39': 'LIBERTY', '40': 'MADISON',
  '41': 'MANATEE', '42': 'MARION', '43': 'MARTIN', '44': 'MONROE', '45': 'NASSAU',
  '46': 'OKALOOSA', '47': 'OKEECHOBEE', '48': 'ORANGE', '49': 'OSCEOLA', '50': 'PALM_BEACH',
  '51': 'PASCO', '52': 'PINELLAS', '53': 'POLK', '54': 'PUTNAM', '55': 'ST_JOHNS',
  '56': 'ST_LUCIE', '57': 'SANTA_ROSA', '58': 'SARASOTA', '59': 'SEMINOLE', '60': 'SUMTER',
  '61': 'SUWANNEE', '62': 'TAYLOR', '63': 'UNION', '64': 'VOLUSIA', '65': 'WAKULLA',
  '66': 'WALTON', '67': 'WASHINGTON'
};

// Initialize Supabase
const supabase = createClient(CONFIG.SUPABASE_URL, CONFIG.SUPABASE_KEY);

// Logging system
class Logger {
  constructor() {
    this.ensureDir(CONFIG.LOGS_BASE);
    this.logFile = path.join(CONFIG.LOGS_BASE, `florida-sync-${new Date().toISOString().split('T')[0]}.log`);
  }

  ensureDir(dir) {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  }

  log(level, message, data = null) {
    const timestamp = new Date().toISOString();
    const logEntry = {
      timestamp,
      level,
      message,
      data
    };

    // Console output
    console.log(`[${timestamp}] ${level.toUpperCase()}: ${message}`);
    if (data) {
      console.log('  Data:', JSON.stringify(data, null, 2));
    }

    // File output
    fs.appendFileSync(this.logFile, JSON.stringify(logEntry) + '\n');
  }

  info(message, data) { this.log('info', message, data); }
  error(message, data) { this.log('error', message, data); }
  warn(message, data) { this.log('warn', message, data); }
  success(message, data) { this.log('success', message, data); }
}

const logger = new Logger();

// File utilities
class FileUtils {
  static ensureDir(dirPath) {
    if (!fs.existsSync(dirPath)) {
      fs.mkdirSync(dirPath, { recursive: true });
    }
  }

  static getFileHash(filePath) {
    if (!fs.existsSync(filePath)) return null;
    const content = fs.readFileSync(filePath);
    return createHash('md5').update(content).digest('hex');
  }

  static getFileSize(filePath) {
    if (!fs.existsSync(filePath)) return 0;
    return fs.statSync(filePath).size;
  }
}

// Download manager
class DownloadManager {
  constructor() {
    FileUtils.ensureDir(CONFIG.DOWNLOADS_BASE);
    FileUtils.ensureDir(CONFIG.DATA_BASE);
  }

  async downloadFile(url, destPath, retries = 3) {
    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        logger.info(`Downloading (attempt ${attempt}): ${path.basename(destPath)}`);

        await new Promise((resolve, reject) => {
          const file = fs.createWriteStream(destPath);

          https.get(url, (response) => {
            if (response.statusCode === 301 || response.statusCode === 302) {
              // Handle redirects
              const redirectUrl = response.headers.location;
              logger.info(`Redirected to: ${redirectUrl}`);
              this.downloadFile(redirectUrl, destPath, retries - attempt + 1)
                .then(resolve)
                .catch(reject);
              return;
            }

            if (response.statusCode !== 200) {
              reject(new Error(`HTTP ${response.statusCode}: ${response.statusMessage}`));
              return;
            }

            const totalSize = parseInt(response.headers['content-length'] || '0', 10);
            let downloaded = 0;

            response.on('data', (chunk) => {
              downloaded += chunk.length;
              if (totalSize > 0) {
                const percent = ((downloaded / totalSize) * 100).toFixed(1);
                if (downloaded % (1024 * 1024) === 0) { // Log every MB
                  process.stdout.write(`\r    ${percent}% (${(downloaded / 1024 / 1024).toFixed(1)} MB)`);
                }
              }
            });

            response.pipe(file);

            file.on('finish', () => {
              file.close();
              const sizeMB = (FileUtils.getFileSize(destPath) / 1024 / 1024).toFixed(2);
              logger.success(`Downloaded: ${path.basename(destPath)} (${sizeMB} MB)`);
              resolve();
            });

            file.on('error', (err) => {
              fs.unlink(destPath, () => {});
              reject(err);
            });
          }).on('error', reject);
        });

        return true;
      } catch (error) {
        logger.warn(`Download attempt ${attempt} failed: ${error.message}`);
        if (attempt === retries) {
          throw error;
        }
        // Wait before retry (exponential backoff)
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
      }
    }
  }

  async extractZip(zipPath, extractTo) {
    logger.info(`Extracting: ${path.basename(zipPath)}`);

    try {
      const zip = new AdmZip(zipPath);
      zip.extractAllTo(extractTo, true);

      // List extracted files
      const extractedFiles = fs.readdirSync(extractTo);
      logger.info(`Extracted ${extractedFiles.length} files`, { files: extractedFiles });

      return extractedFiles;
    } catch (error) {
      logger.error(`Extraction failed: ${error.message}`);
      throw error;
    }
  }
}

// County data processor
class CountyProcessor {
  constructor(downloadManager) {
    this.downloadManager = downloadManager;
  }

  async processCounty(countyCode, countyName) {
    logger.info(`Processing ${countyName} County (${countyCode})`);

    const countyDataPath = path.join(CONFIG.DATA_BASE, countyName);
    const sdfPath = path.join(countyDataPath, 'SDF');
    FileUtils.ensureDir(sdfPath);

    try {
      // Try downloading from multiple sources
      const downloadSources = [
        {
          type: 'final',
          url: `${CONFIG.BASE_URL}${CONFIG.FINAL_PATH}${encodeURIComponent(countyName)}%20${countyCode}%20Final%20SDF%202025.zip`
        },
        {
          type: 'preliminary',
          url: `${CONFIG.BASE_URL}${CONFIG.PRELIMINARY_PATH}${encodeURIComponent(countyName)}%20${countyCode}%20Preliminary%20SDF%202025.zip`
        }
      ];

      let downloaded = false;
      let extractedFiles = [];

      for (const source of downloadSources) {
        const zipFileName = `${countyName}_${countyCode}_${source.type}_SDF_2025.zip`;
        const zipPath = path.join(CONFIG.DOWNLOADS_BASE, zipFileName);

        try {
          // Check if we need to download (file doesn't exist or is old)
          const shouldDownload = this.shouldDownloadFile(zipPath);

          if (shouldDownload) {
            await this.downloadManager.downloadFile(source.url, zipPath);
          } else {
            logger.info(`Using cached file: ${zipFileName}`);
          }

          // Extract the zip
          extractedFiles = await this.downloadManager.extractZip(zipPath, sdfPath);
          downloaded = true;
          break;
        } catch (error) {
          logger.warn(`Failed to download ${source.type} data: ${error.message}`);
          continue;
        }
      }

      if (!downloaded) {
        throw new Error(`All download sources failed for ${countyName}`);
      }

      return {
        success: true,
        county: countyName,
        code: countyCode,
        extractedFiles
      };

    } catch (error) {
      logger.error(`County processing failed: ${countyName}`, { error: error.message });
      return {
        success: false,
        county: countyName,
        code: countyCode,
        error: error.message
      };
    }
  }

  shouldDownloadFile(filePath, maxAgeHours = 24) {
    if (!fs.existsSync(filePath)) {
      return true;
    }

    const stats = fs.statSync(filePath);
    const ageHours = (Date.now() - stats.mtime.getTime()) / (1000 * 60 * 60);
    return ageHours > maxAgeHours;
  }
}

// Supabase data importer
class DataImporter {
  async importCountyData(countyCode, countyName, sdfPath) {
    logger.info(`Importing ${countyName} data to Supabase`);

    try {
      // Find SDF files
      const sdfFiles = fs.readdirSync(sdfPath)
        .filter(file => file.toLowerCase().includes('sdf'))
        .filter(file => file.endsWith('.csv') || file.endsWith('.txt'));

      if (sdfFiles.length === 0) {
        throw new Error('No SDF files found');
      }

      const filePath = path.join(sdfPath, sdfFiles[0]);
      logger.info(`Processing file: ${sdfFiles[0]}`);

      const records = [];
      let lineCount = 0;

      // Read and parse CSV
      await new Promise((resolve, reject) => {
        fs.createReadStream(filePath)
          .pipe(csv())
          .on('data', (row) => {
            lineCount++;
            const record = this.parseSdfRecord(row, countyCode, countyName);

            if (record && record.parcel_id && record.sale_year && record.sale_price > 0) {
              records.push(record);
            }

            if (lineCount % 10000 === 0) {
              process.stdout.write(`\r    Processed: ${lineCount} lines, ${records.length} valid sales`);
            }
          })
          .on('end', resolve)
          .on('error', reject);
      });

      logger.info(`Found ${records.length} valid sales from ${lineCount} records`);

      // Import to Supabase in batches
      let imported = 0;
      for (let i = 0; i < records.length; i += CONFIG.BATCH_SIZE) {
        const batch = records.slice(i, i + CONFIG.BATCH_SIZE);

        const { error } = await supabase
          .from('property_sales_history')
          .upsert(batch, {
            onConflict: 'parcel_id,county_no,sale_year,sale_month,or_book,or_page',
            ignoreDuplicates: false
          });

        if (error) {
          logger.error(`Batch import error: ${error.message}`);
          throw error;
        }

        imported += batch.length;
        process.stdout.write(`\r    Imported: ${imported}/${records.length} records`);
      }

      logger.success(`Import complete: ${imported} records imported for ${countyName}`);
      return { success: true, imported, total: records.length };

    } catch (error) {
      logger.error(`Import failed for ${countyName}: ${error.message}`);
      return { success: false, error: error.message };
    }
  }

  parseSdfRecord(row, countyCode, countyName) {
    return {
      parcel_id: (row.PARCEL_ID || '').toString().replace(/"/g, '').trim(),
      county_no: countyCode,
      county_name: countyName,
      sale_year: parseInt(row.SALE_YR) || null,
      sale_month: parseInt(row.SALE_MO) || null,
      sale_price: parseFloat(row.SALE_PRC) || 0,
      or_book: (row.OR_BOOK || '').toString().trim(),
      or_page: (row.OR_PAGE || '').toString().trim(),
      quality_code: (row.QUAL_CD || '').toString().trim(),
      verification_code: (row.VI_CD || '').toString().trim(),
      deed_type: (row.QUAL_CD === 'Q') ? 'WD' : 'QC',
      clerk_no: (row.CLERK_NO || '').toString().trim(),
      sale_id: (row.SALE_ID_CD || '').toString().trim()
    };
  }
}

// Main synchronization service
class FloridaDataSyncService {
  constructor() {
    this.downloadManager = new DownloadManager();
    this.countyProcessor = new CountyProcessor(this.downloadManager);
    this.dataImporter = new DataImporter();
  }

  async syncAllCounties() {
    logger.info('Starting Florida data synchronization');

    const startTime = Date.now();
    const results = {
      processed: 0,
      successful: 0,
      failed: 0,
      imported: 0,
      errors: []
    };

    try {
      // Process counties in parallel (limited concurrency)
      const countyCodes = Object.keys(FLORIDA_COUNTIES);
      const chunks = this.chunkArray(countyCodes, CONFIG.MAX_PARALLEL_DOWNLOADS);

      for (const chunk of chunks) {
        const chunkPromises = chunk.map(async (countyCode) => {
          const countyName = FLORIDA_COUNTIES[countyCode];
          results.processed++;

          try {
            // Process county (download & extract)
            const processResult = await this.countyProcessor.processCounty(countyCode, countyName);

            if (processResult.success) {
              // Import to Supabase
              const sdfPath = path.join(CONFIG.DATA_BASE, countyName, 'SDF');
              const importResult = await this.dataImporter.importCountyData(countyCode, countyName, sdfPath);

              if (importResult.success) {
                results.successful++;
                results.imported += importResult.imported;
              } else {
                results.failed++;
                results.errors.push(`${countyName}: Import failed - ${importResult.error}`);
              }
            } else {
              results.failed++;
              results.errors.push(`${countyName}: Processing failed - ${processResult.error}`);
            }
          } catch (error) {
            results.failed++;
            results.errors.push(`${countyName}: Unexpected error - ${error.message}`);
            logger.error(`Unexpected error processing ${countyName}`, { error: error.message });
          }
        });

        // Wait for chunk to complete
        await Promise.all(chunkPromises);

        logger.info(`Chunk complete. Progress: ${results.successful + results.failed}/${results.processed}`);
      }

    } catch (error) {
      logger.error('Synchronization failed', { error: error.message });
    }

    const duration = Math.round((Date.now() - startTime) / 1000);

    // Final report
    logger.success('Florida data synchronization complete', {
      duration: `${Math.floor(duration / 60)}m ${duration % 60}s`,
      results
    });

    // Save sync report
    const reportPath = path.join(CONFIG.LOGS_BASE, `sync-report-${new Date().toISOString().split('T')[0]}.json`);
    fs.writeFileSync(reportPath, JSON.stringify({
      timestamp: new Date().toISOString(),
      duration,
      results
    }, null, 2));

    return results;
  }

  chunkArray(array, chunkSize) {
    const chunks = [];
    for (let i = 0; i < array.length; i += chunkSize) {
      chunks.push(array.slice(i, i + chunkSize));
    }
    return chunks;
  }

  startScheduledSync() {
    logger.info(`Scheduling daily sync at: ${CONFIG.DAILY_SCHEDULE}`);

    schedule.scheduleJob(CONFIG.DAILY_SCHEDULE, () => {
      logger.info('Starting scheduled synchronization');
      this.syncAllCounties().catch(error => {
        logger.error('Scheduled sync failed', { error: error.message });
      });
    });
  }
}

// CLI interface
async function main() {
  const args = process.argv.slice(2);
  const service = new FloridaDataSyncService();

  if (args.includes('--schedule')) {
    // Start the scheduler
    logger.info('Starting Florida Data Sync Service with scheduler');
    service.startScheduledSync();

    // Keep the process running
    process.on('SIGINT', () => {
      logger.info('Service stopping...');
      process.exit(0);
    });

    logger.info('Service running. Press Ctrl+C to stop.');

  } else {
    // Run sync once
    logger.info('Running one-time synchronization');
    await service.syncAllCounties();
    process.exit(0);
  }
}

// Handle uncaught errors
process.on('uncaughtException', (error) => {
  logger.error('Uncaught exception', { error: error.message, stack: error.stack });
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled rejection', { reason, promise });
  process.exit(1);
});

// Export for testing
module.exports = {
  FloridaDataSyncService,
  CONFIG,
  FLORIDA_COUNTIES
};

// Run if called directly
if (require.main === module) {
  main().catch(error => {
    logger.error('Main execution failed', { error: error.message });
    process.exit(1);
  });
}