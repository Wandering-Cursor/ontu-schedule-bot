"""Contains the 'heart' of the bot. Here it's initialized and configured"""
import datetime
import logging

from secret_config import API_TOKEN
import commands
import patterns

import pytz

import classes

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    PicklePersistence,
    JobQueue
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename="log.log"
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Start the bot"""
    persistence = PicklePersistence(filepath="persistance_cache")

    application = (
        Application.builder()
        .token(API_TOKEN)
        .persistence(persistence)
        .arbitrary_callback_data(True)
        .build()
    )

    application.add_handler(
        CommandHandler(
            command="start",
            callback=commands.start_command
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            callback=commands.faculty_select,
            pattern=patterns.set_group_pattern
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            callback=commands.group_select,
            pattern=patterns.pick_faculty_pattern
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            callback=commands.group_set,
            pattern=patterns.pick_group_pattern
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            callback=commands.start_command,
            pattern=patterns.start_pattern
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            callback=commands.get_schedule,
            pattern=patterns.get_schedule
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            callback=commands.get_day_details,
            pattern=patterns.day_details_pattern
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            callback=commands.get_pair_details,
            pattern=patterns.pair_details_pattern
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            callback=commands.toggle_subscription,
            pattern=patterns.toggle_subscription_pattern
        )
    )

    application.add_handler(
        CommandHandler(
            command="next_pair",
            callback=commands.pair_check_per_chat
        )
    )

    application.add_handler(
        CommandHandler(
            command="schedule",
            callback=commands.get_schedule
        )
    )

    if not isinstance(application.job_queue, JobQueue):
        logger.error("Application doesn't have job_queue")
        return

    for time_kwargs in classes.base.notification_times:
        application.job_queue.run_daily(
            commands.pair_check,
            time=datetime.time(
                tzinfo=pytz.timezone("Europe/Kiev"),
                **time_kwargs
            ),
            days=(1, 2, 3, 4, 5, 6),  # Monday-Saturday
        )

    application.job_queue.run_repeating(
        commands.update_notbot,
        interval=1800  # 30 * 60 = every 30 minutes
    )

    application.run_polling()


if __name__ == "__main__":
    main()
