@echo off
echo Starting EduLife v2.0 Backend Server...
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Start uvicorn server
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

pause
