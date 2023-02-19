"""This module contains all the commands bot may execute"""
from telegram import InlineKeyboardButton, Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import utils
import classes
import enums


async def start_command(update: Update, _) -> None:
    """Executed when user initiates conversation, or returns to main menu"""
    telegram_chat = update.effective_chat
    if not telegram_chat:
        return

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
    back_list: list[str | int] = query_data
    forward_list: list[str | int] = query_data

    if len(query_data) > enums.PAGE_INDEX:
        back_list[2] = page - 1 if page - 1 >= 0 else 0
        forward_list[2] = page + 1
    else:
        back_list.append(page)
        forward_list.append(page+1)
    return tuple(back_list), tuple(forward_list)


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

    data: tuple[str, classes.Group] = tuple(query.data) # type: ignore
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


async def pair_check_for_group(
        chat: classes.Chat,
        find_all: bool = False) -> str | bool:
    """Returns False if there's no pair, pair as string if there is a lesson"""
    if not chat.subscription:
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


async def pair_check_per_chat(update: Update, _) -> None:
    """This method will get a next pair for current chat"""
    if not update.effective_chat or not update.message:
        return

    chat_id = update.effective_chat.id
    chat = utils.Getter().get_chat(
        chat_id=chat_id
    )
    if not chat or not chat.subscription:
        await update.message.reply_text(
            text="У вас немає підписки (Чи ви не в списку) - виправте це:\n/start"
        )
        return

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


async def pair_check(context: ContextTypes.DEFAULT_TYPE) -> None:
    """This method is used to check for upcoming pairs"""
    job = context.job
    if not job:
        return

    all_chats = utils.Getter().get_all_chats()
    for chat in all_chats:
        result = await pair_check_for_group(chat=chat)
        if not result:
            continue
        await context.bot.send_message(
            chat.chat_id,
            f"{result}"
        )
