import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from dishka.integrations.taskiq import FromDishka, inject

from src.services.notification import NotificationService
from src.worker.broker import broker

logger = logging.getLogger(__name__)

NOTIFICATION_TEXT = (
    "Вітаю, <b>{name}</b>! 👋\n\nУ цябе ёсць карткі для паўтарэння. Час трэніравацца! 📚"
)


@broker.task(schedule=[{"cron": "0 * * * *"}])
@inject(patch_module=True)
async def send_review_notifications(
    notification_service: FromDishka[NotificationService],
    bot: FromDishka[Bot],
) -> None:
    users = await notification_service.get_users_to_notify()

    notified = 0
    for user in users:
        local_hour = datetime.now(ZoneInfo(user.timezone)).hour
        if local_hour != user.notification_hour:
            continue

        try:
            await bot.send_message(
                chat_id=user.id,
                text=NOTIFICATION_TEXT.format(name=user.name),
            )
            notified += 1
        except TelegramForbiddenError:
            logger.warning("User %d blocked the bot, disabling notifications", user.id)
            await notification_service.disable_notifications(user.id)
        except TelegramRetryAfter as e:
            logger.warning("Rate limited, sleeping %s seconds", e.retry_after)
            await asyncio.sleep(e.retry_after)
            try:
                await bot.send_message(
                    chat_id=user.id,
                    text=NOTIFICATION_TEXT.format(name=user.name),
                )
                notified += 1
            except Exception:
                logger.exception("Failed to notify user %d after retry", user.id)
        except Exception:
            logger.exception("Failed to notify user %d", user.id)

    logger.info("Sent %d notifications out of %d eligible users", notified, len(users))
