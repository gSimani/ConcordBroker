# Sunbiz SFTP Navigation Guide

## Access Portal Details
- **URL**: https://sftp.floridados.gov
- **Username**: Public  
- **Password**: PubAccess1845!
- **Portal Name**: Florida Department of State - Data Access Portal

## Interface Structure After Login

### Current Folder Display
After successful login, you land in: `<root>\Public\`

The interface shows a file browser with these columns:
- **Name** (with folder/file icons)
- **Type** (Folder/File)
- **Date Modified** 
- **Size (KB)**

### Navigation Elements
1. **Current folder path**: Shows at top as "Current folder: <root>\Public\"
2. **Action buttons** in toolbar:
   - 🔄 Refresh
   - 📁 New Folder
   - 🔄 Rename
   - ✅ Open
   - 📤 Upload
   - 📥 Download
   - ❌ Delete
   - ❓ Help
3. **Logout button**: Top right corner

## Step-by-Step Navigation

### 1. Login Process
```python
# Selectors for login form
username_selector = 'input[name="username"]'
password_selector = 'input[name="password"]'
login_button = 'button[type="submit"]'
```

### 2. Navigate to doc Folder
After login, the "doc" folder is visible in the main listing:
- **Method 1**: Double-click the "doc" row
- **Method 2**: Single click to select, then click "Open" button
- **Method 3**: Click directly on the folder name "doc"

```python
# Selectors for doc folder
doc_folder_selector = 'tr:has-text("doc")'  # Table row containing "doc"
doc_link_selector = 'td:has-text("doc")'    # Table cell with "doc" text
```

### 3. Inside doc Folder Structure
Once inside `/doc/`, you'll find:

#### Main Directories:
- **cor/** - Corporation daily files (2011-2024)
- **fic/** - Fictitious name files
- **AG/** - Agent files
- **FLR/** - Florida records
- **tm/** - Trademark files
- **notes/** - Documentation
- **Quarterly/** - Quarterly reports

#### Key Files:
- **corprindata.zip** - Principal/officer data (665MB)
- **cordata_quarterly.zip** - Quarterly corporation data (685MB)
- **WELCOME.TXT** - Documentation file

## File Download Process

### Download Methods
1. **Single File Download**:
   - Click on file row to select
   - Click "Download" button in toolbar
   - OR right-click and select download

2. **Multiple File Download**:
   - Ctrl+Click to select multiple files
   - Click "Download" button
   - Files download as a zip

### Download Selectors
```python
# File selection
file_row = 'tr:has-text("filename.txt")'
download_button = 'button:has-text("Download")'

# Alternative: Direct click on file
file_link = 'a[href*="download"]'
```

## Folder Navigation

### Enter Subfolder
```python
# Click on folder name (e.g., "cor")
await page.click('tr:has-text("cor") td:first-child')
# OR double-click
await page.dblclick('tr:has-text("cor")')
```

### Navigate Back
```python
# Use browser back button
await page.go_back()
# OR click parent folder in breadcrumb
await page.click('a:has-text("Public")')
```

## Complete Navigation Flow

```
1. Login Page
   ↓
2. Land in <root>\Public\
   ↓
3. Click "doc" folder
   ↓
4. Land in <root>\Public\doc\
   ↓
5. Navigate to subfolders:
   - cor/ → Corporation files
   - fic/ → Fictitious names
   - AG/ → Agent data
   ↓
6. Download files
   ↓
7. Navigate back to parent
```

## Important Notes

### File Types and Sizes
- **Text files (.txt)**: Can be previewed before download
- **ZIP files**: Download directly, no preview
- **Large files**: May take time, watch for download progress

### Session Management
- Session timeout: ~30 minutes of inactivity
- Keep browser active to maintain session
- Refresh page if session expires

### Download Path Structure
Maintain same structure locally:
```
C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\
└── doc\
    ├── cor\
    │   ├── 2024\
    │   ├── 2023\
    │   └── Events\
    ├── fic\
    ├── AG\
    └── [other folders]
```

## Troubleshooting

### Common Issues:
1. **"doc" not visible**: You may be in wrong directory - check "Current folder" path
2. **Download fails**: Check browser download settings and permissions
3. **Session expired**: Refresh page and re-login
4. **Folder won't open**: Try double-click instead of single click

### Playwright Specific:
```python
# Wait for navigation
await page.wait_for_load_state('networkidle')

# Wait for table to load
await page.wait_for_selector('table')

# Handle download with timeout
async with page.expect_download(timeout=60000) as download_info:
    await page.click(download_button)
```

## Quick Reference

| Action | Selector | Method |
|--------|----------|--------|
| Login username | `input[name="username"]` | fill() |
| Login password | `input[name="password"]` | fill() |
| Submit login | `button[type="submit"]` | click() |
| Select doc folder | `tr:has-text("doc")` | click() or dblclick() |
| Download button | `button:has-text("Download")` | click() |
| File row | `tr:has-text("filename")` | click() |
| Navigate back | - | page.go_back() |

This guide ensures consistent navigation through the Sunbiz SFTP portal for downloading business data files.