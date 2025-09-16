const { chromium } = require('playwright');
const fs = require('fs').promises;
const path = require('path');

// Configuration
const CONFIG = {
    url: 'https://sftp.floridados.gov',
    username: 'Public',
    password: 'PubAccess1845!',
    basePath: 'C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\TEMP\\DATABASE\\doc',
    targetFolders: [
        'fic',              // Fictitious Names (DBAs) - has year subfolders
        'FLR',              // Florida Lien Registry - has category subfolders
        'tm',               // Trademarks - has year subfolders
        'DHE',              // Highway Safety - has zip files
        'ficevent-Year2000', // Historical events - has .dat files
        'notes',            // Documentation - has txt files
    ],
    maxFilesPerFolder: 5,  // Limit downloads for demo
    maxDepth: 2            // Max folder depth to explore
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
    
    try {
        await fs.appendFile('recursive_sunbiz_download.log', logMessage + '\n');
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

async function processFolder(page, folderName, localBasePath, depth = 0) {
    if (depth >= CONFIG.maxDepth) {
        await log(`⚠️ Max depth reached for ${folderName}, skipping deeper folders`);
        return;
    }
    
    await log(`📂 Processing folder: ${folderName} (depth: ${depth})`);
    
    // Create local folder
    const localFolderPath = path.join(localBasePath, folderName);
    await ensureDirectory(localFolderPath);
    
    // Click on the folder to enter it
    const folderRow = await page.locator(`tr:has-text("${folderName}")`).first();
    if (await folderRow.count() > 0) {
        await folderRow.click();
        await delay(500);
        await folderRow.dblclick();
        await page.waitForLoadState('networkidle');
        await delay(2000);
        
        // Take screenshot of folder contents
        await page.screenshot({ path: `screenshots/folder_${folderName.replace(/[\/\\]/g, '_')}_depth${depth}.png` });
        
        // Get all items in current folder
        const rows = await page.locator('tr').all();
        const items = [];
        
        for (const row of rows) {
            const rowText = await row.textContent();
            if (!rowText || rowText.trim() === '') continue;
            if (rowText.includes('Name') && rowText.includes('Type')) continue;
            if (rowText.includes('Parent Folder')) continue;
            
            const firstCell = await row.locator('td').first();
            if (await firstCell.count() > 0) {
                const nameText = await firstCell.textContent();
                if (nameText && nameText.trim() !== '' && nameText.trim() !== '..') {
                    const name = nameText.trim();
                    const cells = await row.locator('td').all();
                    let type = 'File';
                    
                    if (cells.length >= 2) {
                        const typeText = await cells[1].textContent();
                        type = typeText?.trim() || 'File';
                    }
                    
                    items.push({ name, type });
                }
            }
        }
        
        await log(`📊 Found ${items.length} items in ${folderName}`);
        
        // Separate files and folders
        const files = items.filter(item => !item.type.toLowerCase().includes('folder'));
        const subfolders = items.filter(item => item.type.toLowerCase().includes('folder'));
        
        // Download files (if any)
        if (files.length > 0) {
            await log(`📄 Found ${files.length} files to download`);
            const filesToDownload = files.slice(0, CONFIG.maxFilesPerFolder);
            
            for (const file of filesToDownload) {
                await log(`📥 Attempting to download: ${file.name}`);
                
                try {
                    // Try to find and click the file - it might be a direct link
                    const fileElement = await page.locator(`td:has-text("${file.name}")`).first();
                    
                    if (await fileElement.count() > 0) {
                        // Click on the file row to select it
                        await fileElement.click();
                        await delay(500);
                        
                        // Try double-clicking to download
                        const downloadPromise = page.waitForEvent('download', { timeout: 5000 }).catch(() => null);
                        await fileElement.dblclick();
                        
                        const download = await downloadPromise;
                        if (download) {
                            const savePath = path.join(localFolderPath, file.name);
                            await download.saveAs(savePath);
                            stats.filesDownloaded++;
                            await log(`✅ Downloaded: ${file.name}`);
                        } else {
                            // If double-click doesn't work, try right-click
                            await fileElement.click({ button: 'right' });
                            await delay(500);
                            
                            // Look for download option in context menu
                            const downloadOption = await page.locator('text=/download/i').first();
                            if (await downloadOption.count() > 0) {
                                const downloadPromise2 = page.waitForEvent('download', { timeout: 5000 });
                                await downloadOption.click();
                                const download2 = await downloadPromise2;
                                const savePath = path.join(localFolderPath, file.name);
                                await download2.saveAs(savePath);
                                stats.filesDownloaded++;
                                await log(`✅ Downloaded via context menu: ${file.name}`);
                            } else {
                                await log(`⚠️ Could not download: ${file.name} - no download method available`);
                            }
                        }
                    }
                } catch (err) {
                    await log(`❌ Error downloading ${file.name}: ${err.message}`, 'ERROR');
                }
                
                await delay(1000);
            }
        }
        
        // Process subfolders recursively
        if (subfolders.length > 0 && depth < CONFIG.maxDepth - 1) {
            await log(`📁 Found ${subfolders.length} subfolders to explore`);
            
            // Limit subfolder processing for demo
            const subfoldersToProcess = subfolders.slice(0, 3);
            
            for (const subfolder of subfoldersToProcess) {
                await processFolder(page, subfolder.name, localFolderPath, depth + 1);
            }
        }
        
        // Navigate back to parent folder
        await log('⬆️ Navigating back to parent folder...');
        const parentButton = await page.locator('a:has-text("Parent Folder")').first();
        if (await parentButton.count() > 0) {
            await parentButton.click();
            await page.waitForLoadState('networkidle');
            await delay(2000);
        }
    } else {
        await log(`⚠️ Could not find folder: ${folderName}`);
    }
}

async function downloadSunbizDataRecursively() {
    await log('🚀 Starting Recursive Sunbiz Downloader');
    await log('============================================================');
    
    const browser = await chromium.launch({
        headless: false,
        slowMo: 100,
        args: ['--window-size=1920,1080']
    });

    const context = await browser.newContext({
        acceptDownloads: true,
        viewport: { width: 1920, height: 1080 }
    });

    const page = await context.newPage();

    try {
        // Login
        await log(`📍 Navigating to ${CONFIG.url}`);
        await page.goto(CONFIG.url, { waitUntil: 'networkidle' });
        
        await log('🔐 Logging in...');
        await page.fill('input[placeholder="Username"]', CONFIG.username);
        await page.fill('input[placeholder="Password"]', CONFIG.password);
        await page.click('button:has-text("Login")');
        await page.waitForLoadState('networkidle');
        await delay(2000);
        await log('✅ Login successful!');
        
        // Navigate to doc folder
        await log('📁 Navigating to doc folder...');
        const docRow = await page.locator('tr:has-text("doc")').first();
        if (await docRow.count() > 0) {
            await docRow.click();
            await delay(500);
            await docRow.dblclick();
            await page.waitForLoadState('networkidle');
            await delay(2000);
            await log('✅ Entered doc folder');
        }
        
        // Process each target folder recursively
        for (const folder of CONFIG.targetFolders) {
            await log('');
            await log('============================================================');
            await log(`📦 Starting recursive processing of: ${folder}`);
            await log('============================================================');
            
            try {
                await processFolder(page, folder, CONFIG.basePath, 0);
                stats.foldersProcessed++;
            } catch (err) {
                await log(`❌ Error processing folder ${folder}: ${err}`, 'ERROR');
                stats.errors.push(`Failed to process: ${folder}`);
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
        await log(`📁 Folders Processed: ${stats.foldersProcessed}/${CONFIG.targetFolders.length}`);
        await log(`📄 Files Downloaded: ${stats.filesDownloaded}`);
        
        if (stats.errors.length > 0) {
            await log(`❌ Errors: ${stats.errors.length}`);
            stats.errors.forEach(err => log(`  - ${err}`, 'ERROR'));
        }
        
        await log('============================================================');
        await log('✅ Recursive download process completed!');
        
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
    await downloadSunbizDataRecursively();
})();