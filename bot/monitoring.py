import logging
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.models import Site, User, SystemSettings
from config import Config
from datetime import datetime
from zoneinfo import ZoneInfo
from aiogram import Bot
import asyncio

logger = logging.getLogger(__name__)


async def check_website(url: str) -> tuple[bool, str]:
    async with httpx.AsyncClient(follow_redirects=False) as client:
        try:
            response = await client.get(url, timeout=10)
            if 200 <= response.status_code < 300:
                return True, "OK"
            elif 300 <= response.status_code < 400:
                redirect_location = response.headers.get("location", "unknown")
                logger.error(
                    f"Website {url} returned redirect {response.status_code} to {redirect_location}"
                )
                return False, f"Redirect {response.status_code} to {redirect_location}"
            else:
                logger.error(f"Website {url} returned status {response.status_code}")
                return False, f"HTTP {response.status_code}"
        except httpx.HTTPError as e:
            logger.error(f"Website {url} is unavailable: {str(e)}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Unexpected error checking {url}: {str(e)}")
            return False, str(e)


async def start_monitoring(bot: Bot, async_session):
    logger.info("Starting monitoring loop")
    while True:
        interval = Config.CHECK_INTERVAL  # Значение по умолчанию
        try:
            async with async_session() as session:
                logger.debug("Fetching check interval")
                try:
                    result = await session.execute(
                        select(SystemSettings).filter_by(key="check_interval")
                    )
                    settings = result.scalar_one_or_none()
                    interval = (
                        int(settings.value) if settings else Config.CHECK_INTERVAL
                    )
                    logger.debug(f"Check interval: {interval} seconds")
                except Exception as e:
                    logger.error(
                        f"Failed to fetch check interval: {str(e)}", exc_info=True
                    )
                    interval = Config.CHECK_INTERVAL  # Используем значение по умолчанию

                logger.debug("Fetching sites")
                result = await session.execute(select(Site))
                sites = result.scalars().all()
                logger.info(f"Found {len(sites)} sites to check")

                if not sites:
                    logger.warning("No sites found in the database")

                msk_tz = ZoneInfo("Europe/Moscow")
                for site in sites:
                    try:
                        logger.info(f"Checking site {site.url}")
                        is_available, reason = await check_website(site.url)
                        logger.info(
                            f"Site {site.url} is available: {is_available}, reason: {reason}"
                        )
                        if site.is_available != is_available:
                            site.is_available = is_available
                            site.last_checked = datetime.now(msk_tz)
                            result = await session.execute(
                                select(User).filter_by(id=site.user_id)
                            )
                            user = result.scalar_one_or_none()
                            if user:
                                status = (
                                    "снова доступен"
                                    if is_available
                                    else f"недоступен ({reason})"
                                )
                                await bot.send_message(
                                    user.telegram_id,
                                    f"Сайт {site.url} {status} ({site.last_checked.strftime('%Y-%m-%d %H:%M:%S MSK')}).",
                                )
                                logger.debug(
                                    f"Notification sent to user {user.telegram_id}"
                                )
                                site.last_notified = datetime.now(msk_tz)
                            await session.commit()
                        else:
                            site.last_checked = datetime.now(msk_tz)
                            await session.commit()
                    except Exception as e:
                        logger.error(f"Error processing site {site.url}: {str(e)}")
                        continue
        except Exception as e:
            logger.error(f"Monitoring loop error: {str(e)}", exc_info=True)
        logger.debug(f"Sleeping for {interval} seconds")
        await asyncio.sleep(interval)
