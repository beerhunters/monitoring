import asyncio
import requests
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.models import Site, SystemSettings
from config import Config
import httpx


async def check_website(url: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(url)
        return response.status_code == 200
    except Exception:
        return False


async def start_monitoring(bot, async_session):
    while True:
        async with async_session() as session:
            result = await session.execute(
                select(SystemSettings).filter_by(key="check_interval")
            )
            settings = result.scalar_one_or_none()
            interval = int(settings.value) if settings else Config.CHECK_INTERVAL

            result = await session.execute(select(Site))
            sites = result.scalars().all()

            for site in sites:
                is_available = await check_website(site.url)

                if is_available != site.is_available:
                    site.is_available = is_available
                    site.last_notified = datetime.utcnow()

                    status = "снова доступен" if is_available else "недоступен"
                    await bot.send_message(
                        chat_id=site.user.telegram_id,
                        text=f"Ваш сайт {site.url} {status}!",
                    )

                site.last_checked = datetime.utcnow()
                await session.commit()

        await asyncio.sleep(interval)
