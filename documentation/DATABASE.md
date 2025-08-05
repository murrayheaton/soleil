# Database Documentation for SOLEil

## Overview
SOLEil uses PostgreSQL as the primary database with SQLAlchemy as the ORM, and Redis for caching and session management.

## PostgreSQL Setup

### Connection Configuration
```python
# Environment variables
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/soleil_db

# SQLAlchemy setup
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)
```

## Database Models

### Base Model Pattern
```python
from sqlalchemy import Column, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class BaseModel(Base):
    """Base model with common fields"""
    __abstract__ = True
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### User Model
```python
from sqlalchemy import Column, String, JSON, Boolean

class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String, unique=True, nullable=False, index=True)
    google_id = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=False)
    profile_data = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    repertoire = relationship("Song", back_populates="user")
    bands = relationship("BandMember", back_populates="user")
```

### Song/Repertoire Model
```python
class Song(BaseModel):
    __tablename__ = "songs"
    
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False, index=True)
    artist = Column(String, index=True)
    key = Column(String)
    tempo = Column(Integer)
    genre = Column(String)
    chart_types = Column(JSON, default=list)  # ["guitar", "bass", "drums"]
    drive_file_id = Column(String, unique=True)
    
    # Relationships
    user = relationship("User", back_populates="repertoire")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_songs', 'user_id', 'title'),
    )
```

## Database Migrations with Alembic

### Initial Setup
```bash
# Initialize Alembic
alembic init alembic

# Create first migration
alembic revision --autogenerate -m "Initial migration"

# Run migrations
alembic upgrade head
```

### Migration Configuration
```python
# alembic/env.py
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.models import Base

config = context.config
target_metadata = Base.metadata

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        
        with context.begin_transaction():
            context.run_migrations()
```

### Common Migration Commands
```bash
# Create new migration
alembic revision --autogenerate -m "Add band tables"

# Upgrade to latest
alembic upgrade head

# Downgrade one revision
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

## Query Patterns

### Basic CRUD Operations
```python
# Create
async def create_user(db: AsyncSession, user_data: dict):
    user = User(**user_data)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

# Read
async def get_user_by_email(db: AsyncSession, email: str):
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    return result.scalar_one_or_none()

# Update
async def update_user_profile(db: AsyncSession, user_id: str, profile_data: dict):
    query = update(User).where(User.id == user_id).values(profile_data=profile_data)
    await db.execute(query)
    await db.commit()

# Delete
async def delete_song(db: AsyncSession, song_id: str):
    query = delete(Song).where(Song.id == song_id)
    await db.execute(query)
    await db.commit()
```

### Advanced Queries
```python
# Joins
async def get_user_with_repertoire(db: AsyncSession, user_id: str):
    query = select(User).options(
        selectinload(User.repertoire)
    ).where(User.id == user_id)
    
    result = await db.execute(query)
    return result.unique().scalar_one_or_none()

# Aggregations
async def get_repertoire_stats(db: AsyncSession, user_id: str):
    query = select(
        func.count(Song.id).label('total_songs'),
        func.count(func.distinct(Song.artist)).label('unique_artists'),
        func.count(func.distinct(Song.genre)).label('unique_genres')
    ).where(Song.user_id == user_id)
    
    result = await db.execute(query)
    return result.first()

# Full-text search
async def search_songs(db: AsyncSession, search_term: str):
    query = select(Song).where(
        or_(
            Song.title.ilike(f"%{search_term}%"),
            Song.artist.ilike(f"%{search_term}%")
        )
    ).order_by(Song.title)
    
    result = await db.execute(query)
    return result.scalars().all()
```

## Redis Integration

### Configuration
```python
import redis.asyncio as redis

# Create Redis connection
redis_client = redis.from_url(
    "redis://localhost:6379",
    encoding="utf-8",
    decode_responses=True
)
```

### Caching Patterns
```python
# Cache user session
async def cache_user_session(user_id: str, session_data: dict):
    key = f"session:{user_id}"
    await redis_client.setex(
        key, 
        3600,  # 1 hour TTL
        json.dumps(session_data)
    )

# Get cached data
async def get_cached_repertoire(user_id: str):
    key = f"repertoire:{user_id}"
    data = await redis_client.get(key)
    if data:
        return json.loads(data)
    return None

# Invalidate cache
async def invalidate_user_cache(user_id: str):
    pattern = f"*:{user_id}:*"
    async for key in redis_client.scan_iter(match=pattern):
        await redis_client.delete(key)
```

### Session Management
```python
# Store session
async def create_session(user_id: str, token: str):
    session_key = f"session:{token}"
    user_data = {
        "user_id": user_id,
        "created_at": datetime.utcnow().isoformat()
    }
    await redis_client.setex(
        session_key,
        86400,  # 24 hours
        json.dumps(user_data)
    )

# Validate session
async def validate_session(token: str):
    session_key = f"session:{token}"
    data = await redis_client.get(session_key)
    if data:
        return json.loads(data)
    return None
```

## Performance Optimization

### Connection Pooling
```python
# PostgreSQL connection pool
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,        # Number of connections to maintain
    max_overflow=40,     # Maximum overflow connections
    pool_timeout=30,     # Timeout for getting connection
    pool_recycle=1800,   # Recycle connections after 30 minutes
)
```

### Query Optimization
```python
# Use eager loading to avoid N+1 queries
query = select(Band).options(
    selectinload(Band.members).selectinload(BandMember.user)
)

# Use bulk operations
async def bulk_create_songs(db: AsyncSession, songs_data: List[dict]):
    await db.execute(
        insert(Song),
        songs_data
    )
    await db.commit()

# Index usage
class Song(BaseModel):
    __table_args__ = (
        Index('idx_user_title', 'user_id', 'title'),
        Index('idx_artist', 'artist'),
        Index('idx_created', 'created_at'),
    )
```

## Backup and Recovery

### Automated Backups
```bash
# Backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_NAME="soleil_db"

pg_dump -U postgres -h localhost $DB_NAME | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Keep only last 7 days of backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
```

### Restore from Backup
```bash
# Restore database
gunzip < backup_20240101_120000.sql.gz | psql -U postgres -h localhost soleil_db
```

## Monitoring

### Query Performance
```sql
-- Find slow queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
WHERE mean_time > 100  -- queries taking more than 100ms
ORDER BY mean_time DESC
LIMIT 20;
```

### Connection Monitoring
```sql
-- Active connections
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query_start,
    state_change
FROM pg_stat_activity
WHERE state != 'idle';
```

## Testing

### Test Database Setup
```python
# conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture
async def test_db():
    # Use separate test database
    engine = create_async_engine("postgresql+asyncpg://localhost/soleil_test")
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Provide session
    async with AsyncSession(engine) as session:
        yield session
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

### Database Tests
```python
@pytest.mark.asyncio
async def test_create_user(test_db):
    user_data = {
        "email": "test@example.com",
        "google_id": "123456",
        "display_name": "Test User"
    }
    
    user = await create_user(test_db, user_data)
    assert user.id is not None
    assert user.email == "test@example.com"
```

## Security Best Practices

1. **Use Parameterized Queries**: Always use SQLAlchemy's query builders
2. **Connection Encryption**: Use SSL for database connections
3. **Least Privilege**: Create specific database users with minimal permissions
4. **Regular Updates**: Keep PostgreSQL and drivers updated
5. **Audit Logging**: Enable PostgreSQL audit logging

## Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Redis Documentation](https://redis.io/documentation)
- [AsyncPG Documentation](https://magicstack.github.io/asyncpg/)