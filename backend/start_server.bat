@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
echo Starting Backend Server...
echo.
echo Backend will be available at: http://localhost:8000
echo API Docs will be available at: http://localhost:8000/docs
echo.
python main.py
pause


