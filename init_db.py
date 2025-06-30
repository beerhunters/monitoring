from sqlalchemy.ext.asyncio import create_async_engine
from models.models import Base
import asyncio


async def init_db():
    engine = create_async_engine("postgresql+psycopg://user:password@db:5432/monitor")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_db())
