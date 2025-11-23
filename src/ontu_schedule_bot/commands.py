"""This module contains all the commands bot may execute"""

import contextvars
import datetime
import logging
import time
from typing import Literal

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.constants import ParseMode
from telegram.error import Forbidden
from telegram.ext import ContextTypes

from ontu_schedule_bot import classes, decorators, utils
from ontu_schedule_bot.settings import settings
from ontu_schedule_bot.third_party.admin.client import AdminClient
from ontu_schedule_bot.third_party.admin.enums import Platform
from ontu_schedule_bot.third_party.admin.schemas import (
    Chat,
    CreateChatRequest,
    Department,
    Faculty,
    Group,
    Subscription,
    Teacher,
)
from ontu_schedule_bot import messages
from ontu_schedule_bot.utils import PAIR_START_TIME


current_client = contextvars.ContextVar("current_client")
current_update = contextvars.ContextVar("update")


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
    except LookupError:
        raise RuntimeError("No update in context")
    return update


async def get_chat_info(
    update: Update,
) -> Chat:
    """Gets chat info from admin service"""
    telegram_chat = update.effective_chat
    if not telegram_chat:
        raise RuntimeError("No chat in update")

    client = get_current_client()

    return client.get_chat(chat_id=str(telegram_chat.id))


async def get_subscription_info(
    chat: Chat,
) -> Subscription:
    """Gets subscription info from admin service"""
    client = get_current_client()

    return client.get_subscription(chat_id=chat.platform_chat_id)


# TODO: Deprecate `reply_with_exception` decorator
# Use error handling provided by telegram.ext.Application instead


@decorators.reply_with_exception
async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    base_text: str | None = None,
) -> None:
    """Executed when user initiates conversation, or returns to main menu"""
    telegram_chat = update.effective_chat
    message = update.effective_message

    if not telegram_chat or not message:
        return

    await messages.processing_update(update=update)

    client = AdminClient()

    chat = client.get_or_create_chat(
        chat_info=CreateChatRequest(
            platform=Platform.TELEGRAM,
            platform_chat_id=str(telegram_chat.id),
            title=telegram_chat.title or telegram_chat.full_name or "No Name",
            username=telegram_chat.username or None,
            first_name=telegram_chat.first_name or None,
            last_name=telegram_chat.last_name or None,
            language_code=update.effective_user.language_code
            if update.effective_user
            else None,
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
        return

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

    client = get_current_client()

    chat = client.get_chat(chat_id=str(telegram_chat.id))

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

    client = get_current_client()

    chat = client.get_chat(chat_id=str(telegram_chat.id))

    tomorrow = utils.current_time_in_kiev().date() + datetime.timedelta(days=1)
    await send_day_schedule(chat=chat, date=tomorrow)


async def next_pair(
    update: "Update",
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Performs a check of current time.

    If current time is past the start of the last pair, performs same checks with the next day.
    Note: Once using next day's schedule, ignores time checks and returns first pair with non-empty lessons.

    If current time is not past the start of the last pair, performs check for current day.
    Should only send the next upcoming pair. (If no more pairs today, search in tomorrow's schedule.)
    """
    await messages.processing_update(update=update)

    telegram_chat = update.effective_chat
    if not telegram_chat:
        raise RuntimeError("No chat in update")

    client = get_current_client()

    chat = client.get_chat(chat_id=str(telegram_chat.id))

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
            )
            if pair_start_time > now and pair.lessons:
                await messages.send_lesson_details(
                    update=update,
                    pair=pair,
                    day_schedule=item,
                )
                return

    delta = 1

    while delta <= 7:
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
                    await messages.send_lesson_details(
                        update=update,
                        pair=pair,
                        day_schedule=item,
                    )
                    return

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

    chat = client.get_chat(chat_id=str(telegram_chat.id))

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


# TODO: Replace this method
@decorators.reply_with_exception
async def get_pair_details(update: Update, _):
    """Sends pair's details"""
    query = update.callback_query
    if not query or not query.message or not query.data:
        raise ValueError("get_day_details is designed for callbacks")

    await query.answer(text="Будь-ласка, зачекайте")

    callback_data: tuple[str, classes.Pair, classes.Day] = tuple(query.data)  # type: ignore

    pair = callback_data[1]
    day = callback_data[2]

    keyboard = [
        [InlineKeyboardButton(text="Назад ⤴️", callback_data=("day_details", day))]
    ]

    await query.message.edit_text(
        text=pair.as_text(day_name=day.name),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )


# TODO: Replace batch processing
@decorators.reply_with_exception
async def batch_pair_check_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """This method is used to check for upcoming pairs"""
    if not update.effective_chat:
        return
    if update.effective_chat.id != settings.DEBUG_CHAT_ID:
        return

    await batch_pair_check(context=context, _=update)


@decorators.reply_with_exception
async def batch_pair_check(
    context: ContextTypes.DEFAULT_TYPE, _: Update | None = None
) -> None:
    """This method is used to check for upcoming pairs"""
    start_time = time.time()
    batch = utils.Getter().get_batch_schedule()

    for group in batch:
        chat_infos: list[dict[str, int]] = group["chat_info"]  # type: ignore
        for chat_info in chat_infos:
            # type: ignore
            schedule: "utils.classes.Schedule" = group["schedule"]
            pair, string = schedule.get_next_pair(find_all=False)
            if not pair:
                continue
            pair_as_text = pair.as_text(day_name=string)
            try:
                await context.bot.send_message(
                    chat_id=chat_info["chat_id"],
                    message_thread_id=chat_info["topic_id"],
                    text=pair_as_text,
                    parse_mode="HTML",
                )
            except Forbidden as exc:
                logging.exception(exc)
                await context.bot.send_message(
                    chat_id=settings.DEBUG_CHAT_ID,
                    text=f"Користувач заблокував бота: {chat_info=}\nВ методі batch_pair_check",
                )
                continue
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logging.exception(exc)
                await decorators.send_exception(
                    bot=context.bot,
                    exception=exc,
                    func=context.bot.send_message,
                    bot_token=context.bot.token,
                    kwargs={
                        "chat_info": chat_info,
                        "text": pair_as_text,
                        "parse_mode": "HTML",
                    },
                )
                continue

    end_time = time.time()

    await context.bot.send_message(
        chat_id=settings.DEBUG_CHAT_ID,
        text=f"Batch pair check finished in {end_time - start_time:.2f} seconds",
        disable_notification=True,
    )


# TODO: Replace this method


@decorators.reply_with_exception
async def toggle_subscription(update: Update, _):
    """This method toggles current state of subscription"""
    query = update.callback_query

    if not query or not update.effective_chat:
        raise ValueError("Improper method usage")

    if not query.message or not query.data:
        raise ValueError("Incomplete data :(")

    data: tuple[str, classes.Chat] = tuple(query.data)  # type: ignore

    chat = data[1]
    if not chat.subscription:
        raise ValueError("В вас ще немає підписки! Здається ви мені бота зламали...")

    new_status = not chat.subscription.is_active

    if chat.subscription.group:
        utils.Setter().set_chat_group(
            message=update.effective_message,
            group=chat.subscription.group,
            is_active=new_status,
        )
    if chat.subscription.teacher:
        utils.Setter().set_chat_teacher(
            message=update.effective_message,
            teacher=chat.subscription.teacher,
            is_active=new_status,
        )

    if new_status:
        status = "активна"
    else:
        status = "вимкнена"

    await query.answer(text=f"Ваша підписка тепер {status}", show_alert=True)

    await start_command(update=update, context=_)


@decorators.reply_with_exception
async def send_message_campaign(
    update: Update,
    _: ContextTypes.DEFAULT_TYPE,
):
    """Allows to send batch messages to users"""
    message = update.effective_message
    if not message or not message.text:
        return

    if message.chat.id != settings.DEBUG_CHAT_ID:
        return

    text = message.text.replace("/send_campaign ", "")
    campaign = utils.Getter().get_message_campaign(text)

    if not campaign:
        await message.reply_text("Не вдалося знайти повідомлення - перевірте логи.")
        return

    chats_list = set(campaign.to_chats)

    await message.reply_text("Починаю надсилати повідомлення")
    await message.reply_text(
        text=campaign.message,
        parse_mode=ParseMode.HTML,
    )

    start = time.time()

    for chat_id in chats_list:
        utils.send_message_to_telegram(
            bot_token=message.get_bot().token,
            chat_id=chat_id,
            topic_id=None,
            text=campaign.message,
        )

    end = time.time()

    await message.reply_text(
        f"Повідомлення надіслано всім отримувачам за {round(end - start, 2)} секунд"
    )
