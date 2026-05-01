@echo off
echo Starting Veracity Uz Local Server...
echo.

:: Start Backend in a new window
echo [1/2] Starting FastAPI Backend on port 8000...
start "Veracity-Backend" cmd /c "uvicorn app:app --port 8000"

:: Wait a moment for backend to initialize
timeout /t 3 /nobreak > nul

:: Open Frontend in default browser
echo [2/2] Opening Dashboard...
start "" "http://127.0.0.1:8000/"

echo.
echo Server is running! Please keep the backend window open.
pause
