"""
Database connection setup with async SQLAlchemy and connection pooling.

This module provides database connection management following the PRP requirements
for async operations and proper connection pooling for the band platform.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import QueuePool
from sqlalchemy import event

from ..config import settings

logger = logging.getLogger(__name__)

# Create the declarative base for all models
Base = declarative_base()

# Global engine and session maker instances
_engine: Optional[AsyncEngine] = None
_async_session_maker: Optional[async_sessionmaker[AsyncSession]] = None


def create_database_engine() -> AsyncEngine:
    """
    Create an async SQLAlchemy engine with optimized connection pooling.
    
    Returns:
        Configured AsyncEngine instance with connection pooling.
    """
    # Configure connection pool based on environment
    if settings.debug:
        # Development: smaller pool, more logging
        pool_class = QueuePool
        pool_kwargs = {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_pre_ping": True,
            "pool_recycle": 1800,  # 30 minutes
            "echo": settings.database_echo,
        }
    else:
        # Production: larger pool, optimized settings
        pool_class = QueuePool
        pool_kwargs = {
            "pool_size": 20,
            "max_overflow": 40,
            "pool_pre_ping": True,
            "pool_recycle": 3600,  # 1 hour
            "echo": False,
        }
    
    # Create the async engine
    engine = create_async_engine(
        settings.database_url,
        poolclass=pool_class,
        **pool_kwargs,
        # Connection arguments for PostgreSQL
        connect_args={
            "server_settings": {
                "application_name": settings.app_name,
                "jit": "off",  # Disable JIT for better connection performance
            },
            "command_timeout": 60,
        },
        # JSON serializer for better performance with JSON columns
        json_serializer=lambda obj: obj,
        json_deserializer=lambda obj: obj,
    )
    
    # Add event listeners for connection lifecycle
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """Set PostgreSQL-specific connection parameters."""
        # This is for PostgreSQL, not SQLite
        pass
    
    @event.listens_for(engine.sync_engine, "checkout")
    def receive_checkout(dbapi_connection, connection_record, connection_proxy):
        """Log connection checkout in debug mode."""
        if settings.debug:
            logger.debug(f"Connection checked out: {id(dbapi_connection)}")
    
    @event.listens_for(engine.sync_engine, "checkin")
    def receive_checkin(dbapi_connection, connection_record):
        """Log connection checkin in debug mode."""
        if settings.debug:
            logger.debug(f"Connection checked in: {id(dbapi_connection)}")
    
    return engine


def create_session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """
    Create an async session maker with optimal configuration.
    
    Args:
        engine: The async database engine.
        
    Returns:
        Configured async session maker.
    """
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,  # Keep objects accessible after commit
        autoflush=True,  # Auto-flush before queries
        autocommit=False,  # Explicit transaction control
    )


async def init_database() -> None:
    """
    Initialize the database connection and create tables.
    
    This function should be called during application startup.
    """
    global _engine, _async_session_maker
    
    try:
        # Create the database engine
        _engine = create_database_engine()
        
        # Create the session maker
        _async_session_maker = create_session_maker(_engine)
        
        # Test the connection
        async with _engine.begin() as conn:
            # Import all models to ensure they are registered
            from ..models import user, content, sync  # noqa: F401
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_database() -> None:
    """
    Close the database connection and cleanup resources.
    
    This function should be called during application shutdown.
    """
    global _engine, _async_session_maker
    
    if _engine:
        await _engine.dispose()
        _engine = None
        _async_session_maker = None
        logger.info("Database connection closed")


def get_engine() -> AsyncEngine:
    """
    Get the global database engine.
    
    Returns:
        The async database engine.
        
    Raises:
        RuntimeError: If the database is not initialized.
    """
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """
    Get the global session maker.
    
    Returns:
        The async session maker.
        
    Raises:
        RuntimeError: If the database is not initialized.
    """
    if _async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _async_session_maker


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session with automatic cleanup.
    
    This is the primary way to get database sessions in the application.
    
    Yields:
        AsyncSession: A database session.
        
    Example:
        async with get_db_session() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
    """
    session_maker = get_session_maker()
    
    async with session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_session_dependency() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.
    
    This function is used as a FastAPI dependency to inject database sessions
    into route handlers.
    
    Yields:
        AsyncSession: A database session.
        
    Example:
        @app.get("/users")
        async def get_users(session: AsyncSession = Depends(get_db_session_dependency)):
            result = await session.execute(select(User))
            return result.scalars().all()
    """
    async with get_db_session() as session:
        yield session


class DatabaseManager:
    """
    Database manager class for advanced database operations.
    
    This class provides utilities for batch operations, transactions,
    and connection health checks.
    """
    
    def __init__(self):
        self.engine = get_engine()
        self.session_maker = get_session_maker()
    
    async def health_check(self) -> bool:
        """
        Check if the database connection is healthy.
        
        Returns:
            True if the database is accessible, False otherwise.
        """
        try:
            async with self.session_maker() as session:
                await session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def get_connection_info(self) -> dict:
        """
        Get information about the current database connections.
        
        Returns:
            Dictionary with connection pool information.
        """
        pool = self.engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
        }
    
    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Create a database transaction context.
        
        Yields:
            AsyncSession: A database session within a transaction.
            
        Example:
            db_manager = DatabaseManager()
            async with db_manager.transaction() as session:
                # All operations in this block are in a single transaction
                user = User(name="Test")
                session.add(user)
                # Commit happens automatically on exit
        """
        async with self.session_maker() as session:
            async with session.begin():
                try:
                    yield session
                except Exception:
                    await session.rollback()
                    raise


# Convenience instance for use throughout the application
# Instantiate a default database manager if the database is initialised.
# During unit tests the database is usually mocked, so failure to create the
# manager here should not raise an exception. Tests patch this attribute.
try:
    db_manager = DatabaseManager()
except RuntimeError:
    db_manager = None