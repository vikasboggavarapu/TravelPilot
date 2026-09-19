"""
TravelPilot — Async Database Connection Pool
Supports PostgreSQL (asyncpg) and SQLite (aiosqlite).
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import settings

# ── Engine Configuration ──────────────────────────────────────────────────────
engine_kwargs = {
    "echo": settings.app_debug,
}

if "sqlite" not in settings.database_url:
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,
    })

engine = create_async_engine(
    settings.database_url,
    **engine_kwargs,
)

# ── Session Factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ── Base Model ────────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Dependency for FastAPI ────────────────────────────────────────────────────
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Init DB (create all tables) ───────────────────────────────────────────────
async def init_db():
    """Create all tables on startup."""
    from database import models  # noqa: F401 — ensures models are registered
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
