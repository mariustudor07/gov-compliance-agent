@echo off
rem Double-click to review flagged labels. Always uses THIS project folder, so the answers land in data\labels.csv here.
cd /d %~dp0backend
.venv\Scripts\python.exe -m ml.review
echo.
pause
