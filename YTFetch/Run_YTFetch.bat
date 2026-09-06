@echo off
cd /d "%~dp0"
if exist "%~dp0venv\Scripts\pythonw.exe" (
    start "" "%~dp0venv\Scripts\pythonw.exe" "%~dp0YTFetch.py"
) else (
    start "" pythonw "%~dp0YTFetch.py"
)
exit
