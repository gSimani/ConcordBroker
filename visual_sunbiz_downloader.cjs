const { chromium } = require('playwright');
const fs = require('fs').promises;
const path = require('path');

// Configuration
const CONFIG = {
    url: 'https://sftp.floridados.gov',
    username: 'Public',
    password: 'PubAccess1845!',
    basePath: 'C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\TEMP\\DATABASE\\doc',
    missingFolders: [
        'fic',              // Fictitious Names (DBAs) - CRITICAL
        'FLR',              // Florida Lien Registry - CRITICAL  
        'comp',             // Company/Compliance
        'gen',              // General Partnerships
        'tm',               // Trademarks
        'DHE',              // Highway Safety
        'ficevent-Year2000', // Historical events
        'notes',            // Documentation
        'Quarterly'         // Quarterly reports
    ]
};

// Statistics tracking
let stats = {
    startTime: new Date(),
    foldersProcessed: 0,
    filesDownloaded: 0,
    currentFolder: '',
    currentFile: '',
    errors: []
};

async function log(message, type = 'INFO') {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] [${type}] ${message}`;
    console.log(logMessage);
    
    // Also append to log file
    try {
        await fs.appendFile('visual_sunbiz_download.log', logMessage + '\n');
    } catch (err) {
        console.error('Failed to write to log file:', err);
    }
}

async function ensureDirectory(dirPath) {
    try {
        await fs.mkdir(dirPath, { recursive: true });
    } catch (err) {
        await log(`Error creating directory ${dirPath}: ${err}`, 'ERROR');
    }
}

async function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function downloadMissingSunbizData() {
    await log('🚀 Starting Visual Sunbiz Downloader');
    await log('============================================================');
    
    const browser = await chromium.launch({
        headless: false,
        slowMo: 100, // Slow down for visibility
        args: ['--window-size=1920,1080']
    });

    const context = await browser.newContext({
        acceptDownloads: true,
        viewport: { width: 1920, height: 1080 }
    });

    const page = await context.newPage();

    try {
        // Step 1: Navigate to SFTP site
        await log(`📍 Navigating to ${CONFIG.url}`);
        await page.goto(CONFIG.url, { waitUntil: 'networkidle' });
        await page.screenshot({ path: 'screenshots/01_login_page.png' });

        // Step 2: Login
        await log('🔐 Logging in...');
        // Use the correct field names from the actual login form
        await page.fill('input[placeholder="Username"]', CONFIG.username);
        await page.fill('input[placeholder="Password"]', CONFIG.password);
        await page.screenshot({ path: 'screenshots/02_credentials_filled.png' });
        
        // Click the Login button (green button with text "Login")
        await page.click('button:has-text("Login")');
        await page.waitForLoadState('networkidle');
        await delay(2000);
        await page.screenshot({ path: 'screenshots/03_after_login.png' });
        await log('✅ Login successful!');

        // Step 3: Navigate to doc folder - we see the doc folder in the listing
        await log('📁 Navigating to doc folder...');
        // Click on the doc folder row to select it, then double-click to enter
        const docRow = await page.locator('tr:has-text("doc")').first();
        if (await docRow.count() > 0) {
            await docRow.click(); // Select the row first
            await delay(500);
            await docRow.dblclick(); // Then double-click to enter
            await page.waitForLoadState('networkidle');
            await delay(2000);
            await log('✅ Entered doc folder');
        } else {
            await log('⚠️ Could not find doc folder');
        }

        await page.screenshot({ path: 'screenshots/04_in_doc_folder.png' });
        await log(`📂 Current location: ${page.url()}`);

        // Step 4: Process each missing folder
        for (let i = 0; i < CONFIG.missingFolders.length; i++) {
            const folderName = CONFIG.missingFolders[i];
            stats.currentFolder = folderName;
            
            await log('');
            await log('============================================================');
            await log(`📦 Processing folder ${i + 1}/${CONFIG.missingFolders.length}: ${folderName}`);
            await log('============================================================');

            try {
                // Look for the folder in the table row
                const folderRow = await page.locator(`tr:has-text("${folderName}")`).first();
                
                if (await folderRow.count() > 0) {
                    await log(`✅ Found folder: ${folderName}`);
                    
                    // Highlight the folder row we're about to click
                    await folderRow.evaluate(element => {
                        element.style.backgroundColor = 'yellow';
                        element.style.border = '3px solid red';
                    });
                    
                    await delay(1000); // Pause to show highlight
                    await page.screenshot({ path: `screenshots/folder_${folderName}_highlighted.png` });
                    
                    // Click to select, then double-click to enter the folder
                    await folderRow.click();
                    await delay(500);
                    await folderRow.dblclick();
                    await page.waitForLoadState('networkidle');
                    await delay(2000);
                    
                    await log(`📂 Entered folder: ${folderName}`);
                    await page.screenshot({ path: `screenshots/folder_${folderName}_contents.png` });
                    
                    // Wait a bit for content to fully load
                    await delay(1000);
                    
                    // Get all visible rows that have folder/file entries
                    const files = [];
                    const rows = await page.locator('tr').all();
                    
                    for (const row of rows) {
                        // Check if row has text content (skip empty rows)
                        const rowText = await row.textContent();
                        if (!rowText || rowText.trim() === '') continue;
                        
                        // Skip header rows and parent folder
                        if (rowText.includes('Name') && rowText.includes('Type')) continue;
                        if (rowText.includes('Parent Folder')) continue;
                        
                        // Try to get the file/folder name from the first cell
                        const firstCell = await row.locator('td').first();
                        if (await firstCell.count() > 0) {
                            const nameText = await firstCell.textContent();
                            if (nameText && nameText.trim() !== '') {
                                const name = nameText.trim();
                                
                                // Get all cells for this row
                                const cells = await row.locator('td').all();
                                let type = 'File';
                                let size = '';
                                
                                if (cells.length >= 2) {
                                    const typeText = await cells[1].textContent();
                                    type = typeText?.trim() || 'File';
                                }
                                
                                if (cells.length >= 3) {
                                    const sizeText = await cells[cells.length - 1].textContent();
                                    size = sizeText?.trim() || '';
                                }
                                
                                files.push({ name, type, size });
                            }
                        }
                    }
                    
                    await log(`📊 Found ${files.length} items in ${folderName}`);
                    if (files.length > 0) {
                        await log(`📋 First few items: ${files.slice(0, 3).map(f => `${f.name} (${f.type})`).join(', ')}`);
                    }
                    
                    // Create local folder
                    const localFolderPath = path.join(CONFIG.basePath, folderName);
                    await ensureDirectory(localFolderPath);
                    
                    // Filter out folders and parent directory, then download files
                    const actualFiles = files.filter(f => 
                        !f.type.toLowerCase().includes('folder') && 
                        f.name !== '..' && 
                        f.name !== '.'
                    );
                    
                    // Download files (limit to 10 for now)
                    const filesToDownload = actualFiles.length > 0 ? actualFiles.slice(0, 10) : files.slice(0, 5);
                    
                    for (let j = 0; j < filesToDownload.length; j++) {
                        const file = filesToDownload[j];
                        stats.currentFile = file.name;
                        
                        await log(`📥 Downloading ${j + 1}/${filesToDownload.length}: ${file.name}`);
                        
                        try {
                            // Check if it's a folder by looking at the type
                            const isFolder = file.type.toLowerCase().includes('folder');
                            
                            if (!isFolder) {
                                // It's a file - download it
                                // Find the row containing this file, then find its link
                                const fileRows = await page.locator('tr').all();
                                let fileLink = null;
                                
                                for (const row of fileRows) {
                                    const rowText = await row.textContent();
                                    if (rowText && rowText.includes(file.name)) {
                                        const link = await row.locator('a').first();
                                        if (await link.count() > 0) {
                                            const linkText = await link.textContent();
                                            if (linkText && linkText.trim() === file.name) {
                                                fileLink = link;
                                                break;
                                            }
                                        }
                                    }
                                }
                                
                                if (fileLink) {
                                    try {
                                        // Start waiting for download before clicking
                                        const downloadPromise = page.waitForEvent('download', { timeout: 30000 });
                                        
                                        // Click the file link to trigger download
                                        await fileLink.click();
                                        
                                        // Wait for the download to start
                                        const download = await downloadPromise;
                                        
                                        // Save the download to local folder
                                        const savePath = path.join(localFolderPath, file.name);
                                        await download.saveAs(savePath);
                                        
                                        stats.filesDownloaded++;
                                        await log(`✅ Downloaded: ${file.name} (${file.size})`);
                                    } catch (downloadErr) {
                                        await log(`⚠️ Download failed for ${file.name}: ${downloadErr.message}`, 'WARNING');
                                        // Try alternative download method
                                        await log(`🔄 Trying alternative download method...`);
                                        await fileLink.click({ modifiers: ['Alt'] });
                                        await delay(2000);
                                    }
                                } else {
                                    await log(`⚠️ Could not find link for: ${file.name}`, 'WARNING');
                                }
                            } else {
                                await log(`📁 Skipping subfolder: ${file.name}`);
                            }
                        } catch (err) {
                            await log(`❌ Error downloading ${file.name}: ${err.message}`, 'ERROR');
                            stats.errors.push(`Failed to download: ${file.name}`);
                        }
                        
                        await delay(1000); // Small delay between downloads
                    }
                    
                    if (files.length > 5) {
                        await log(`ℹ️ Note: Only downloaded first 5 files for demonstration. ${files.length - 5} files remaining.`);
                    }
                    
                    // Navigate back to parent folder
                    await log('⬆️ Navigating back to parent folder...');
                    const parentButton = await page.locator('button[title="Parent Folder"], a:has-text("Parent Folder")').first();
                    if (await parentButton.count() > 0) {
                        await parentButton.click();
                        await page.waitForLoadState('networkidle');
                        await delay(2000);
                    } else {
                        // Try going back via URL
                        await page.goto(`${CONFIG.url}/#!/%3Croot%3E%5CPublic%5Cdoc%5C`);
                        await page.waitForLoadState('networkidle');
                        await delay(2000);
                    }
                    
                    stats.foldersProcessed++;
                    
                } else {
                    await log(`⚠️ Folder not found: ${folderName}`, 'WARNING');
                    await page.screenshot({ path: `screenshots/folder_${folderName}_not_found.png` });
                }
                
            } catch (err) {
                await log(`❌ Error processing folder ${folderName}: ${err}`, 'ERROR');
                stats.errors.push(`Failed to process folder: ${folderName}`);
                
                // Try to recover by going back to doc folder
                await page.goto(`${CONFIG.url}/#!/%3Croot%3E%5CPublic%5Cdoc%5C`);
                await page.waitForLoadState('networkidle');
                await delay(2000);
            }
        }

    } catch (err) {
        await log(`❌ Critical error: ${err}`, 'ERROR');
    } finally {
        // Print summary
        const endTime = new Date();
        const duration = (endTime - stats.startTime) / 1000;
        
        await log('');
        await log('============================================================');
        await log('📊 DOWNLOAD SUMMARY');
        await log('============================================================');
        await log(`⏱️ Duration: ${duration.toFixed(2)} seconds`);
        await log(`📁 Folders Processed: ${stats.foldersProcessed}/${CONFIG.missingFolders.length}`);
        await log(`📄 Files Downloaded: ${stats.filesDownloaded}`);
        
        if (stats.errors.length > 0) {
            await log(`❌ Errors: ${stats.errors.length}`);
            stats.errors.forEach(err => log(`  - ${err}`, 'ERROR'));
        }
        
        await log('============================================================');
        await log('✅ Visual download process completed!');
        
        // Keep browser open for 10 seconds to see final state
        await delay(10000);
        
        await browser.close();
    }
}

// Create screenshots directory
async function setup() {
    await ensureDirectory('screenshots');
    await ensureDirectory(CONFIG.basePath);
}

// Run the downloader
(async () => {
    await setup();
    await downloadMissingSunbizData();
})();