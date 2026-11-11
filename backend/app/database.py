from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from app.config import settings

connect_args = {"timeout": 2} if "postgresql+asyncpg" in settings.SQLALCHEMY_DATABASE_URI else {}
engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=False, poolclass=NullPool, connect_args=connect_args)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
