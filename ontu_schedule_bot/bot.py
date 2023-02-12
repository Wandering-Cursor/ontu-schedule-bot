from secret_config import API_TOKEN
import commands
import patterns
import classes

import pytz

import datetime

import logging

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, PicklePersistence, JobQueue

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Start the bot"""
    persistence = PicklePersistence(filepath="./ontu_schedule_bot_data")

    application = (
        Application.builder()
        .token(API_TOKEN)
        .persistence(persistence)
        .arbitrary_callback_data(True)
        .build()
    )
    application = Application.builder().token(API_TOKEN).build()

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
            pattern=patterns.set_group_pattern
        )
    )

    if not isinstance(application.job_queue, JobQueue):
        logger.error("Application doesn't have job_queue")
        return

    pair_times = [
        {"hour": 8, "minute": 0},
        {"hour": 9, "minute": 30},
        {"hour": 11, "minute": 30},
        {"hour": 13, "minute": 0},
        {"hour": 14, "minute": 30},
        {"hour": 16, "minute": 0},
    ]

    for time_kwargs in pair_times:
        application.job_queue.run_daily(
            commands.pair_check,
            time=datetime.time(**time_kwargs, tzinfo=pytz.timezone("Europe/Kiev")),
            days=(1, 2, 3, 4, 5, 6),
        )

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
