# Start both Backend and Frontend
# Usage: .\start_all.ps1

$backendDir = "F:\Internship Projects\Body Language and Voice Analyzer"
$flutterDir = "F:\Internship Projects\Body Language and Voice Analyzer\body_language_analyzer"
$chromePath = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

Write-Host "=== Starting Body Language & Voice Analyzer ===" -ForegroundColor Cyan

# 1. Start Backend in new window
Write-Host "Starting FastAPI backend..." -ForegroundColor Green
$backendScript = "cd '$backendDir'; .\venv\Scripts\Activate.ps1; python -m uvicorn app.main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript

# 2. Wait for backend health check
Write-Host "Waiting for backend to be ready..." -ForegroundColor Yellow
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
        if ($resp.StatusCode -eq 200) {
            Write-Host "Backend is healthy!" -ForegroundColor Green
            $ready = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}

if (-not $ready) {
    Write-Host "Warning: Backend health check timed out" -ForegroundColor Yellow
}

# 3. Start Frontend
Write-Host "Starting Flutter web app..." -ForegroundColor Green
$env:CHROME_EXECUTABLE = $chromePath

cd $flutterDir
flutter run -d chrome --web-port 5000