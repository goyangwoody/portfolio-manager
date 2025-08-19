@echo off
echo Starting PortfolioPulse FastAPI Backend...
cd /d "C:\Users\Seungjae\Desktop\pr"

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

echo Starting FastAPI server on port 8000...
python api\main.py

pause
