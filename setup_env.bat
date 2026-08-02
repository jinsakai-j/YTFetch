@echo off
title YTFetch Setup Environment & Shortcut Creator
echo ====================================================
echo      YTFetch Setup Environment & Desktop Shortcut
echo ====================================================
echo.

cd /d "%~dp0"

echo [1/2] Memasang dependencies dari requirements.txt...
python -m pip install -r requirements.txt

echo.
echo [2/2] Membuat Desktop Shortcut YTFetch...
python create_shortcut.py

echo.
echo ====================================================
echo      Setup Selesai! Shortcut YTFetch Siap di Desktop.
echo ====================================================
echo.
pause
