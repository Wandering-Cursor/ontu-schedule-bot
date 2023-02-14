from telegram import InlineKeyboardButton, Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import utils
import classes

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Executed when user initiates conversation, or returns to main menu"""
    telegram_chat = update.effective_chat
    if not telegram_chat:
        return
    if not update.message:
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

    await update.message.reply_html(
        "Чим можу допомогти?",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        ),
    )


async def faculty_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
                "Відмінити",
                callback_data=("cancel", )
            )
        ]
    )

    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )


    await query.message.reply_text(
        f"Будь-ласка - оберіть факультет:",
        reply_markup=reply_markup
    )
    return 0


async def group_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.message:
        return
    await query.answer()

    if not query.data:
        return

    data = tuple(query.data)
    faculty_name_index = 1
    if len(data) < faculty_name_index + 1:
        return

    keyboard = []

    groups = utils.Getter().get_groups(
        faculty_name=data[faculty_name_index]
    )
    for group in groups:
        if len(keyboard) > 0 and len(keyboard[-1]) < 6:
            keyboard[-1].append(
                InlineKeyboardButton(
                    group.name,
                    callback_data=("pick_group", group)
                )
            )
        else:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        group.name,
                        callback_data=("pick_group", group)
                    )
                ]
            )
    keyboard.append(
        [
            InlineKeyboardButton(
                "Відмінити",
                callback_data=("set_group", )
            )
        ]
    )

    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )

    await query.message.edit_text(
        text="Тепер - оберіть групу",
        reply_markup=reply_markup
    )


async def group_set(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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


async def pair_check_for_group(chat: classes.Chat) -> str | bool | None:
    """Returns None if chat has no sub, false if there's no pair, str if there's a pair"""
    if not chat.subscription:
        return None
    schedule = utils.Getter().get_schedule(
        chat.subscription.group
    )
    next_pair = schedule.get_next_pair()
    if not next_pair.lessons:
        print("No lessons per pair")
        return False
    return next_pair.get_text()


async def pair_check_per_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

    next_pair_text = await pair_check_for_group(chat)
    if next_pair_text is None:
        await update.message.reply_text(
            text="Не вдалося отримати наступну пару :(\nСпробуйте /start"
        )
    elif isinstance(next_pair_text, str):
        await update.message.reply_text(
            text=next_pair_text
        )
    elif next_pair_text is False:
        await update.message.reply_text(
            text="У вас немає наступної пари"
        )


async def pair_check(context: ContextTypes.DEFAULT_TYPE) -> None:
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
