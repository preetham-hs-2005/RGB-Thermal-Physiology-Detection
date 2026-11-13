@echo off
cd /d "%~dp0"
python scripts\run_lutseg_baseline.py
if errorlevel 1 pause
