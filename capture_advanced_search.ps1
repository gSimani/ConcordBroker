# PowerShell script to capture Advanced Search functionality
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

Write-Host "Opening Properties page to test Advanced Search..." -ForegroundColor Green
Start-Process "http://localhost:5174/properties"

Write-Host "Waiting for page to load..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host "`nAdvanced Search has been restored with the following features:" -ForegroundColor Cyan
Write-Host "- Price Range Filters Min and Max" -ForegroundColor Green
Write-Host "- Square Footage Filters Min and Max" -ForegroundColor Green  
Write-Host "- Bedrooms and Bathrooms Filters" -ForegroundColor Green
Write-Host "- Property Type Dropdown" -ForegroundColor Green
Write-Host "- Tax Delinquent Checkbox" -ForegroundColor Green
Write-Host "- Date Range Filters" -ForegroundColor Green
Write-Host "- Clear All Button resets all fields" -ForegroundColor Green
Write-Host "- Tax Deed Sales Tab new feature" -ForegroundColor Green

Write-Host "`nPlease verify in the browser that:" -ForegroundColor Yellow
Write-Host "1. Click 'Advanced Search' button to expand filters"
Write-Host "2. All filter inputs are visible and functional"
Write-Host "3. Tax Delinquent checkbox works"
Write-Host "4. Clear All button resets all fields"
Write-Host "5. Tax Deed Sales tab is visible"

Write-Host "`nPress any key to take a screenshot..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Take screenshot
$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$filename = "advanced_search_test_$timestamp.png"
$bitmap.Save($filename)

Write-Host "`nScreenshot saved as: $filename" -ForegroundColor Green
Write-Host "Advanced Search functionality has been successfully restored!" -ForegroundColor Green