@echo off
REM Florida Property Data Downloader - Simple Batch Script
REM Downloads SDF (Sales Data Files) for key counties

echo ========================================
echo FLORIDA PROPERTY DATA DOWNLOADER
echo ========================================
echo.

set BASE_URL=https://floridarevenue.com/property/dataportal/DataPortal_Files/2025/
set OUTPUT_BASE=C:\TEMP\DATABASE PROPERTY APP

REM Create base directory
if not exist "%OUTPUT_BASE%" mkdir "%OUTPUT_BASE%"

REM Priority Counties - Download SDF files for these
echo Downloading BROWARD County (06) - Property 514124070600 location...
call :download_county 06 BROWARD

echo Downloading MIAMI-DADE County (13)...
call :download_county 13 MIAMI-DADE

echo Downloading PALM BEACH County (50)...
call :download_county 50 PALM_BEACH

echo Downloading ORANGE County (48)...
call :download_county 48 ORANGE

echo Downloading HILLSBOROUGH County (29)...
call :download_county 29 HILLSBOROUGH

echo Downloading PINELLAS County (52)...
call :download_county 52 PINELLAS

echo Downloading DUVAL County (16)...
call :download_county 16 DUVAL

echo Downloading LEE County (36)...
call :download_county 36 LEE

echo Downloading COLLIER County (11)...
call :download_county 11 COLLIER

echo Downloading SARASOTA County (58)...
call :download_county 58 SARASOTA

echo.
echo ========================================
echo DOWNLOAD COMPLETE!
echo ========================================
echo Check: %OUTPUT_BASE%
echo Next: Run import script to load into Supabase
pause
exit /b

:download_county
set CODE=%1
set NAME=%2

REM Create county directories
if not exist "%OUTPUT_BASE%\%NAME%" mkdir "%OUTPUT_BASE%\%NAME%"
if not exist "%OUTPUT_BASE%\%NAME%\NAL" mkdir "%OUTPUT_BASE%\%NAME%\NAL"
if not exist "%OUTPUT_BASE%\%NAME%\NAP" mkdir "%OUTPUT_BASE%\%NAME%\NAP"
if not exist "%OUTPUT_BASE%\%NAME%\NAV" mkdir "%OUTPUT_BASE%\%NAME%\NAV"
if not exist "%OUTPUT_BASE%\%NAME%\SDF" mkdir "%OUTPUT_BASE%\%NAME%\SDF"

REM Download each file type
echo   Downloading %NAME% NAL (Names/Addresses)...
curl -s -o "%OUTPUT_BASE%\%NAME%\NAL\%NAME%_NAL_2025.txt" "%BASE_URL%%CODE%_NAL_2025.txt"

echo   Downloading %NAME% NAP (Property Characteristics)...
curl -s -o "%OUTPUT_BASE%\%NAME%\NAP\%NAME%_NAP_2025.txt" "%BASE_URL%%CODE%_NAP_2025.txt"

echo   Downloading %NAME% NAV (Property Values)...
curl -s -o "%OUTPUT_BASE%\%NAME%\NAV\%NAME%_NAV_2025.txt" "%BASE_URL%%CODE%_NAV_2025.txt"

echo   Downloading %NAME% SDF (Sales Data) - CRITICAL...
curl -s -o "%OUTPUT_BASE%\%NAME%\SDF\%NAME%_SDF_2025.txt" "%BASE_URL%%CODE%_SDF_2025.txt"

echo   %NAME% complete!
echo.
exit /b