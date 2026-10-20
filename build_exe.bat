@echo off
cd /d "%~dp0"
py -m pip install pyinstaller
if errorlevel 1 goto fail
py -m PyInstaller --noconfirm --clean --windowed --name MouseFX mouse_fx.py
if errorlevel 1 goto fail
echo EXE created at dist\MouseFX.exe
pause
exit /b 0
:fail
echo Build failed. Read the error above.
pause
