# AI-Driven Agri-Civic Intelligence Platform

A comprehensive multilingual system that leverages Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG) to deliver actionable agricultural intelligence to farmers and rural communities.

## Features

- Multi-channel input processing (voice, text, SMS, IVR)
- Multilingual support with translation layer
- Weather intelligence and forecasting
- Crop disease detection and treatment recommendations
- Government scheme discovery
- Market intelligence and price optimization
- RAG-based knowledge retrieval
- Proactive notification system

## Development Setup

### Prerequisites

- Python 3.11+
- Poetry (recommended) or pip
- Docker and Docker Compose

### Installation

#### Option 1: Using Poetry (Recommended)

1. Clone the repository
2. Install dependencies:
   ```bash
   poetry install
   ```

3. Set up environment variables:
   ```bash
   cp .env.template .env
   # Edit .env with your configuration
   ```

4. Start development services:
   ```bash
   docker-compose up -d postgres redis
   ```

5. Run the application:
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

#### Option 2: Using pip

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.template .env
   # Edit .env with your configuration
   ```

5. Start development services:
   ```bash
   docker-compose up -d postgres redis
   ```

6. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

### Quick Setup Script

For automated setup, use the provided scripts:

**Linux/Mac:**
```bash
chmod +x scripts/setup-dev.sh
./scripts/setup-dev.sh
```

**Windows:**
```cmd
scripts\setup-dev.bat
```

## Project Structure

```
app/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration management
├── core/                # Core business logic
├── api/                 # API routes and endpoints
├── models/              # Database models
├── services/            # Business logic services
├── utils/               # Utility functions
└── tests/               # Test files
```

## API Documentation

Once the application is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

### Running Tests

Run the test suite:
```bash
# With Poetry
poetry run pytest tests/ -v

# With pip
python -m pytest tests/ -v
```

Run tests with coverage:
```bash
# With Poetry
poetry run pytest tests/ -v --cov=app --cov-report=html

# With pip
python -m pytest tests/ -v --cov=app --cov-report=html
```

### Test Server Startup

Test that the server can start properly:
```bash
python test_server.py
```

### Validate Project Setup

Validate that all required files are present:
```bash
python validate_setup.py
```