@echo off
cd /d "%~dp0"
echo Installing MouseFX requirements...
py -m pip install -r requirements.txt
if errorlevel 1 (echo Install failed. Try Python 3.12 or 3.13, then retry.& pause & exit /b 1)
echo Done. Double-click run.bat to start.
pause
