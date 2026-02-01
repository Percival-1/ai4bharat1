# Database Setup Guide

This guide explains how to set up and manage the PostgreSQL database for the AI-Driven Agri-Civic Intelligence Platform.

## Database Models

The platform uses the following database models:

### Core Models

1. **User** - Stores farmer and user information
   - Contact information (phone number)
   - Location data (coordinates, district, state)
   - Language preferences
   - Crop information
   - Profile data

2. **Session** - Manages user conversation context
   - User sessions across different channels (voice, SMS, chat, IVR)
   - Conversation history and context
   - Session state management
   - Cross-channel continuity

3. **MarketPrice** - Stores market price data
   - Mandi/market information
   - Crop prices and trends
   - Location-based pricing
   - Price change tracking

4. **NotificationPreferences** - User notification settings
   - Notification type preferences (MSP updates, weather alerts, etc.)
   - Channel preferences (SMS, voice, chat)
   - Timing and frequency settings
   - Language preferences for notifications

5. **NotificationHistory** - Tracks sent notifications
   - Notification delivery status
   - Message content and metadata
   - Error tracking
   - External service integration data

## Database Configuration

### Connection Settings

The database connection is configured in `app/config.py` using environment variables:

```python
database_url: str = Field(
    default="postgresql+asyncpg://postgres:password@localhost:5432/agri_platform",
    description="Database URL",
)
```

### Environment Variables

Set these in your `.env` file:

```bash
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/database_name
DATABASE_ECHO=false  # Set to true for SQL query logging
```

## Database Setup

### 1. Prerequisites

- PostgreSQL 12+ installed and running
- Python dependencies installed (`pip install -r requirements.txt`)

### 2. Database Initialization

#### Option A: Using Alembic (Recommended)

```bash
# Create initial migration (already done)
python -m alembic revision -m "Initial migration"

# Run migrations to create tables
python -m alembic upgrade head
```

#### Option B: Using Python Scripts

```bash
# Initialize database tables
python scripts/init_db.py

# Reset database (drop and recreate tables)
python scripts/init_db.py --reset
```

### 3. Seed Sample Data

```bash
# Add sample data for development/testing
python scripts/seed_db.py

# Clear sample data
python scripts/seed_db.py --clear
```

## Database Services

The platform includes a service layer (`app/services/database.py`) with CRUD operations:

### UserService
- Create, read, update, delete users
- Find users by phone number or location
- Location-based user queries

### SessionService
- Manage user sessions across channels
- Context persistence and retrieval
- Session cleanup and maintenance

### MarketPriceService
- Store and retrieve market price data
- Price trend analysis
- Location-based price queries

### NotificationService
- Manage notification preferences
- Track notification history
- Update delivery status

## Usage Examples

### Creating a User

```python
from app.services.database import UserService
from app.database import get_db

async def create_farmer():
    async for db in get_db():
        user_data = {
            "phone_number": "+919876543210",
            "preferred_language": "hi",
            "location_lat": 28.6139,
            "location_lng": 77.2090,
            "district": "New Delhi",
            "state": "Delhi",
            "crops": ["wheat", "rice"],
            "name": "राम कुमार"
        }
        
        user = await UserService.create_user(db, user_data)
        return user
```

### Managing Sessions

```python
from app.services.database import SessionService

async def create_session():
    async for db in get_db():
        session_data = {
            "user_id": user.id,
            "channel": "sms",
            "context": {"last_query": "weather"},
            "is_active": True
        }
        
        session = await SessionService.create_session(db, session_data)
        return session
```

### Storing Market Prices

```python
from app.services.database import MarketPriceService
from datetime import date

async def add_market_price():
    async for db in get_db():
        price_data = {
            "mandi_name": "Azadpur Mandi",
            "crop_name": "wheat",
            "price_per_quintal": 2150.00,
            "date": date.today(),
            "district": "North Delhi",
            "state": "Delhi"
        }
        
        price = await MarketPriceService.create_market_price(db, price_data)
        return price
```

## Database Migrations

### Creating New Migrations

```bash
# Auto-generate migration from model changes
python -m alembic revision --autogenerate -m "Description of changes"

# Create empty migration file
python -m alembic revision -m "Description of changes"
```

### Running Migrations

```bash
# Apply all pending migrations
python -m alembic upgrade head

# Apply specific migration
python -m alembic upgrade <revision_id>

# Rollback to previous migration
python -m alembic downgrade -1

# Show current migration status
python -m alembic current

# Show migration history
python -m alembic history
```

## Testing

### Model Validation

```bash
# Test model definitions without database connection
python test_models_only.py
```

### Database Integration Tests

```bash
# Test database setup and basic operations (requires running PostgreSQL)
python test_db_setup.py
```

## Connection Pooling

The database uses SQLAlchemy's async connection pooling:

- **Pool Size**: 10 connections
- **Max Overflow**: 20 additional connections
- **Pool Recycle**: 3600 seconds (1 hour)
- **Pre-ping**: Enabled for connection validation

## Performance Considerations

### Indexes

The models include strategic indexes for:
- User phone number lookups
- Session activity tracking
- Market price queries by crop and location
- Notification history queries

### Query Optimization

- Use `selectinload()` for eager loading relationships
- Implement pagination for large result sets
- Use database-level constraints for data integrity
- Regular cleanup of old sessions and notification history

## Troubleshooting

### Common Issues

1. **Connection Failed**: Check PostgreSQL is running and credentials are correct
2. **Migration Errors**: Ensure database user has CREATE/ALTER permissions
3. **Import Errors**: Verify all dependencies are installed
4. **Performance Issues**: Check connection pool settings and query patterns

### Logs

Enable SQL query logging for debugging:

```bash
DATABASE_ECHO=true
```

This will log all SQL queries to help with debugging and optimization.