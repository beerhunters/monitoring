import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.handlers import router
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config import Config
from bot.monitoring import start_monitoring

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class DbSessionMiddleware:
    def __init__(self, session_pool):
        self.session_pool = session_pool

    async def __call__(self, handler, event, data):
        async with self.session_pool() as session:
            data["session"] = session
            return await handler(event, data)


async def main():
    engine = create_async_engine(Config.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    bot = Bot(token=Config.TELEGRAM_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    dp.message.middleware(DbSessionMiddleware(async_session))

    # Start monitoring as a background task
    logger.info("Starting website monitoring task")
    asyncio.create_task(start_monitoring(bot, async_session))

    logger.info("Starting bot polling")
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
