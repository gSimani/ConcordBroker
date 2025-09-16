# ConcordBroker Development with Nodemon
# PowerShell script for Windows development

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "CONCORDBROKER DEVELOPMENT WITH NODEMON" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Check if nodemon is installed
$nodemon = Get-Command nodemon -ErrorAction SilentlyContinue
if (-not $nodemon) {
    Write-Host "[INFO] Installing nodemon globally..." -ForegroundColor Yellow
    npm install -g nodemon
}

# Menu for development options
Write-Host "`nSelect development mode:" -ForegroundColor Green
Write-Host "1. Full Stack (API + Web + Pipeline)" -ForegroundColor White
Write-Host "2. API Only (FastAPI backend)" -ForegroundColor White
Write-Host "3. Web Only (React frontend)" -ForegroundColor White
Write-Host "4. Pipeline Only (Data agents)" -ForegroundColor White
Write-Host "5. Custom Watch (specify files)" -ForegroundColor White
Write-Host "0. Exit" -ForegroundColor White

$choice = Read-Host "`nEnter your choice"

switch ($choice) {
    "1" {
        Write-Host "`n[STARTING] Full Stack Development Mode" -ForegroundColor Green
        
        # Start all services in separate terminals
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "nodemon --config nodemon-api.json"
        Start-Sleep -Seconds 2
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "nodemon --config nodemon-web.json"
        Start-Sleep -Seconds 2
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "nodemon --config nodemon-pipeline.json"
        
        Write-Host "[SUCCESS] All services started with auto-restart" -ForegroundColor Green
        Write-Host "API: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "Web: http://localhost:5173" -ForegroundColor Cyan
        Write-Host "Pipeline: Running in background" -ForegroundColor Cyan
    }
    
    "2" {
        Write-Host "`n[STARTING] API Development Mode" -ForegroundColor Green
        nodemon --config nodemon-api.json
    }
    
    "3" {
        Write-Host "`n[STARTING] Web Development Mode" -ForegroundColor Green
        nodemon --config nodemon-web.json
    }
    
    "4" {
        Write-Host "`n[STARTING] Pipeline Development Mode" -ForegroundColor Green
        nodemon --config nodemon-pipeline.json
    }
    
    "5" {
        $files = Read-Host "Enter files/directories to watch (comma-separated)"
        $extensions = Read-Host "Enter file extensions to watch (default: py,js,ts,tsx)"
        
        if (-not $extensions) { $extensions = "py,js,ts,tsx" }
        
        Write-Host "`n[STARTING] Custom Watch Mode" -ForegroundColor Green
        nodemon --watch $files --ext $extensions --exec "echo 'Files changed, add your command here'"
    }
    
    "0" {
        Write-Host "Exiting..." -ForegroundColor Yellow
        exit
    }
    
    default {
        Write-Host "Invalid choice!" -ForegroundColor Red
    }
}

Write-Host "`n[TIP] Press 'rs' to manually restart" -ForegroundColor Yellow
Write-Host "[TIP] Press Ctrl+C to stop" -ForegroundColor Yellow