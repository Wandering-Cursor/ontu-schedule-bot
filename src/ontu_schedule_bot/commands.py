"""This module contains all the commands bot may execute"""

import contextvars
import logging
import time
from typing import Literal

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.constants import ChatType, ParseMode
from telegram.error import Forbidden
from telegram.ext import ContextTypes

from ontu_schedule_bot import classes, decorators, enums, utils
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


current_client = contextvars.ContextVar("current_client")


def get_current_client() -> AdminClient:
    """Gets current admin client from contextvar"""
    try:
        client = current_client.get()
    except LookupError:
        client = AdminClient()
        current_client.set(client)
    return client


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


@decorators.reply_with_exception
async def pair_check_for_group(
    chat: classes.Chat,
    find_all: bool = False,
    check_subscription_is_active: bool = False,
) -> tuple[bool, str]:
    """
    Returns False if there's no pair, pair as string if there is a lesson

    If check_subscription_is_active is True - if subscription is not active - will not send anything
    """
    if not chat.subscription:
        return False, "Немає підписки"

    if check_subscription_is_active:
        if not chat.subscription.is_active:
            return False, "Підписка не активна"

    schedule = utils.Getter().get_schedule(chat.subscription)

    pair, string = schedule.get_next_pair(find_all=find_all)

    if not pair:
        return False, string

    return True, pair.as_text(day_name=string)


@decorators.reply_with_exception
async def pair_check_per_chat(update: Update, _) -> None:
    """This method will get a next pair for current chat"""
    if not update.effective_chat or not update.message:
        return

    if update.effective_chat:
        await update.effective_chat.send_chat_action(action="typing")

    message = update.effective_message
    chat = utils.get_chat_from_message(message)

    got_pair, next_pair_text = await pair_check_for_group(
        chat,
        find_all=True,
        check_subscription_is_active=False,
    )
    if not got_pair:
        await update.message.reply_html(
            text=(
                "Не вдалося отримати наступну пару. Можлива причина:"
                f"\n\n{next_pair_text}"
                "\n\n<i>(Перевірте /schedule)</i>"
            )
        )
        return

    await update.message.reply_html(text=next_pair_text)


@decorators.reply_with_exception
async def send_week_schedule(
    message: Message,
    week_schedule: list[classes.Day],
    group: classes.Group | None = None,
    is_updated: bool = False,
):
    """Common sender"""

    message_text = "Розклад:"
    notbot_keyboard = []
    if not is_updated and group:
        notbot_keyboard = [
            [
                InlineKeyboardButton(
                    text="Оновити кеш 🔃",
                    callback_data=("update_cache", group),
                ),
            ]
        ]
    elif is_updated:
        message_text = "Розклад (оновлено):"

    days = [
        [
            InlineKeyboardButton(
                text=day.get_brief(),
                callback_data=("day_details", day),
            )
        ]
        for day in week_schedule
    ]

    inline_keyboard = days + notbot_keyboard

    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    kwargs = {
        "text": message_text,
        "reply_markup": keyboard,
    }

    if message.from_user and message.from_user.is_bot:
        await message.edit_text(**kwargs)
    else:
        await message.reply_html(**kwargs)


@decorators.reply_with_exception
async def get_schedule(update: Update, _) -> None:
    """This method sends back a weekly schedule message"""
    message = update.effective_message
    if update.callback_query:
        await update.callback_query.answer(text="Будь-ласка, зачекайте")
        message = update.callback_query.message

    if update.effective_chat:
        await update.effective_chat.send_chat_action(action="typing")

    if not update.effective_chat or not message:
        return

    group = utils.get_chat_from_message(message=message)
    if not group.subscription:
        await message.reply_text("Будь-ласка, спочатку підпишіться за допомогою /start")
        return

    schedule = utils.Getter().get_schedule(subscription=group.subscription)

    week_schedule = schedule.get_week_representation()

    await send_week_schedule(
        message=message,
        week_schedule=week_schedule,
        group=group.subscription.group,
    )


@decorators.reply_with_exception
async def send_day_details(day: classes.Day, message: Message, send_new: bool = False):
    """A `helper` method to send details of the day

    Args:
        day (classes.Day): A day that we need to send
        message (Message): Message of bot or human
        send_new (bool, optional): If True - new message will be sent. Defaults to False.
    """
    keyboard = []
    text = f"Пари {day.name}:\n"

    details = day.get_details()
    for pair, representation in details.items():
        text += representation + "\n"
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{pair.pair_no}",
                    callback_data=("pair_details", pair, day),
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                text="Назад ⤴️",
                callback_data=("get_schedule",),
            )
        ]
    )

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    if not send_new:
        await message.edit_text(
            text=text,
            reply_markup=markup,
        )
    else:
        await message.reply_text(
            text=text,
            reply_markup=markup,
        )


@decorators.reply_with_exception
async def get_day_details(update: Update, _):
    """
    Callback data contains:
        1. string
        2. day
    """

    query = update.callback_query
    if not query or not query.message or not query.data:
        raise ValueError("get_day_details is designed for callbacks")

    await query.answer(text="Будь-ласка, зачекайте")

    callback_data: tuple[str, classes.Day] = tuple(query.data)  # type: ignore

    day = callback_data[1]

    await send_day_details(day=day, message=query.message)


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


@decorators.reply_with_exception
async def send_pair_check_result(
    chat: classes.Chat, context: ContextTypes.DEFAULT_TYPE
):
    """
    Extracting this because I was hoping it'll run async, but it doesn't :)
    """
    got_pair, text = await pair_check_for_group(
        chat=chat,
        find_all=False,
        check_subscription_is_active=True,
    )

    if not got_pair:
        return

    utils.send_message_to_telegram(
        bot_token=context.bot.token,
        chat_id=chat.chat_id,
        topic_id=chat.topic_id,
        text=text,
    )


@decorators.reply_with_exception
async def pair_check(context: ContextTypes.DEFAULT_TYPE) -> None:
    """This method is used to check for upcoming pairs"""
    all_chats = utils.Getter().get_all_chats()
    for chat in all_chats:
        try:
            await send_pair_check_result(chat=chat, context=context)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logging.exception(exc)
            await decorators.send_exception(
                bot=context.bot,
                exception=exc,
                func=send_pair_check_result,
                bot_token=context.bot.token,
                kwargs={
                    "chat": chat,
                    "context": context,
                },
            )


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
async def get_today(update: Update, _):
    """Method that returns a `schedule` like message for this day

    Args:
        update (Update): Telegram Update (with message...)
        _ (_type_): Redundant telegram bot argument
    """
    message = update.effective_message
    if update.effective_chat:
        await update.effective_chat.send_chat_action(action="typing")

    if not update.effective_chat or not message:
        raise ValueError("Update doesn't contain chat info")

    group = utils.get_chat_from_message(message=message)
    if not group.subscription:
        await message.reply_text("Будь-ласка, спочатку підпишіться за допомогою /start")
        return

    schedule = utils.Getter().get_schedule(group.subscription)
    today_schedule = schedule.get_today_representation()

    if not today_schedule:
        await message.reply_text(
            "День не було знайдено.\n"
            "Якщо сьогодні неділя - все гаразд, скористайтеся /schedule\n"
            "Якщо ж зараз інший день - повідомте @man_with_a_name"
        )
        return

    await send_day_details(day=today_schedule, message=message, send_new=True)


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
