@echo off
echo ============================================================
echo Sunbiz Missing Data Downloader
echo ============================================================
echo.
echo This will download all missing folders from the Sunbiz SFTP:
echo - comp (Company/Compliance)
echo - DHE (Department of Highway Safety)
echo - fic (Fictitious Names/DBAs) - CRITICAL
echo - ficevent-Year2000 (Historical events)
echo - FLR (Florida Lien Registry) - CRITICAL
echo - gen (General Partnerships)
echo - notes (Documentation)
echo - Quarterly (Quarterly Reports)
echo - tm (Trademarks)
echo.
echo ============================================================
pause

echo.
echo Installing required packages...
pip install playwright aiofiles --quiet

echo.
echo Installing Playwright browsers...
playwright install chromium

echo.
echo Starting download process...
python download_missing_sunbiz.py

echo.
echo ============================================================
echo Download process completed!
echo Check sunbiz_missing_download.log for details
echo ============================================================
pause