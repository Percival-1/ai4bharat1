@echo off
REM Development environment setup script for AI-Driven Agri-Civic Intelligence Platform (Windows)

echo 🚀 Setting up AI-Driven Agri-Civic Intelligence Platform development environment...

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    exit /b 1
)

REM Check if Poetry is installed
poetry --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Poetry is not installed. Please install Poetry first.
    echo Visit: https://python-poetry.org/docs/#installation
    exit /b 1
)

REM Create .env file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file from template...
    copy .env.template .env
    echo ✅ .env file created. Please update it with your actual API keys and configuration.
) else (
    echo ✅ .env file already exists.
)

REM Install Python dependencies
echo 📦 Installing Python dependencies with Poetry...
poetry install

REM Create necessary directories
echo 📁 Creating necessary directories...
if not exist logs mkdir logs
if not exist data mkdir data
if not exist uploads mkdir uploads

REM Start Docker services
echo 🐳 Starting Docker services...
docker-compose up -d postgres redis

REM Wait for services to be ready
echo ⏳ Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Check if services are running
echo 🔍 Checking service status...
docker-compose ps

echo.
echo 🎉 Development environment setup complete!
echo.
echo To start the application:
echo   poetry run uvicorn app.main:app --reload
echo.
echo Or use Docker Compose:
echo   docker-compose up app
echo.
echo API Documentation will be available at:
echo   http://localhost:8000/docs
echo.
echo To stop services:
echo   docker-compose down
echo.