"""
Database connection and session management
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging
import os
from pathlib import Path

from config import settings
from .models import Base

logger = logging.getLogger(__name__)

# Ensure /tmp directory exists (for Render deployment)
if "/tmp/" in settings.DATABASE_URL:
    os.makedirs("/tmp", exist_ok=True)
    logger.info("Ensured /tmp directory exists for database")

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    poolclass=StaticPool if "sqlite" in settings.DATABASE_URL else None,
    echo=settings.DEBUG,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """Initialize database tables only if they don't exist"""
    try:
        async with engine.begin() as conn:
            # Check if tables already exist
            def check_tables(connection):
                from sqlalchemy import inspect
                inspector = inspect(connection)
                existing_tables = inspector.get_table_names()
                return 'shipments' in existing_tables
            
            has_tables = await conn.run_sync(check_tables)
            
            if has_tables:
                logger.info("Database tables already exist - preserving data")
            else:
                logger.info("Creating database tables...")
                await conn.run_sync(Base.metadata.create_all)
                logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session
    Usage: async with get_db() as db:
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context():
    """Context manager for database sessions"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
