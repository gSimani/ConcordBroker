@echo off
echo ================================================================
echo  ConcordBroker Data Verification System
echo  ML-based Field Mapping + Visual Verification
echo ================================================================
echo.

REM Run PowerShell script with execution policy bypass
powershell -ExecutionPolicy Bypass -File run_data_verification.ps1

pause