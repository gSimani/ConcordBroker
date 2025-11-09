# SFTP Download Agent - Permanent Knowledge Base

## Overview
This agent manages downloads from the Florida Department of State SFTP portal at https://sftp.floridados.gov

## Credentials
- **URL**: https://sftp.floridados.gov
- **Username**: Public
- **Password**: PubAccess1845!

## Local Storage
- **Base Path**: C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE
- **Structure**: Mirrors SFTP structure exactly

## SFTP Structure Map
```
<root>\Public\
├── doc\
│   ├── AG\              (1 file)
│   ├── cor\             (6,286 files across years)
│   │   ├── 2011\        (251 files)
│   │   ├── 2012\        (251 files)
│   │   ├── 2013\        (251 files)
│   │   ├── 2014\        (251 files)
│   │   ├── 2015\        (251 files)
│   │   ├── 2016\        (251 files)
│   │   ├── 2017\        (244 files)
│   │   ├── 2018\        (245 files)
│   │   ├── 2019\        (245 files)
│   │   ├── 2020\        (243 files)
│   │   ├── 2021\        (251 files)
│   │   ├── Events\      (947 files)
│   │   ├── Filings\     (1 file)
│   │   └── Prior to 2011\ (760 files)
│   ├── cornp\           (1 file)
│   ├── DHE\             (10 files)
│   ├── fic\             (5,415 files across years)
│   │   ├── 2011\        (337 files)
│   │   ├── 2012\        (364 files)
│   │   ├── 2013\        (360 files)
│   │   ├── 2014\        (362 files)
│   │   ├── 2015\        (364 files)
│   │   ├── 2016\        (350 files)
│   │   ├── 2017\        (359 files)
│   │   ├── 2018\        (362 files)
│   │   ├── 2019\        (365 files)
│   │   ├── 2020\        (360 files)
│   │   ├── 2021\        (337 files)
│   │   ├── Events\      (1,314 files)
│   │   ├── Filings\     (1 file)
│   │   └── Prior to 2011\ (781 files)
│   ├── FLR\             (1,762 files)
│   │   ├── DEBTORS\     (160 files)
│   │   ├── EVENTS\      (160 files)
│   │   ├── FILINGS\     (162 files)
│   │   └── SECURED\     (160 files)
│   ├── gen\             (737 files)
│   │   ├── Events\      (178 files)
│   │   └── Filings\     (559 files)
│   ├── Quarterly\       (13 files)
│   │   ├── Cor\         (2 files)
│   │   ├── Fic\         (2 files)
│   │   ├── FLR\         (5 files)
│   │   ├── Gen\         (2 files)
│   │   ├── Non-Profit\  (1 file)
│   │   └── TradeMarks\  (1 file)
│   ├── notes\           (system folder - skip)
│   ├── ficevent-Year2000\ (system folder - skip)
│   └── tm\              (system folder - skip)
├── corprindata.zip      (665MB - officer/principal data)
└── cordata_quarterly.zip (685MB - quarterly corporate data)
```

## Navigation Rules

### 1. Login Process
- Navigate to https://sftp.floridados.gov
- Fill username field: `input[placeholder="Username"]`
- Fill password field: `input[placeholder="Password"]`
- Click login: `button:has-text("Login")`
- Verify success: Look for `tr:has-text("doc")`

### 2. Folder Navigation
- **Enter folder**: Double-click on `tr:has-text("foldername")`
- **Go back**: Double-click on `tr:has-text("..")`
- **Alternative back**: Click `button:has-text("Parent Folder")`
- **Wait after navigation**: Always wait 1-2 seconds for page load

### 3. File Detection
- Files have extensions (.txt, .zip, etc.)
- Folders don't have extensions
- Check cell type: "Folder" = folder, anything else = file
- Scroll down with `End` key to see all files

### 4. Download Process
- **Select file**: Single click on `tr:has-text("filename.txt")`
- **Download**: Click `button:has-text("Download")`
- **Alternative download**: `button[title="Download"]`
- **Wait for download**: Use `page.expect_download()`
- **Save to correct path**: Mirror SFTP structure locally

## Download Strategy

### Batch Processing (4 files at a time)
```python
async def download_batch(files_to_download, batch_size=4):
    for i in range(0, len(files_to_download), batch_size):
        batch = files_to_download[i:i+batch_size]
        tasks = []
        for file in batch:
            tasks.append(download_single_file(file))
        await asyncio.gather(*tasks)
        await asyncio.sleep(2)  # Pause between batches
```

### Duplicate Prevention
1. Build set of existing local files before starting
2. Check each file before download: `if local_file.exists()`
3. Track downloaded files to avoid re-downloading in same session
4. Compare file sizes if unsure

### Completion Detection
- Folder is complete when:
  - All visible files have been processed
  - Scrolling doesn't reveal new files
  - Local file count matches remote file count
  - No errors in last batch

## Priority Download Order
1. **doc/fic/** - Fictitious names (many missing)
2. **doc/FLR/** - Florida records (many missing)
3. **doc/gen/** - General records (many missing)
4. **doc/DHE/** - Small folder, quick to complete
5. **doc/Quarterly/** - Important quarterly reports
6. **doc/cor/** - Corporation files (mostly complete)

## Error Handling

### Common Issues & Solutions
1. **Timeout on navigation**
   - Increase timeout to 60-90 seconds
   - Try alternative selectors
   - Refresh page and retry

2. **Download button not found**
   - File might not be selected
   - Try alternative selectors: `#download-button`, `button[title="Download"]`
   - Ensure file is clicked first

3. **Can't enter folder**
   - Might be in wrong location
   - Return to root first
   - Check if folder name has special characters

4. **Download fails**
   - Check available disk space
   - Verify file doesn't already exist
   - Try downloading individually instead of batch

## Monitoring Requirements

### Real-time Monitoring
- Show current location in SFTP
- Display download progress (X of Y files)
- Track downloaded vs skipped files
- Monitor download speed
- Alert on errors

### Verification Steps
1. Count files in remote folder
2. Count files in local folder
3. Compare counts and sizes
4. List missing files
5. Verify no duplicates

## Update Schedule
- **Daily**: Check for new files in Quarterly folders
- **Weekly**: Full scan of all folders
- **Monthly**: Deep verification of all downloaded files
- **On-demand**: When user requests specific folders

## Success Metrics
- All 14,201 remote files accessible
- Zero duplicate downloads
- Proper folder structure maintained
- Download completion rate > 95%
- Error rate < 5%

## Important Notes
1. Browser must stay VISIBLE for monitoring
2. Never download WELCOME.TXT
3. Skip system folders (notes, tm, ficevent-Year2000)
4. Create folders before downloading files
5. Always return to root between different folder paths
6. Session timeout after ~30 minutes of inactivity
7. Quarterly folders have the most recent data
8. Officer data is in corprindata.zip (fixed-width format)
9. Corporate data updates are in Quarterly folder

## File Formats
- **Corporation files**: .txt files with pipe-delimited data
- **Officer files**: Fixed-width format in corprindata.zip
- **Quarterly updates**: ZIP files in Quarterly folder
- **Events/Filings**: Dated .txt files (YYYYMMDD format)