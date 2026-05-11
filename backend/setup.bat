@echo off
REM Knowledge Factory Backend Setup Script for Windows

echo.
echo 🚀 Setting up Knowledge Factory Backend...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.12 or higher.
    exit /b 1
)

echo ✅ Python found
python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

echo.

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

echo.

REM Upgrade pip
echo 📦 Upgrading pip...
python -m pip install --upgrade pip

echo.

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt

echo.

REM Check if .env exists
if not exist ".env" (
    echo ⚠️  .env file not found. Creating default .env...
    echo DATABASE_URL=sqlite+aiosqlite:///./knowledge_factory.db > .env
    echo DEBUG=true >> .env
    echo CORS_ORIGINS=http://localhost:5173,http://localhost:3000 >> .env
    echo ✅ .env file created
) else (
    echo ✅ .env file exists
)

echo.
echo ✨ Setup complete!
echo.
echo Next steps:
echo   1. Activate the virtual environment:
echo      venv\Scripts\activate
echo.
echo   2. Test Piston integration:
echo      python test_piston_standalone.py
echo.
echo   3. Start the server:
echo      uvicorn app.main:app --reload --port 8000
echo.

pause
