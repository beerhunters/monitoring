import logging
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.models import Site, SystemSettings, User
from config import Config
from datetime import datetime
from datetime import datetime, timedelta
import asyncio
from aiogram.exceptions import TelegramBadRequest
from zoneinfo import ZoneInfo

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
                msk_tz = ZoneInfo("Europe/Moscow")
                logger.info(f"Found {len(sites)} sites to check")

                for site in sites:
                    logger.debug(
                        f"Processing site ID {site.id}: {site.url} for user_id {site.user_id}"
                    )
                    try:
                        is_available, reason = await check_website(site.url)
                        if site.is_available != is_available:
                            site.is_available = is_available
                            site.last_checked = datetime.now(msk_tz)
                            status = (
                                "снова доступен"
                                if is_available
                                else f"недоступен ({reason})"
                            )

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
                                    user.telegram_id,
                                    f"Сайт {site.url} {status} ({site.last_checked.strftime('%Y-%m-%d %H:%M:%S %Z')}).",
                                )
                                # site.last_notified = datetime.utcnow()
                                site.last_notified = datetime.now(msk_tz)
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
