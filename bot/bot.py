import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.handlers import router
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config import Config
from bot.monitoring import start_monitoring

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


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

        logger.debug("Creating sessionmaker for AsyncSession")
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        logger.debug("Sessionmaker created")

        logger.info("Initializing Telegram bot")
        bot = Bot(token=Config.TELEGRAM_TOKEN)
        dp = Dispatcher(storage=MemoryStorage())
        logger.info("Bot and Dispatcher initialized")

        logger.debug("Including router in Dispatcher")
        dp.include_router(router)
        logger.debug("Registering DbSessionMiddleware")
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
