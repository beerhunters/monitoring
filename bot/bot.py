import logging
from logging import Formatter
from zoneinfo import ZoneInfo
from datetime import datetime
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from bot.handlers import router
from bot.monitoring import start_monitoring
from config import Config


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
logger.setLevel(logging.DEBUG)


class DbSessionMiddleware:
    def __init__(self, session_pool):
        self.session_pool = session_pool

    async def __call__(self, handler, event, data):
        async with self.session_pool() as session:
            data["session"] = session
            return await handler(event, data)


async def main():
    try:
        logger.info("Initializing database engine")
        engine = create_async_engine(Config.DATABASE_URL, echo=False)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        logger.info("Initializing bot")
        bot = Bot(token=Config.TELEGRAM_TOKEN)
        dp = Dispatcher(storage=MemoryStorage())
        dp.include_router(router)
        dp.message.middleware(DbSessionMiddleware(async_session))
        dp.callback_query.middleware(DbSessionMiddleware(async_session))
        logger.info("Starting bot and monitoring")
        # Запускаем мониторинг как отдельную задачу
        monitoring_task = asyncio.create_task(start_monitoring(bot, async_session))

        # Проверяем, не завершится ли задача мониторинга с ошибкой
        async def monitor_task_errors():
            try:
                await monitoring_task
            except Exception as e:
                logger.error(f"Monitoring task failed: {str(e)}", exc_info=True)

        asyncio.create_task(monitor_task_errors())
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Main function error: {str(e)}", exc_info=True)
        raise
    finally:
        logger.info("Shutting down bot")
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
