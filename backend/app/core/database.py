from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.core.config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    # Import all models so metadata is populated before create_all
    import app.models.account           # noqa: F401
    import app.models.password_reset_token  # noqa: F401
    import app.models.ticket            # noqa: F401
    import app.models.faq               # noqa: F401
    import app.models.troubleshooting   # noqa: F401
    import app.models.incident_history  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for sql in [
            "ALTER TABLE accounts ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'user'",
            "ALTER TABLE accounts ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE accounts ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP WITH TIME ZONE",
        ]:
            await conn.execute(text(sql))

    from app.services.faq_service import seed as seed_faq
    from app.services.troubleshooting_service import seed as seed_ts
    from app.services.memory_service import seed as seed_memory
    async with AsyncSessionLocal() as db:
        await seed_faq(db)
        await seed_ts(db)
        await seed_memory(db)
