#!/bin/bash

# Development environment setup script for AI-Driven Agri-Civic Intelligence Platform

set -e

echo "🚀 Setting up AI-Driven Agri-Civic Intelligence Platform development environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed. Please install Poetry first."
    echo "Visit: https://python-poetry.org/docs/#installation"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.template .env
    echo "✅ .env file created. Please update it with your actual API keys and configuration."
else
    echo "✅ .env file already exists."
fi

# Install Python dependencies
echo "📦 Installing Python dependencies with Poetry..."
poetry install

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p data
mkdir -p uploads

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d postgres redis

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are healthy
echo "🔍 Checking service health..."
if docker-compose ps | grep -q "healthy"; then
    echo "✅ Services are healthy!"
else
    echo "⚠️  Some services might not be fully ready. Check with: docker-compose ps"
fi

# Run database migrations (when implemented)
# echo "🗃️  Running database migrations..."
# poetry run alembic upgrade head

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "To start the application:"
echo "  poetry run uvicorn app.main:app --reload"
echo ""
echo "Or use Docker Compose:"
echo "  docker-compose up app"
echo ""
echo "API Documentation will be available at:"
echo "  http://localhost:8000/docs"
echo ""
echo "To stop services:"
echo "  docker-compose down"
echo ""