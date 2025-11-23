"""Contains the 'heart' of the bot. Here it's initialized and configured"""

import datetime
import logging
import os

import pytz
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    JobQueue,
    PicklePersistence,
    AIORateLimiter,
)

from ontu_schedule_bot import commands, patterns
from ontu_schedule_bot.settings import settings
from ontu_schedule_bot.utils import PAIR_START_TIME

os.makedirs("logs", exist_ok=True)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler(
            filename=f"logs/debug_{datetime.datetime.now().isoformat().replace(':', '_')}.log",
            mode="w",
            encoding="UTF-8",
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Start the bot"""
    persistence = PicklePersistence(filepath="persistance_cache")

    application = (
        Application.builder()
        .token(settings.BOT_TOKEN.get_secret_value())
        .persistence(persistence)
        .arbitrary_callback_data(True)
        .concurrent_updates(True)
        .rate_limiter(
            AIORateLimiter(
                max_retries=5,
            )
        )
        .build()
    )

    application.add_error_handler(
        commands.error_handler,
    )

    application.add_handler(
        CommandHandler(
            command="start",
            callback=commands.start_command,
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            callback=commands.start_command,
            pattern=patterns.start_pattern,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            callback=commands.manage_subscription,
            pattern=patterns.manage_subscription_pattern,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            callback=commands.manage_subscription_groups,
            pattern=patterns.manage_subscription_groups_pattern,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            callback=commands.manage_subscription_teachers,
            pattern=patterns.manage_subscription_teachers_pattern,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            callback=commands.add_subscription_group,
            pattern=patterns.add_subscription_group_pattern,
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            callback=commands.add_subscription_teacher,
            pattern=patterns.add_subscription_teacher_pattern,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            callback=commands.select_faculty,
            pattern=patterns.select_faculty_pattern,
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            callback=commands.select_department,
            pattern=patterns.select_department_pattern,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            callback=commands.add_subscription_item,
            pattern=patterns.add_subscription_item_pattern,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            callback=commands.remove_subscription_items,
            pattern=patterns.remove_subscription_items_pattern,
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            callback=commands.remove_subscription_item,
            pattern=patterns.remove_subscription_item_pattern,
        )
    )

    application.add_handler(
        CommandHandler(
            command="today",
            callback=commands.get_today_schedule,
        )
    )
    application.add_handler(
        CommandHandler(
            command="tomorrow",
            callback=commands.get_tomorrow_schedule,
        )
    )
    application.add_handler(
        CommandHandler(
            command="week",
            callback=commands.get_week_schedule,
        )
    )
    application.add_handler(
        CommandHandler(
            "next_pair",
            commands.next_pair,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            callback=commands.get_schedule,
            pattern=patterns.get_schedule_pattern,
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            callback=commands.get_pair_details,
            pattern=patterns.get_pair_details_pattern,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            callback=commands.toggle_subscription,
            pattern=patterns.toggle_subscription_pattern,
        )
    )

    application.add_handler(
        CommandHandler(
            command="manual_batch_pair_check",
            callback=commands.manual_batch_pair_check,
        )
    )

    if not isinstance(application.job_queue, JobQueue):
        logger.error("Application doesn't have job_queue")
        return

    for _pair, start_time in PAIR_START_TIME.items():
        # Convert time to datetime, subtract 10 minutes, then back to time
        temp_datetime = datetime.datetime.combine(datetime.date.today(), start_time)
        temp_datetime -= datetime.timedelta(minutes=10)
        adjusted_time = temp_datetime.time()

        application.job_queue.run_daily(
            commands.batch_pair_check,
            time=datetime.time(
                hour=adjusted_time.hour,
                minute=adjusted_time.minute,
                tzinfo=pytz.timezone("Europe/Kyiv"),
            ),
            days=(1, 2, 3, 4, 5, 6),  # Monday-Saturday
            job_kwargs={
                "misfire_grace_time": None,
            },
        )

    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
