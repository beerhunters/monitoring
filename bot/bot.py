import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config import Config
from bot.handlers import router
from bot.monitoring import start_monitoring
from models.models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Middleware для внедрения сессии
class DbSessionMiddleware:
    def __init__(self, session_pool):
        self.session_pool = session_pool

    async def __call__(self, handler, event, data):
        async with self.session_pool() as session:
            data["session"] = session
            return await handler(event, data)


async def main():
    # Создание движка и пула сессий
    engine = create_async_engine(Config.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Создание таблиц при запуске
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Инициализация бота и диспетчера
    bot = Bot(token=Config.TELEGRAM_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Добавление middleware
    dp.update.middleware(DbSessionMiddleware(async_session))
    dp.include_router(router)

    # Запуск задачи мониторинга
    asyncio.create_task(start_monitoring(bot, async_session))

    try:
        await dp.start_polling(bot)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
