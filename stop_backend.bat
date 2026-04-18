@echo off
:: NeuroGuard — Stop all backend processes safely
echo.
echo  [NeuroGuard] Stopping backend...
taskkill /F /FI "WINDOWTITLE eq NeuroGuard Backend" /T >nul 2>&1
taskkill /F /FI "IMAGENAME eq uvicorn.exe" /T >nul 2>&1
:: Find and kill python processes running uvicorn on port 8001
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001 " ^| findstr "LISTENING"') do (
    echo  [NeuroGuard] Killing PID %%a on port 8001
    taskkill /F /PID %%a >nul 2>&1
)
echo  [NeuroGuard] Backend stopped.
echo.
exit /b 0
