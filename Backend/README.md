# TwinSec Studio - Backend

Backend services for OT Cybersecurity Testing Platform with LLM-powered model generation.

## Project Structure

```
Backend/
├── api/          # FastAPI REST API and WebSocket server
├── engine/       # Simulation engine with plugin system
├── connectors/   # External service adapters (LLM providers)
├── schemas/      # Shared JSON schemas and contracts
├── scripts/      # Utility scripts (DB init, seed data)
└── docs/         # API documentation
```

## Quick Start

### 1. Create Virtual Environment

```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
```

### 2. Install Dependencies

```bash
# Install API dependencies
cd api
pip install -r requirements.txt

# Install Engine dependencies (if running separately)
cd ../engine
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy environment template
copy .env.example .env

# Edit .env with your settings:
# - DATABASE_URL (PostgreSQL connection)
# - SECRET_KEY (generate a secure key)
# - OPENAI_API_KEY (or other LLM provider)
```

### 4. Initialize Database

```bash
# Run database initialization script
python scripts/init_db.py
```

### 5. Run API Server

```bash
cd api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at: http://localhost:8000
API documentation: http://localhost:8000/docs

## Development

### Running Tests

```bash
# API tests
cd api
pytest

# Engine tests
cd engine
pytest
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Architecture

- **API Layer**: FastAPI with async/await, WebSocket support
- **Business Logic**: Service layer with clear separation of concerns
- **Data Layer**: SQLAlchemy ORM with PostgreSQL
- **Simulation Engine**: Plugin-based architecture for extensibility
- **LLM Integration**: Adapter pattern for multiple providers

## License

MIT
