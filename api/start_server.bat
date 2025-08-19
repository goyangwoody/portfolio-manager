@echo off
echo Starting PortfolioPulse FastAPI Server...
echo Using existing database models from src/pm/db/models.py
cd /d "%~dp0"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
pause
