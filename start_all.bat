@echo off
echo =========================================
echo Starting Body Language & Voice Analyzer
echo =========================================

echo.
echo [1/2] Starting FastAPI Backend...
start "Backend" cmd /k "cd /d "F:\Internship Projects\Body Language and Voice Analyzer" && .\venv\Scripts\activate && python -m uvicorn app.main:app --reload --port 8000"

echo Waiting for backend to start...
timeout /t 5 >nul

echo.
echo [2/2] Starting Flutter Web App...
cd /d "F:\Internship Projects\Body Language and Voice Analyzer\body_language_analyzer"
set CHROME_EXECUTABLE=C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe
flutter run -d chrome --web-port 5000

pause