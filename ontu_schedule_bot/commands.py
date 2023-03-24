"""This module contains all the commands bot may execute"""
from telegram import InlineKeyboardButton, Update, InlineKeyboardMarkup, Message
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import utils
import classes
import enums
import decorators


@decorators.reply_with_exception
async def start_command(update: Update, _) -> None:
    """Executed when user initiates conversation, or returns to main menu"""
    telegram_chat = update.effective_chat
    if not telegram_chat:
        return

    await telegram_chat.send_chat_action(
        action="typing"
    )

    chat_entity = None
    try:
        chat_entity = utils.Getter().get_chat(
            telegram_chat.id
        )
    except ValueError as error:
        print(error)
    if not chat_entity:
        chat_entity = utils.Setter().new_chat(
            chat=telegram_chat
        )
        if not isinstance(chat_entity, classes.Chat):
            raise ValueError(
                "Could not create chat for whatever reason!"
            )

    keyboard = []
    if chat_entity.subscription:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "Оновити отримання розкладу",
                    callback_data=("set_group", )
                ),
            ]
        )
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="Переключити отримання розкладу",
                    callback_data=("toggle_subscription", chat_entity)
                )
            ]
        )
    else:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "Отримувати розклад",
                    callback_data=("set_group", )
                ),
            ]
        )

    kwargs = {
        "text": "Чим можу допомогти?",
        "reply_markup": InlineKeyboardMarkup(
            inline_keyboard=keyboard
        ),
    }

    if update.callback_query and update.callback_query.message:
        await update.callback_query.message.edit_text(
            **kwargs
        )
    elif update.message:
        await update.message.reply_html(
            **kwargs
        )


@decorators.reply_with_exception
async def faculty_select(update: Update, _) -> int:
    """This command sends a list of faculties to choose for subscription"""
    query = update.callback_query
    if not query or not query.message:
        return -1
    await query.answer()

    keyboard = []

    faculties = utils.Getter().get_faculties()
    for faculty in faculties:
        keyboard.append(
            [
                InlineKeyboardButton(
                    faculty.name,
                    callback_data=("pick_faculty", faculty.name)
                )
            ]
        )
    keyboard.append(
        [
            InlineKeyboardButton(
                "Назад ⤴️",
                callback_data=("start", )
            )
        ]
    )

    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )


    await query.message.edit_text(
        text="Будь-ласка - оберіть факультет:",
        reply_markup=reply_markup
    )
    return 0


def _back_forward_buttons_get(
        page: int,
        query_data: list) -> tuple[tuple, tuple]:
    """This method encapsulates logics to get forward and backwards buttons"""
    back_list: list[str | int] = query_data.copy()
    forward_list: list[str | int] = query_data.copy()

    if len(query_data) > enums.PAGE_INDEX:
        back_list[2] = page - 1 if page - 1 >= 0 else 0
        forward_list[2] = page + 1
    else:
        back_list.append(page)
        forward_list.append(page+1)
    return tuple(back_list), tuple(forward_list)


@decorators.reply_with_exception
async def group_select(update: Update, _) -> None:
    """This command sends a list of groups of some faculty to choose for subscription"""
    query = update.callback_query
    if not query or not query.message:
        return
    await query.answer("Будь-ласка, зачекайте")

    if not query.data:
        return

    data: tuple[str, str, int] = tuple(query.data)  # type: ignore

    if len(data) < enums.FACULTY_NAME_INDEX + 1:
        return

    if len(data) < enums.PAGE_INDEX + 1:
        page: int = 0
    else:
        page: int = data[enums.PAGE_INDEX]

    keyboard = []

    groups = utils.Getter().get_groups(
        faculty_name=data[enums.FACULTY_NAME_INDEX]
    )
    number_of_pages = utils.get_number_of_pages(
        groups  # type: ignore
    )
    current_page: list[classes.Group] = utils.get_current_page(
        list_of_elements=groups,  # type: ignore
        page=page
    )
    for group in current_page:
        keyboard.append(
            [
                InlineKeyboardButton(
                    group.name,
                    callback_data=("pick_group", group)
                )
            ]
        )

    back_tuple, forward_tuple = _back_forward_buttons_get(
        page=page,
        query_data=list(data)
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                "◀️",
                callback_data=back_tuple
            ),
            InlineKeyboardButton(
                "Назад ⤴️",
                callback_data=("set_group", )
            ),
            InlineKeyboardButton(
                "▶️",
                callback_data=forward_tuple
            ),
        ]
    )

    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )

    await query.message.edit_text(
        text=f"Тепер - оберіть групу\nCторінка {page+1}/{number_of_pages}",
        reply_markup=reply_markup
    )


@decorators.reply_with_exception
async def group_set(update: Update, _) -> None:
    """This command activates a subscription"""
    if not update.effective_chat:
        return

    query = update.callback_query
    if not query or not query.message:
        return
    await query.answer()

    if not query.data:
        return

    data: tuple[str, classes.Group] = tuple(query.data)  # type: ignore
    group_index = 1
    group: classes.Group = data[group_index]
    subscription = utils.Setter().set_chat_group(
        chat=update.effective_chat,
        group=group
    )
    if isinstance(subscription, dict):
        raise ValueError(
            "Instead of subscription - got response from server",
            subscription
        )
    await query.message.reply_html(
        "Відтепер ви будете отримувати розклад для групи: "
        f"{subscription.group.name} факультету {subscription.group.faculty.name}"
    )


@decorators.reply_with_exception
async def pair_check_for_group(
        chat: classes.Chat,
        find_all: bool = False,
        check_subscription_is_active: bool = False) -> str | bool:
    """
    Returns False if there's no pair, pair as string if there is a lesson

    If check_subscription_is_active is True - if subscription is not active - will not send anything
    """
    if not chat.subscription:
        return False

    if check_subscription_is_active:
        if not chat.subscription.is_active:
            return False

    schedule = utils.Getter().get_schedule(
        chat.subscription.group
    )

    data = schedule.get_next_pair(find_all=find_all)

    if not data:
        return False

    next_pair = data[0]
    day_name = data[1]

    return next_pair.as_text(day_name=day_name)


@decorators.reply_with_exception
async def pair_check_per_chat(update: Update, _) -> None:
    """This method will get a next pair for current chat"""
    if not update.effective_chat or not update.message:
        return

    if update.effective_chat:
        await update.effective_chat.send_chat_action(
            action="typing"
        )

    chat_id = update.effective_chat.id
    chat = utils.get_chat_by_tg_chat(
        chat_id=chat_id
    )

    next_pair_text = await pair_check_for_group(chat, find_all=True)
    if next_pair_text is None:
        await update.message.reply_html(
            text="Не вдалося отримати наступну пару :(\nСпробуйте /start"
        )
    elif isinstance(next_pair_text, str):
        await update.message.reply_html(
            text=next_pair_text
        )
    elif next_pair_text is False:
        await update.message.reply_html(
            text="У вас немає наступної пари"
        )


async def send_week_schedule(message: Message, week_schedule: list[classes.Day]):
    """Common sender"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=day.get_brief(),
                    callback_data=('day_details', day)
                )
            ]
            for day in week_schedule
        ]
    )

    kwargs = {
        "text": "Розклад:",
        "reply_markup": keyboard,
    }

    if message.from_user and message.from_user.is_bot:
        await message.edit_text(
            **kwargs
        )
    else:
        await message.reply_html(
            **kwargs
        )


@decorators.reply_with_exception
async def get_schedule(update: Update, _) -> None:
    """This method sends back a weekly schedule message"""
    message = update.message
    if update.callback_query:
        await update.callback_query.answer(text="Будь-ласка, зачекайте")
        message = update.callback_query.message

    if update.effective_chat:
        await update.effective_chat.send_chat_action(
            action="typing"
        )

    if not update.effective_chat or not message:
        return

    chat_id = update.effective_chat.id
    group = utils.get_chat_by_tg_chat(
        chat_id=chat_id
    )
    if not group.subscription:
        raise ValueError("В чата немає підписки")

    schedule = utils.Getter().get_schedule(
        group=group.subscription.group
    )

    week_schedule = schedule.get_week_representation()

    await send_week_schedule(
        message=message,
        week_schedule=week_schedule
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

    keyboard = []
    text = f"Пари {day.name}:\n"

    details = day.get_details()
    for pair, representation in details.items():
        text += representation + "\n"
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{pair.pair_no}",
                    callback_data=("pair_details", pair, day)
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                text="Назад ⤴️",
                callback_data=("get_schedule", )
            )
        ]
    )

    await query.message.edit_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )

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
        [
            InlineKeyboardButton(
                text="Назад ⤴️",
                callback_data=("day_details", day)
            )
        ]
    ]

    await query.message.edit_text(
        text=pair.as_text(day_name=day.name),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )


async def pair_check(context: ContextTypes.DEFAULT_TYPE) -> None:
    """This method is used to check for upcoming pairs"""
    job = context.job
    if not job:
        return

    all_chats = utils.Getter().get_all_chats()
    for chat in all_chats:
        result = await pair_check_for_group(
            chat=chat,
            find_all=False,
            check_subscription_is_active=True
        )
        if not result:
            continue
        await context.bot.send_message(
            chat.chat_id,
            f"{result}",
            parse_mode=ParseMode.HTML,
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

    utils.Setter().set_chat_group(
        chat=update.effective_chat,
        group=chat.subscription.group,
        is_active=new_status
    )

    if new_status:
        status = "активна"
    else:
        status = "вимкнена"

    await query.answer(
        text=f"Ваша підписка тепер {status}",
        show_alert=True
    )
