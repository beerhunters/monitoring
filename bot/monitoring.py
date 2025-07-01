import logging
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.models import Site, SystemSettings, User
from config import Config
from datetime import datetime
import asyncio
from aiogram.exceptions import TelegramBadRequest

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


async def check_website(url: str) -> bool:
    logger.debug(f"Checking website: {url}")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10)
            response.raise_for_status()
            logger.info(f"Website {url} is available")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Website {url} is unavailable: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking website {url}: {str(e)}")
            return False


async def start_monitoring(bot, async_session):
    logger.info("Starting monitoring loop")
    while True:
        try:
            async with async_session() as session:
                # Load check interval
                logger.debug("Loading check interval from SystemSettings")
                result = await session.execute(
                    select(SystemSettings).filter_by(key="check_interval")
                )
                settings = result.scalar_one_or_none()
                interval = int(settings.value) if settings else Config.CHECK_INTERVAL
                logger.info(f"Using check interval: {interval} seconds")

                # Load all sites
                logger.debug("Fetching all sites from database")
                result = await session.execute(select(Site))
                sites = result.scalars().all()
                logger.info(f"Found {len(sites)} sites to check")

                for site in sites:
                    logger.debug(
                        f"Processing site ID {site.id}: {site.url} for user_id {site.user_id}"
                    )
                    try:
                        is_available = await check_website(site.url)
                        if is_available != site.is_available:
                            logger.info(
                                f"Site {site.url} status changed to {'available' if is_available else 'unavailable'}"
                            )
                            site.is_available = is_available
                            site.last_checked = datetime.utcnow()
                            status = "снова доступен" if is_available else "недоступен"

                            # Check if user exists and chat is valid
                            try:
                                result = await session.execute(
                                    select(User).filter_by(id=site.user_id)
                                )
                                user = result.scalar_one_or_none()
                                if not user:
                                    logger.warning(
                                        f"No user found in database for user_id {site.user_id}"
                                    )
                                    continue

                                # Verify chat exists in Telegram
                                await bot.get_chat(user.telegram_id)
                                await bot.send_message(
                                    user.telegram_id, f"Сайт {site.url} {status}"
                                )
                                site.last_notified = datetime.utcnow()
                                logger.info(
                                    f"Notification sent to user {user.telegram_id} for site {site.url}"
                                )
                            except TelegramBadRequest as e:
                                if "chat not found" in str(e).lower():
                                    logger.error(
                                        f"Cannot send notification for site {site.url}: Chat not found for telegram_id {user.telegram_id}"
                                    )
                                else:
                                    logger.error(
                                        f"Telegram API error for site {site.url}: {str(e)}"
                                    )
                            except Exception as e:
                                logger.error(
                                    f"Failed to send notification for site {site.url}: {str(e)}"
                                )
                        else:
                            logger.debug(
                                f"Site {site.url} status unchanged: {'available' if site.is_available else 'unavailable'}"
                            )
                        await session.commit()
                    except Exception as e:
                        logger.error(f"Error processing site {site.url}: {str(e)}")
                        await session.rollback()
                logger.debug(f"Finished processing sites, committing session")
                await session.commit()

            logger.debug(f"Sleeping for {interval} seconds")
            await asyncio.sleep(interval)
        except Exception as e:
            logger.error(f"Monitoring loop error: {str(e)}")
            await asyncio.sleep(10)  # Prevent tight loop on persistent errors
