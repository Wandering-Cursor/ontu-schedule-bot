from telegram import InlineKeyboardButton, Update, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

import utils
import classes

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Executed when user initiates conversation, or returns to main menu"""
    telegram_chat = update.effective_chat
    if not telegram_chat:
        return
    if not update.message:
        return

    chat_entity = utils.Getter().get_chat(
        telegram_chat.id
    )
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
            InlineKeyboardButton(
                faculty.name,
                callback_data=("pick_faculty", faculty.name)
            )
        )
    keyboard.append(
        InlineKeyboardButton(
            "Відмінити",
            callback_data=("cancel", )
        )
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
        keyboard.append(
            InlineKeyboardButton(
                group.name,
                callback_data=("pick_group", group)
            )
        )
    keyboard.append(
        InlineKeyboardButton(
            "Відмінити",
            callback_data=("set_group", )
        )
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
        f"{group.name} факультету {group.faculty.name}"
    )


async def pair_check(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    if not job:
        return

    await context.bot.send_message(
        253742276,
        text=f"Checked pair for: {job.data}"
    )