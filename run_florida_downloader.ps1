# Florida Revenue Data Downloader Runner
Write-Host "Starting Florida Revenue Comprehensive Downloader..." -ForegroundColor Green

# Change to the project directory
Set-Location "C:\Users\gsima\Documents\MyProject\ConcordBroker"

# Run the Python downloader
python florida_comprehensive_downloader.py

Write-Host "Download process completed. Check logs for details." -ForegroundColor Green
Pause