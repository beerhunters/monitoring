from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from models.models import Base, SystemSettings
import asyncio
import logging
from logging import Formatter
from zoneinfo import ZoneInfo
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


class MSKFormatter(Formatter):
    def converter(self, timestamp):
        return timestamp.astimezone(ZoneInfo("Europe/Moscow"))

    def formatTime(self, record, datefmt=None):
        dt = self.converter(datetime.fromtimestamp(record.created))
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")


logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(
    MSKFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


async def init_db():
    await asyncio.sleep(5)
    logger.info("Initializing database")
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        logger.info("Creating tables")
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        logger.info("Checking system_settings")
        result = await session.execute(
            select(SystemSettings).filter_by(key="check_interval")
        )
        settings = result.scalar_one_or_none()
        if not settings:
            logger.info("Adding default check_interval")
            session.add(SystemSettings(key="check_interval", value="60"))
            await session.commit()
        logger.info("Database initialization complete")


if __name__ == "__main__":
    asyncio.run(init_db())
