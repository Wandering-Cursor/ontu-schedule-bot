"""This module contains all the commands bot may execute"""

import contextvars
import datetime
import html
import json
import logging
import time
import traceback
from typing import Literal

import telegram.error
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from ontu_schedule_bot import messages, utils
from ontu_schedule_bot.settings import settings
from ontu_schedule_bot.third_party.admin.client import AdminClient
from ontu_schedule_bot.third_party.admin.enums import Platform
from ontu_schedule_bot.third_party.admin.schemas import (
    Chat,
    CreateChatRequest,
    DaySchedule,
    Department,
    Faculty,
    Group,
    Pair,
    Subscription,
    Teacher,
)
from ontu_schedule_bot.utils import PAIR_START_TIME

current_client = contextvars.ContextVar("current_client")
current_update = contextvars.ContextVar("update")
logger = logging.getLogger(__name__)


def get_current_client() -> AdminClient:
    """Gets current admin client from contextvar"""
    try:
        client = current_client.get()
    except LookupError:
        client = AdminClient()
        current_client.set(client)
    return client


def get_current_update() -> Update:
    """Gets current update from contextvar"""
    try:
        update = current_update.get()
    except LookupError as e:
        raise RuntimeError("No update in context") from e
    return update


async def get_chat_info(
    update: Update,
) -> Chat:
    """Gets chat info from admin service"""
    telegram_chat = update.effective_chat
    if not telegram_chat:
        raise RuntimeError("No chat in update")

    client = get_current_client()

    chat_id = str(telegram_chat.id)

    if (
        telegram_chat.is_forum
        and update.effective_message
        and update.effective_message.is_topic_message
        and update.effective_message.message_thread_id
    ):
        chat_id += f":{update.effective_message.message_thread_id}"

    return client.get_chat(chat_id=chat_id)


async def get_subscription_info(
    chat: Chat,
) -> Subscription:
    """Gets subscription info from admin service"""
    client = get_current_client()

    return client.get_subscription(chat_id=chat.platform_chat_id)


async def start_command(
    update: Update,
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Executed when user initiates conversation, or returns to main menu"""
    telegram_chat = update.effective_chat
    message = update.effective_message

    if not telegram_chat or not message:
        return

    await messages.processing_update(update=update)

    client = AdminClient()

    if message.message_thread_id:
        telegram_chat_id = f"{telegram_chat.id}:{message.message_thread_id}"
    else:
        telegram_chat_id = str(telegram_chat.id)

    chat = client.get_or_create_chat(
        chat_info=CreateChatRequest(
            platform=Platform.TELEGRAM,
            platform_chat_id=telegram_chat_id,
            title=telegram_chat.title or telegram_chat.full_name or "No Name",
            username=telegram_chat.username or None,
            first_name=telegram_chat.first_name or None,
            last_name=telegram_chat.last_name or None,
            language_code=update.effective_user.language_code if update.effective_user else None,
            additional_info={
                "type": telegram_chat.type,
                "is_forum": telegram_chat.is_forum,
                "topic_id": message.message_thread_id,
            },
        )
    )

    subscription = client.get_subscription(chat_id=chat.platform_chat_id)

    await messages.start_command(
        update=update,
        chat=chat,
        subscription=subscription,
    )


async def manage_subscription(
    update: "Update",
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Starts the process of updating the subscription:
    - Choose wether modifying groups or teachers;
    - Proceed to choose between adding and removing subscription items;
    - Finally, choose specific groups/teachers to add/remove.
    """
    await messages.processing_update(update=update)

    chat = await get_chat_info(update=update)

    await messages.manage_subscription(
        update=update,
        chat=chat,
    )


async def manage_subscription_groups(
    update: "Update",
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Continues the process of updating the subscription by focusing on groups only.
    """
    await messages.processing_update(update=update)

    chat = await get_chat_info(update=update)

    subscription = await get_subscription_info(chat=chat)

    await messages.manage_subscription_groups(
        update=update,
        chat=chat,
        subscription=subscription,
    )


async def manage_subscription_teachers(
    update: "Update",
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Continues the process of updating the subscription by focusing on teachers only.
    """
    await messages.processing_update(update=update)

    chat = await get_chat_info(update=update)

    subscription = await get_subscription_info(chat=chat)

    await messages.manage_subscription_teachers(
        update=update,
        chat=chat,
        subscription=subscription,
    )


async def remove_subscription_items(
    update: "Update",
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Continues the process of updating the subscription by focusing on removing items.
    """
    await messages.processing_update(update=update)

    if not update.callback_query or not update.callback_query.data:
        raise ValueError("remove_subscription_items is designed for callbacks")

    item_type: Literal["group", "teacher"] = update.callback_query.data[1]  # type: ignore

    chat = await get_chat_info(update=update)

    subscription = await get_subscription_info(chat=chat)

    await messages.remove_subscription_items(
        update=update,
        chat=chat,
        subscription=subscription,
        item_type=item_type,
    )


async def remove_subscription_item(
    update: "Update",
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Finalizes the process of updating the subscription by removing specific item.
    """
    await messages.processing_update(update=update)

    if not update.callback_query or not update.callback_query.data:
        raise ValueError("remove_subscription_item is designed for callbacks")

    item_type: Literal["group", "teacher"] = update.callback_query.data[1]  # type: ignore
    item: Teacher | Group = update.callback_query.data[2]  # type: ignore

    chat = await get_chat_info(update=update)

    client = get_current_client()

    if item_type == "group":
        subscription = client.remove_group(
            chat_id=chat.platform_chat_id,
            group_id=item.uuid,
        )
    elif item_type == "teacher":
        subscription = client.remove_teacher(
            chat_id=chat.platform_chat_id,
            teacher_id=item.uuid,
        )
    else:
        raise RuntimeError("Unsupported item type")

    await messages.remove_subscription_items(
        update=update,
        chat=chat,
        subscription=subscription,
        item_type=item_type,
    )


async def add_subscription_group(
    update: "Update",
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Starts the process of adding a group to the subscription.

    First users have to select a faculty, then a group within that faculty.
    Since there might be quite a lot of groups, pagination is implemented.
    """
    await messages.processing_update(update=update)

    chat = await get_chat_info(update=update)

    client = get_current_client()

    faculties = client.read_faculties()

    await messages.add_subscription_group(
        update=update,
        chat=chat,
        faculties=faculties.items,
    )


async def add_subscription_teacher(
    update: "Update",
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Starts the process of adding a teacher to the subscription.

    First users have to select a department, then a teacher within that department.
    Since there might be quite a lot of teachers, pagination is implemented.
    """
    await messages.processing_update(update=update)

    chat = await get_chat_info(update=update)

    client = get_current_client()

    departments = client.read_departments()

    await messages.add_subscription_teacher(
        update=update,
        chat=chat,
        departments=departments.items,
    )


async def select_faculty(
    update: "Update",
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Continues the process of adding a group to the subscription by selecting a faculty.
    """
    await messages.processing_update(update=update)

    query = update.callback_query
    if not query or not query.message or not query.data:
        return

    faculty: Faculty = query.data[1]  # type: ignore
    page_number: int = query.data[2]  # type: ignore

    client = get_current_client()

    groups = client.read_groups(
        faculty_id=faculty.uuid,
        page=page_number,
    )

    await messages.select_faculty(
        update=update,
        faculty=faculty,
        groups=groups,
    )


async def select_department(
    update: "Update",
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Continues the process of adding a teacher to the subscription by selecting a department.
    """
    await messages.processing_update(update=update)

    query = update.callback_query
    if not query or not query.message or not query.data:
        return

    department: Department = query.data[1]  # type: ignore
    page_number: int = query.data[2]  # type: ignore

    client = get_current_client()

    teachers = client.read_teachers(
        department_id=department.uuid,
        page=page_number,
    )

    await messages.select_department(
        update=update,
        department=department,
        teachers=teachers,
    )


async def add_subscription_item(
    update: "Update",
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    await messages.processing_update(update=update)

    query = update.callback_query
    if not query or not query.message or not query.data:
        return None

    item_type: Literal["group", "teacher"] = query.data[1]  # type: ignore
    item: Group | Teacher = query.data[2]  # type: ignore

    chat = await get_chat_info(update=update)

    client = get_current_client()

    if item_type == "group":
        client.add_group(
            chat_id=chat.platform_chat_id,
            group_id=item.uuid,
        )
    elif item_type == "teacher":
        client.add_teacher(
            chat_id=chat.platform_chat_id,
            teacher_id=item.uuid,
        )
    else:
        raise RuntimeError("Unsupported item type")

    return await messages.manage_subscription(
        update=update,
        chat=chat,
    )


async def send_day_schedule(chat: Chat, date: datetime.date) -> None:
    """Gets day schedule from admin service"""
    client = get_current_client()

    schedule_items = client.schedule_day(
        chat_id=chat.platform_chat_id,
        date=date,
    )

    sent = False

    for item in schedule_items:
        if not item:
            continue

        await messages.send_day_schedule(
            update=get_current_update(),
            day_schedule=item,
        )
        sent = True

    if not sent:
        await messages.send_no_classes_message(
            update=get_current_update(),
            date=date,
        )


async def get_today_schedule(
    update: "Update",
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Gets today's schedule from admin service"""
    current_update.set(update)

    await messages.processing_update(update=update)

    telegram_chat = update.effective_chat
    if not telegram_chat:
        raise RuntimeError("No chat in update")

    chat = await get_chat_info(update=update)

    today = utils.current_time_in_kiev().date()
    await send_day_schedule(chat=chat, date=today)


async def get_tomorrow_schedule(
    update: "Update",
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Gets tomorrow's schedule from admin service"""
    current_update.set(update)

    await messages.processing_update(update=update)

    telegram_chat = update.effective_chat
    if not telegram_chat:
        raise RuntimeError("No chat in update")

    chat = await get_chat_info(update=update)

    tomorrow = utils.current_time_in_kiev().date() + datetime.timedelta(days=1)
    await send_day_schedule(chat=chat, date=tomorrow)


async def next_pair(  # noqa: C901
    update: "Update",
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Performs a check of current time.

    If current time is past the start of the last pair, performs same checks with the next day.
    Note: Once using next day's schedule, ignores time checks and returns first pair with non-empty lessons.

    If current time is not past the start of the last pair, performs check for current day.
    Should only send the next upcoming pair. (If no more pairs today, search in tomorrow's schedule)
    """  # noqa: E501
    await messages.processing_update(update=update)

    telegram_chat = update.effective_chat
    if not telegram_chat:
        raise RuntimeError("No chat in update")

    client = get_current_client()

    chat = await get_chat_info(update=update)

    now = utils.current_time_in_kiev()
    today = now.date()

    schedule_items = client.schedule_day(
        chat_id=chat.platform_chat_id,
        date=today,
    )

    # Check for today's pairs
    for item in schedule_items:
        if not item:
            continue

        for pair in item.pairs:
            pair_start_time = datetime.datetime.combine(
                item.date,
                PAIR_START_TIME.get(pair.number, datetime.time(hour=0, minute=0)),
                tzinfo=now.tzinfo,
            )

            if pair_start_time < now:
                continue

            if pair.lessons:
                await messages.send_pair_details(
                    update=update,
                    pair=pair,
                    day_schedule=item,
                )
                return

    delta = 1

    # Find the next closest pair in the upcoming days
    while delta <= 7:  # noqa: PLR2004
        date = today + datetime.timedelta(days=delta)
        schedule_items = client.schedule_day(
            chat_id=chat.platform_chat_id,
            date=date,
        )

        for item in schedule_items:
            if not item:
                continue

            for pair in item.pairs:
                if pair.lessons:
                    await messages.send_pair_details(
                        update=update,
                        pair=pair,
                        day_schedule=item,
                    )
                    return
        delta += 1

    await messages.send_no_classes_message(
        update=update,
        date=today,
    )


async def get_week_schedule(
    update: "Update",
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Gets weekly schedule from admin service"""
    current_update.set(update)

    await messages.processing_update(update=update)

    telegram_chat = update.effective_chat
    if not telegram_chat:
        raise RuntimeError("No chat in update")

    client = get_current_client()

    chat = await get_chat_info(update=update)

    schedule_items = client.schedule_week(
        chat_id=chat.platform_chat_id,
    )

    for item in schedule_items:
        if not item:
            continue

        await messages.send_week_schedule(
            update=get_current_update(),
            week_schedule=item,
        )


async def get_pair_details(
    update: Update,
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    current_update.set(update)

    await messages.processing_update(update=update)

    query = update.callback_query
    if not query or not query.message or not query.data:
        raise ValueError("get_pair_details is designed for callbacks")

    pair: Pair = query.data[1]  # type: ignore
    day: DaySchedule = query.data[2]  # type: ignore

    await messages.send_pair_details(
        update=update,
        pair=pair,
        day_schedule=day,
    )


async def get_schedule(
    update: Update,
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    current_update.set(update)

    await messages.processing_update(update=update)

    query = update.callback_query
    if not query or not query.message or not query.data:
        raise ValueError("get_schedule is designed for callbacks")

    day_schedule: DaySchedule = query.data[1]  # type: ignore

    telegram_chat = update.effective_chat
    if not telegram_chat:
        raise RuntimeError("No chat in update")

    await messages.send_day_schedule(
        update=get_current_update(),
        day_schedule=day_schedule,
    )


async def manual_batch_pair_check(
    update: Update,  # noqa: ARG001
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    await batch_pair_check(context=context)


async def process_record(
    record: dict[str, list[DaySchedule | None]],
    now: datetime.datetime,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    for chat_id, schedules in record.items():
        message_thread_id = None

        if chat_id.find(":") != -1:
            chat_id, message_thread_id = chat_id.split(":", 1)  # noqa: PLW2901
            message_thread_id = int(message_thread_id)

        for schedule in schedules:
            if not schedule:
                continue

            for pair in schedule.pairs:
                pair_start_time = datetime.datetime.combine(
                    schedule.date,
                    PAIR_START_TIME.get(pair.number, datetime.time(hour=0, minute=0)),
                    tzinfo=now.tzinfo,
                )

                if pair_start_time < now:
                    continue

                if pair.lessons:
                    try:
                        await messages.send_pair_details_with_bot(
                            bot=context.bot,
                            chat_id=chat_id,
                            message_thread_id=message_thread_id,
                            pair=pair,
                            day_schedule=schedule,
                        )
                    except telegram.error.Forbidden as e:
                        logger.warning(
                            f"Cannot send message to chat {chat_id} "
                            f"(message_thread_id={message_thread_id}): {e}",
                        )
                else:
                    # Only send the next upcoming pair for each schedule
                    break


async def batch_pair_check(
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    start_time = time.time()

    client = get_current_client()

    batch_generator = client.bulk_schedule()

    now = utils.current_time_in_kiev()

    for record in batch_generator:
        try:
            await process_record(record=record, now=now, context=context)
        except Exception as e:
            logger.error(f"Error processing record: {e}", exc_info=True)
            await send_message_to_debug_chat(
                context=context,
                message=get_error_message_text(
                    error=e,
                    context=context,
                    base_error_message="Error processing record in batch pair check",
                ),
            )

    end_time = time.time()

    duration = end_time - start_time

    await send_message_to_debug_chat(
        context=context,
        message=f"Batch pair check completed in {round(duration, 2)} seconds.",
    )


async def toggle_subscription(
    update: Update,
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Toggles subscription on/off"""
    await messages.processing_update(update=update)

    chat = await get_chat_info(update=update)

    client = get_current_client()

    subscription = client.toggle_subscription(chat_id=chat.platform_chat_id)

    await messages.start_command(
        update=update,
        chat=chat,
        subscription=subscription,
    )


def get_error_message_text(
    error: Exception,
    context: ContextTypes.DEFAULT_TYPE,
    update: object | None = None,
    base_error_message: str = "An exception was raised while handling an update",
) -> str:
    tb_list = traceback.format_exception(
        None,
        error,
        error.__traceback__,
    )

    tb_string = "".join(tb_list)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)

    return (
        f"{base_error_message}\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False, default=repr))}"  # noqa: E501
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )


async def send_message_to_debug_chat(
    context: ContextTypes.DEFAULT_TYPE,
    message: str,
) -> None:
    """Sends a message to the debug chat"""
    chunks = [message]
    if len(message) > 4096:  # noqa: PLR2004
        chunks = utils.split_message(message, 4000)

    for text in chunks:
        await context.bot.send_message(
            chat_id=settings.DEBUG_CHAT_ID,
            text=text,
            parse_mode=ParseMode.HTML,
        )


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)

    assert context.error is not None

    message = get_error_message_text(
        error=context.error,
        context=context,
        update=update,
    )

    await send_message_to_debug_chat(
        context=context,
        message=message,
    )

    if isinstance(update, Update) and update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                "Виникла помилка при обробці вашого запиту.\nСпробуйте його повторити, однак, "  # noqa: RUF001
                "якщо це не допоможе, то адміністратори вже повідомлені і працюють над усуненням "  # noqa: RUF001
                "проблем.\nВибачте за незручності.\n\n"  # noqa: RUF001
                "Якщо ви хочете уточнити щось по своїй проблемі (наприклад - додати інформацію) "
                f'вкажіть наступну інформацію: <code>"update_id": {update.update_id}</code>'
            ),
            parse_mode=ParseMode.HTML,
        )
