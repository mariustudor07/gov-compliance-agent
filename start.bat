@echo off
rem Double-click to start GovCheck: the API (port 8000) and the website (port 5173) in two windows.
rem Close those two windows to stop it.
cd /d %~dp0

start "GovCheck API" cmd /k "cd backend && .venv\Scripts\python.exe -m uvicorn api.main:app --port 8000"

rem Always check for packages teammates added (e.g. jspdf for the PDF report); quick when nothing changed.
echo Checking frontend packages...
pushd frontend && call npm install --silent && popd
start "GovCheck website" cmd /k "cd frontend && npm run dev"

timeout /t 6 >nul
start http://localhost:5173
