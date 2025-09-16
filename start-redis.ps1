# Start Redis Server on Windows
Write-Host "Starting Redis Server..." -ForegroundColor Green

# Check if Redis is installed via Chocolatey
$redisPath = "C:\ProgramData\chocolatey\lib\redis-64\redis-server.exe"
if (Test-Path $redisPath) {
    Start-Process $redisPath
    Write-Host "Redis started from Chocolatey installation" -ForegroundColor Green
}
# Check if Redis is installed in Program Files
elseif (Test-Path "C:\Program Files\Redis\redis-server.exe") {
    Start-Process "C:\Program Files\Redis\redis-server.exe"
    Write-Host "Redis started from Program Files" -ForegroundColor Green
}
# Check if Redis is in Downloads folder (common location)
elseif (Test-Path "$env:USERPROFILE\Downloads\Redis-x64-*\redis-server.exe") {
    $redisExe = Get-ChildItem "$env:USERPROFILE\Downloads\Redis-x64-*\redis-server.exe" | Select-Object -First 1
    Start-Process $redisExe.FullName
    Write-Host "Redis started from Downloads folder" -ForegroundColor Green
}
# Try Docker if available
else {
    Write-Host "Redis executable not found. Trying Docker..." -ForegroundColor Yellow
    $dockerRunning = docker ps 2>$null
    if ($?) {
        Write-Host "Starting Redis with Docker..." -ForegroundColor Green
        docker run -d -p 6379:6379 --name redis-concordbroker redis:latest
        if ($?) {
            Write-Host "Redis started in Docker container" -ForegroundColor Green
        } else {
            Write-Host "Failed to start Redis with Docker" -ForegroundColor Red
            Write-Host "`nTo install Redis on Windows, you can:" -ForegroundColor Yellow
            Write-Host "1. Download from: https://github.com/microsoftarchive/redis/releases" -ForegroundColor Cyan
            Write-Host "2. Use Chocolatey: choco install redis-64" -ForegroundColor Cyan
            Write-Host "3. Use Docker: docker run -p 6379:6379 redis" -ForegroundColor Cyan
        }
    } else {
        Write-Host "Docker is not available" -ForegroundColor Red
        Write-Host "`nTo install Redis on Windows, you can:" -ForegroundColor Yellow
        Write-Host "1. Download from: https://github.com/microsoftarchive/redis/releases" -ForegroundColor Cyan
        Write-Host "2. Use Chocolatey: choco install redis-64" -ForegroundColor Cyan
        Write-Host "3. Use WSL: wsl sudo apt install redis-server" -ForegroundColor Cyan
    }
}

# Test Redis connection after a short delay
Start-Sleep -Seconds 2
Write-Host "`nTesting Redis connection..." -ForegroundColor Yellow
python -c "import redis; r = redis.Redis(host='localhost', port=6379); print(f'Redis is running: {r.ping()}')" 2>$null
if ($?) {
    Write-Host "Redis is ready!" -ForegroundColor Green
} else {
    Write-Host "Redis is not responding yet. The in-memory cache will be used as fallback." -ForegroundColor Yellow
}