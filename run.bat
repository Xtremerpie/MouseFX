@echo off
cd /d "%~dp0"
py mouse_fx.py
if errorlevel 1 (echo MouseFX stopped with an error.& pause)
