"""Database connection and session management."""

import asyncio
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncEngine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

print("[DATABASE] Loading database module...")
from app.config import settings

# Show what DATABASE_URL we're using (hide password)
if settings.database_url:
    url_parts = settings.database_url.split("@")
    if len(url_parts) > 1:
        host_info = url_parts[-1]
        scheme = settings.database_url.split("://")[0]
        print(f"[DATABASE] URL scheme: {scheme}")
        print(f"[DATABASE] URL host: {host_info}")
    else:
        print(f"[DATABASE] URL appears to be default/local")
else:
    print("[DATABASE] WARNING: database_url is empty!")

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# Global engine and session maker - initialized lazily
_engine: Optional[AsyncEngine] = None
_async_session_maker: Optional[async_sessionmaker[AsyncSession]] = None

print("[DATABASE] Module loaded, engine not yet created (lazy)")


def get_engine() -> AsyncEngine:
    """Get or create the async engine (lazy initialization)."""
    global _engine
    if _engine is None:
        print("[DATABASE] Creating async engine...")
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.database_echo,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
        )
        print("[DATABASE] Engine created (connection not yet tested)")
    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """Get or create the async session maker (lazy initialization)."""
    global _async_session_maker
    if _async_session_maker is None:
        _async_session_maker = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _async_session_maker


async def get_db() -> AsyncSession:
    """Dependency to get database session."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def wait_for_db(max_retries: int = 5, initial_delay: float = 2.0) -> bool:
    """Wait for database to be available with exponential backoff.
    
    Args:
        max_retries: Maximum number of connection attempts
        initial_delay: Initial delay between retries in seconds
        
    Returns:
        True if connection successful, False otherwise
    """
    print(f"[DATABASE] wait_for_db called, max_retries={max_retries}")
    engine = get_engine()
    delay = initial_delay
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[DATABASE] Connection attempt {attempt}/{max_retries}...")
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                print(f"[DATABASE] Connection SUCCESS on attempt {attempt}")
                logger.info(f"Database connection successful on attempt {attempt}")
                return True
        except Exception as e:
            print(f"[DATABASE] Connection FAILED on attempt {attempt}: {type(e).__name__}: {e}")
            if attempt < max_retries:
                print(f"[DATABASE] Waiting {delay:.1f}s before retry...")
                logger.warning(
                    f"Database connection attempt {attempt}/{max_retries} failed: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                print(f"[DATABASE] All {max_retries} attempts FAILED")
                logger.error(f"Database connection failed after {max_retries} attempts: {e}")
                return False
    
    return False


async def init_db():
    """Initialize database connection and tables."""
    print("[DATABASE] init_db() called")
    # Wait for database to be available
    if not await wait_for_db():
        print("[DATABASE] CRITICAL: Could not connect to database!")
        raise RuntimeError("Could not connect to database after multiple retries")
    
    # Create tables if they don't exist
    print("[DATABASE] Creating tables...")
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("[DATABASE] Database initialized successfully!")
    logger.info("Database initialized successfully")


async def close_db():
    """Close database connections."""
    global _engine, _async_session_maker
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_maker = None
        print("[DATABASE] Connections closed")
        logger.info("Database connections closed")



