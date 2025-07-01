import logging
import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.handlers import router
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from logging import Formatter
from zoneinfo import ZoneInfo
from config import Config
from bot.monitoring import start_monitoring


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


class DbSessionMiddleware:
    def __init__(self, session_pool):
        logger.debug("Initializing DbSessionMiddleware with session pool")
        self.session_pool = session_pool

    async def __call__(self, handler, event, data):
        logger.debug(f"Processing event {event} with DbSessionMiddleware")
        async with self.session_pool() as session:
            data["session"] = session
            try:
                return await handler(event, data)
            except Exception as e:
                logger.error(
                    f"Error in DbSessionMiddleware for event {event}: {str(e)}"
                )
                raise


async def main():
    try:
        logger.info("Creating async database engine")
        engine = create_async_engine(Config.DATABASE_URL, echo=False)
        logger.info("Database engine created successfully")

        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        logger.info("Initializing Telegram bot")
        bot = Bot(token=Config.TELEGRAM_TOKEN)
        dp = Dispatcher(storage=MemoryStorage())
        logger.info("Bot and Dispatcher initialized")

        dp.include_router(router)

        dp.message.middleware(DbSessionMiddleware(async_session))

        logger.info("Starting website monitoring task")
        asyncio.create_task(start_monitoring(bot, async_session))

        logger.info("Starting bot polling")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise


if __name__ == "__main__":
    logger.info("Starting application")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application failed to start: {str(e)}")
