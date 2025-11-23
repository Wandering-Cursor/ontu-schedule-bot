from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update

from ontu_schedule_bot.third_party.admin.schemas import (
    Chat,
    Department,
    Faculty,
    GroupPaginatedResponse,
    Subscription,
    TeacherPaginatedResponse,
)


async def processing_update(
    update: "Update",
) -> None:
    chat = update.effective_chat
    if chat is None:
        return

    await chat.send_chat_action(action="typing")

    if update.callback_query:
        await update.callback_query.answer(
            text="Будь-ласка, зачекайте...",
        )


async def edit_or_reply(
    update: "Update",
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> Message:
    if query := update.callback_query:
        if update_message := query.message:
            if update_message.is_accessible:
                assert isinstance(update_message, Message)

                result = await update_message.edit_text(
                    text=text,
                    reply_markup=reply_markup,
                )

                if isinstance(result, bool):
                    raise RuntimeError("Edited a non-bot message")

                return result

    if update.effective_message:
        return await update.effective_message.reply_html(
            text=text,
            reply_markup=reply_markup,
        )

    if update.effective_chat:
        return await update.effective_chat.send_message(
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )

    raise RuntimeError("No message to edit or reply to")


async def start_command(
    update: "Update",
    chat: "Chat",
    subscription: "Subscription",
) -> None:
    subscription_text = "Ви не підписані на розклад"
    keyboard = []

    if subscription.groups or subscription.teachers:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "Оновити підписку ✏️", callback_data=("manage_subscription",)
                ),
            ]
        )
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=(
                        "Отримувати повідомлення перед парою? "
                        f"{'✅' if subscription.is_active else '❌'}"
                    ),
                    callback_data=("toggle_subscription", chat),
                )
            ]
        )

        subscription_text = ""

        if subscription.groups:
            subscription_text += (
                "Ви підписані на розклад для груп\n"
                f"(пр. {', '.join([group.short_name for group in subscription.groups[:2]])})\n"
            )
        if subscription.teachers:
            subscription_text += (
                "Ви підписані на розклад для викладачів\n"
                f"(пр. {', '.join([teacher.short_name for teacher in subscription.teachers[:2]])})\n"
            )
    else:
        # Replace with subscription management (add/remove groups/teachers)
        keyboard.append(
            [
                InlineKeyboardButton(
                    "Налаштувати підписку ✏️", callback_data=("manage_subscription",)
                ),
            ]
        )

    message_text = f"Чим можу допомогти?\n\n{subscription_text}"

    await edit_or_reply(
        update=update,
        text=message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def manage_subscription(
    update: "Update",
    chat: "Chat",
) -> None:
    """
    Returns a list of options:
    - Manage groups;
    - Manage teachers;
    - Go back to main menu.
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "Керувати групами 🫂", callback_data=("manage_groups", chat)
            ),
        ],
        [
            InlineKeyboardButton(
                "Керувати викладачами 👩‍🏫", callback_data=("manage_teachers", chat)
            ),
        ],
        [
            InlineKeyboardButton(
                "Повернутися в головне меню 🔙", callback_data=("start", chat)
            ),
        ],
    ]

    await edit_or_reply(
        update=update,
        text="Що саме ви хочете налаштувати?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def manage_subscription_groups(
    update: "Update",
    chat: "Chat",
    subscription: "Subscription",
) -> None:
    """
    Shows the list of active groups in the subscription, and buttons to add/remove groups.
    """
    keyboard = []

    keyboard.append(
        [
            InlineKeyboardButton(
                text="Видалити групи 🗑️",
                callback_data=("remove_subscription_items", "group", chat),
            ),
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                "Додати групу ➕", callback_data=("add_subscription_group", chat)
            ),
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton(
                "Повернутися назад 🔙",
                callback_data=("manage_subscription", chat),
            ),
        ]
    )

    subscription_text = "Ви не підписані на жодну групу"
    if subscription.groups:
        subscription_text = "Ви підписані на розклад для груп:\n"
        subscription_text += "\n".join(
            [f"- {group.as_string()}" for group in subscription.groups]
        )

    await edit_or_reply(
        update=update,
        text=subscription_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def manage_subscription_teachers(
    update: "Update",
    chat: "Chat",
    subscription: "Subscription",
) -> None:
    """
    Shows the list of active teachers in the subscription, and buttons to add/remove teachers.
    """
    keyboard = []

    keyboard.append(
        [
            InlineKeyboardButton(
                text="Видалити викладачів 🗑️",
                callback_data=("remove_subscription_items", "teacher", chat),
            ),
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                "Додати викладача ➕", callback_data=("add_subscription_teacher", chat)
            ),
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton(
                "Повернутися назад 🔙",
                callback_data=("manage_subscription", chat),
            ),
        ]
    )

    subscription_text = "Ви не підписані на жодного викладача"
    if subscription.teachers:
        subscription_text = "Ви підписані на розклад для викладачів:\n"
        subscription_text += "\n".join(
            [f"- {teacher.as_string()}" for teacher in subscription.teachers]
        )

    await edit_or_reply(
        update=update,
        text=subscription_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def remove_subscription_items(
    update: "Update",
    chat: "Chat",
    subscription: "Subscription",
    item_type: str,
) -> None:
    """
    Shows the list of active items (groups/teachers) in the subscription to remove.
    """
    keyboard = []

    missing_items_translation = {
        "group": "Ви не підписані на жодну групу",
        "teacher": "Ви не підписані на жодного викладача",
    }

    items = []
    callback_data = ("error",)
    if item_type == "group":
        items = subscription.groups
        callback_data = ("manage_groups", chat)
    elif item_type == "teacher":
        items = subscription.teachers
        callback_data = ("manage_teachers", chat)

    go_back_button = InlineKeyboardButton(
        "Повернутися назад 🔙",
        callback_data=callback_data,
    )

    if not items:
        await edit_or_reply(
            update=update,
            text=missing_items_translation[item_type],
            reply_markup=InlineKeyboardMarkup([[go_back_button]]),
        )
        return

    for item in items:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"Видалити {item.as_string()} ❌",
                    callback_data=(
                        "remove_subscription_item",
                        item_type,
                        item,
                        chat,
                    ),
                ),
            ]
        )

    keyboard.append([go_back_button])

    await edit_or_reply(
        update=update,
        text=f"Оберіть {item_type}, який хочете видалити з підписки:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def add_subscription_group(
    update: "Update",
    chat: "Chat",
    faculties: list["Faculty"],
) -> None:
    """
    Shows the list of faculties to choose from when adding a group subscription.
    """
    keyboard = []

    for faculty in faculties:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=faculty.short_name,
                    callback_data=(
                        "select_faculty",
                        faculty,
                        1,  # Page number
                        chat,
                    ),
                ),
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "Повернутися назад 🔙",
                callback_data=("manage_groups", chat),
            ),
        ]
    )

    await edit_or_reply(
        update=update,
        text="Оберіть факультет, щоб побачити групи для підписки:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def add_subscription_teacher(
    update: "Update",
    chat: "Chat",
    departments: list["Department"],
) -> None:
    """
    Shows the list of departments to choose from when adding a teacher subscription.
    """
    keyboard = []

    for department in departments:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=department.short_name,
                    callback_data=(
                        "select_department",
                        department,
                        1,  # Page number
                        chat,
                    ),
                ),
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "Повернутися назад 🔙",
                callback_data=("manage_teachers", chat),
            ),
        ]
    )

    await edit_or_reply(
        update=update,
        text="Оберіть кафедру, щоб побачити викладачів для підписки:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def select_faculty(
    update: "Update",
    faculty: "Faculty",
    groups: GroupPaginatedResponse,
) -> None:
    """
    Shows the list of groups for the selected faculty to add to the subscription.
    """
    keyboard = []

    for group in groups.items:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=group.short_name,
                    callback_data=(
                        "add_subscription_item",
                        "group",
                        group,
                        update.effective_chat,
                    ),
                ),
            ]
        )

    pagination_row = []

    if groups.meta.has_previous:
        pagination_row.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=(
                    "select_faculty",
                    faculty,
                    groups.meta.page - 1,
                    update.effective_chat,
                ),
            ),
        )

    pagination_row.append(
        InlineKeyboardButton(
            f"{groups.meta.page}/{groups.meta.total_pages}",
            callback_data=("noop",),
        ),
    )

    if groups.meta.has_next:
        pagination_row.append(
            InlineKeyboardButton(
                "➡️",
                callback_data=(
                    "select_faculty",
                    faculty,
                    groups.meta.page + 1,
                    update.effective_chat,
                ),
            ),
        )

    keyboard.append(pagination_row)

    keyboard.append(
        [
            InlineKeyboardButton(
                "Повернутися назад 🔙",
                callback_data=("add_subscription_group", update.effective_chat),
            ),
        ]
    )

    await edit_or_reply(
        update=update,
        text=f"Оберіть групу факультету {faculty.short_name} для підписки:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def select_department(
    update: "Update",
    department: "Department",
    teachers: TeacherPaginatedResponse,
) -> None:
    """
    Shows the list of teachers for the selected department to add to the subscription.
    """
    keyboard = []

    for teacher in teachers.items:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=teacher.short_name,
                    callback_data=(
                        "add_subscription_item",
                        "teacher",
                        teacher,
                        update.effective_chat,
                    ),
                ),
            ]
        )

    pagination_row = []

    if teachers.meta.has_previous:
        pagination_row.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=(
                    "select_department",
                    department,
                    teachers.meta.page - 1,
                    update.effective_chat,
                ),
            ),
        )

    pagination_row.append(
        InlineKeyboardButton(
            f"{teachers.meta.page}/{teachers.meta.total_pages}",
            callback_data=("noop",),
        ),
    )

    if teachers.meta.has_next:
        pagination_row.append(
            InlineKeyboardButton(
                "➡️",
                callback_data=(
                    "select_department",
                    department,
                    teachers.meta.page + 1,
                    update.effective_chat,
                ),
            ),
        )

    keyboard.append(pagination_row)

    keyboard.append(
        [
            InlineKeyboardButton(
                "Повернутися назад 🔙",
                callback_data=("add_subscription_teacher", update.effective_chat),
            ),
        ]
    )

    await edit_or_reply(
        update=update,
        text=f"Оберіть викладача кафедри {department.short_name} для підписки:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
