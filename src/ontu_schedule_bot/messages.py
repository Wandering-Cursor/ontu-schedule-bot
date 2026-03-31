import datetime

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Message, Update

from ontu_schedule_bot import utils
from ontu_schedule_bot.patterns import Patterns, SubscriptionItemType
from ontu_schedule_bot.third_party.admin.schemas import (
    DaySchedule,
    Department,
    Faculty,
    GroupPaginatedResponse,
    Pair,
    Subscription,
    TeacherPaginatedResponse,
    WeekSchedule,
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
    if query := update.callback_query:  # noqa: SIM102
        if (update_message := query.message) and update_message.is_accessible:
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
    subscription: "Subscription",
) -> None:
    subscription_text = "Ви не підписані на розклад"
    keyboard = []

    if subscription.groups or subscription.teachers:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "Оновити підписку ✏️",
                    callback_data=Patterns.MANAGE_SUBSCRIPTION.with_args(),
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
                    callback_data=Patterns.TOGGLE_SUBSCRIPTION.with_args(),
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
                f"(пр. {', '.join([teacher.short_name for teacher in subscription.teachers[:2]])})\n"  # noqa: E501
            )
    else:
        # Replace with subscription management (add/remove groups/teachers)
        keyboard.append(
            [
                InlineKeyboardButton(
                    "Налаштувати підписку ✏️",
                    callback_data=Patterns.MANAGE_SUBSCRIPTION.with_args(),
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
                "Керувати групами 🫂",
                callback_data=Patterns.MANAGE_GROUPS.with_args(),
            ),
        ],
        [
            InlineKeyboardButton(
                "Керувати викладачами 👩‍🏫",
                callback_data=Patterns.MANAGE_TEACHERS.with_args(),
            ),
        ],
        [
            InlineKeyboardButton(
                "Повернутися в головне меню 🔙",
                callback_data=Patterns.START.with_args(),
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
                callback_data=Patterns.REMOVE_SUBSCRIPTION_ITEMS.with_args(
                    SubscriptionItemType.GROUP,
                ),
            ),
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                "Додати групу ➕",  # noqa: RUF001
                callback_data=Patterns.ADD_SUBSCRIPTION_ITEM.with_args(
                    SubscriptionItemType.GROUP,
                ),
            ),
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton(
                "Повернутися назад 🔙",
                callback_data=Patterns.MANAGE_SUBSCRIPTION.with_args(),
            ),
        ]
    )

    subscription_text = "Ви не підписані на жодну групу"
    if subscription.groups:
        subscription_text = "Ви підписані на розклад для груп:\n"
        subscription_text += "\n".join([f"- {group.as_string()}" for group in subscription.groups])

    await edit_or_reply(
        update=update,
        text=subscription_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def manage_subscription_teachers(
    update: "Update",
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
                callback_data=Patterns.REMOVE_SUBSCRIPTION_ITEMS.with_args(
                    SubscriptionItemType.TEACHER,
                ),
            ),
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                "Додати викладача ➕",  # noqa: RUF001
                callback_data=Patterns.ADD_SUBSCRIPTION_ITEM.with_args(
                    SubscriptionItemType.TEACHER
                ),
            ),
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton(
                "Повернутися назад 🔙",
                callback_data=Patterns.MANAGE_SUBSCRIPTION.with_args(),
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
    subscription: "Subscription",
    item_type: SubscriptionItemType,
) -> None:
    """
    Shows the list of active items (groups/teachers) in the subscription to remove.
    """
    keyboard = []

    missing_items_translation = {
        SubscriptionItemType.GROUP: "Ви не підписані на жодну групу",
        SubscriptionItemType.TEACHER: "Ви не підписані на жодного викладача",
    }

    items = []
    callback_data = ("error",)
    if item_type == SubscriptionItemType.GROUP:
        items = subscription.groups
        callback_data = Patterns.MANAGE_GROUPS.with_args()
    elif item_type == SubscriptionItemType.TEACHER:
        items = subscription.teachers
        callback_data = Patterns.MANAGE_TEACHERS.with_args()

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
                    callback_data=Patterns.REMOVE_ITEM.with_args(
                        item_type,
                        item.uuid,
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
                    callback_data=Patterns.SELECT_FACULTY.with_args(
                        faculty.uuid,
                        1,  # Page number
                    ),
                ),
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "Повернутися назад 🔙",
                callback_data=Patterns.MANAGE_GROUPS.with_args(),
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
                    callback_data=Patterns.SELECT_DEPARTMENT.with_args(
                        department.uuid,
                        1,  # Page number
                    ),
                ),
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "Повернутися назад 🔙",
                callback_data=Patterns.MANAGE_TEACHERS.with_args(),
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
                    callback_data=Patterns.ADD_SUBSCRIPTION_ITEM.with_args(
                        SubscriptionItemType.GROUP,
                        group.uuid,
                    ),
                ),
            ]
        )

    pagination_row = []

    if groups.meta.has_previous:
        pagination_row.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=Patterns.SELECT_FACULTY.with_args(
                    faculty.uuid,
                    groups.meta.page - 1,
                ),
            ),
        )

    pagination_row.append(
        InlineKeyboardButton(
            f"{groups.meta.page}/{groups.meta.total_pages}",
            callback_data="noop",
        ),
    )

    if groups.meta.has_next:
        pagination_row.append(
            InlineKeyboardButton(
                "➡️",
                callback_data=Patterns.SELECT_FACULTY.with_args(
                    faculty.uuid,
                    groups.meta.page + 1,
                ),
            ),
        )

    keyboard.append(pagination_row)

    keyboard.append(
        [
            InlineKeyboardButton(
                "Повернутися назад 🔙",
                callback_data=Patterns.ADD_SUBSCRIPTION_ITEM.with_args(
                    SubscriptionItemType.GROUP,
                ),
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
                    callback_data=Patterns.ADD_SUBSCRIPTION_ITEM.with_args(
                        SubscriptionItemType.TEACHER,
                        teacher.uuid,
                    ),
                ),
            ]
        )

    pagination_row = []

    if teachers.meta.has_previous:
        pagination_row.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=Patterns.SELECT_DEPARTMENT.with_args(
                    department.uuid,
                    teachers.meta.page - 1,
                ),
            ),
        )

    pagination_row.append(
        InlineKeyboardButton(
            f"{teachers.meta.page}/{teachers.meta.total_pages}",
            callback_data="noop",
        ),
    )

    if teachers.meta.has_next:
        pagination_row.append(
            InlineKeyboardButton(
                "➡️",
                callback_data=Patterns.SELECT_DEPARTMENT.with_args(
                    department.uuid,
                    teachers.meta.page + 1,
                ),
            ),
        )

    keyboard.append(pagination_row)

    keyboard.append(
        [
            InlineKeyboardButton(
                "Повернутися назад 🔙",
                callback_data=Patterns.ADD_SUBSCRIPTION_ITEM.with_args(
                    SubscriptionItemType.TEACHER,
                ),
            ),
        ]
    )

    await edit_or_reply(
        update=update,
        text=f"Оберіть викладача кафедри {department.full_name} для підписки:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def send_pair_details(
    update: "Update",
    pair: "Pair",
    day_schedule: "DaySchedule",
) -> None:
    """Sends detailed information about a lesson."""
    lessons = pair.lessons

    start_time, end_time = utils.get_pair_time_bounds(pair.number)

    text = (
        f"Деталі заняття №{pair.number} ({start_time.strftime('%H:%M')} - "
        f"{end_time.strftime('%H:%M')}) від {utils.get_weekday_name(day_schedule.date)} "
        f"({day_schedule.date.strftime('%d.%m')}):\n\n"
    )

    for lesson in lessons:
        text += f"{lesson.as_string(string_format='full')}\n\n"

    keyboard_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Повернутися до розкладу 📅",
                    callback_data=Patterns.GET_SCHEDULE.with_args(
                        day_schedule.date.isoformat(),
                        day_schedule.for_entity,
                    ),
                )
            ]
        ]
    )

    await edit_or_reply(
        update=update,
        text=text,
        reply_markup=keyboard_markup,
    )


async def send_pair_details_with_bot(
    bot: "Bot",
    chat_id: str | int,
    message_thread_id: int | None,
    pair: "Pair",
    day_schedule: "DaySchedule",
) -> None:
    """Sends detailed information about a lesson."""
    lessons = pair.lessons

    start_time, end_time = utils.get_pair_time_bounds(pair.number)

    text = (
        f"Деталі заняття №{pair.number} ({start_time.strftime('%H:%M')} "
        f"- {end_time.strftime('%H:%M')}) від {utils.get_weekday_name(day_schedule.date)} "
        f"({day_schedule.date.strftime('%d.%m')}):\n\n"
    )

    for lesson in lessons:
        text += f"{lesson.as_string(string_format='full')}\n\n"

    keyboard_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Повернутися до розкладу 📅",
                    callback_data=Patterns.GET_SCHEDULE.with_args(
                        day_schedule.date.isoformat(),
                        day_schedule.for_entity,
                    ),
                )
            ]
        ]
    )

    await bot.send_message(
        chat_id=chat_id,
        message_thread_id=message_thread_id,
        text=text,
        reply_markup=keyboard_markup,
        parse_mode="HTML",
    )


async def send_day_schedule(
    update: "Update",
    day_schedule: "DaySchedule",
) -> None:
    """Gets day schedule from admin service"""
    text = (
        f"Розклад на {utils.get_weekday_name(day_schedule.date)} "
        f"({day_schedule.date.strftime('%d.%m')}) для {day_schedule.for_entity}:\n\n"
    )

    keyboard = []

    for pair in day_schedule.pairs:
        if not pair.lessons:
            continue

        pair_row = []

        for lesson in pair.lessons:
            text += f"{pair.number}. {lesson.as_string(string_format='short')}\n"
            pair_row.append(
                InlineKeyboardButton(
                    text=f"{pair.number}. {lesson.short_name}",
                    callback_data=Patterns.GET_PAIR_DETAILS.with_args(
                        pair.number,
                        day_schedule.date.isoformat(),
                        day_schedule.for_entity,
                    ),
                )
            )

        keyboard.append(pair_row)

    keyboard.append(
        [
            InlineKeyboardButton(
                "Повернутися до розкладу тижня 📅",
                callback_data=Patterns.WEEK_SCHEDULE.with_args(day_schedule.for_entity),
            )
        ]
    )

    await edit_or_reply(
        update=update,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def send_no_classes_message(
    update: "Update",
    date: datetime.date,
) -> None:
    """Sends a message indicating no classes are scheduled for the given date."""
    text = f"Не знайдено жодних занять на {date.strftime('%d.%m.%Y')}."  # noqa: RUF001

    await edit_or_reply(
        update=update,
        text=text,
    )


async def send_schedule_not_found_message(
    update: "Update",
) -> None:
    """Sends a message indicating that the schedule was not found."""
    text = (
        "Упс! Не вдалося знайти розклад. Можливо ви оновили підписку?\n"  # noqa: RUF001
        "Якщо ви вважаєте що це помилка, будь ласка, зв'яжіться з підтримкою."
    )

    await edit_or_reply(
        update=update,
        text=text,
    )


async def entity_not_found_message(
    update: "Update",
    entity: str,
    entity_id: object,
) -> None:
    """Sends a message indicating that the specified entity was not found."""
    text = (
        f"Не вдалося знайти {entity} з ID {entity_id}.\n"  # noqa: RUF001
        "Якщо ви вважаєте що це помилка, будь ласка, зв'яжіться з підтримкою."
    )

    await edit_or_reply(
        update=update,
        text=text,
    )


async def send_week_schedule(
    update: "Update",
    week_schedule: WeekSchedule,
) -> None:
    """
    Sends a message with keyboard buttons to get a specific day's schedule.
    """
    keyboard = []

    def get_button_name(day: "DaySchedule") -> str:
        day_info = f"{utils.get_weekday_name(day.date)} - {day.date.strftime('%d.%m')}"

        pairs_with_lessons = 0
        first_pair_with_lesson = None
        last_pair_with_lesson = None
        for pair in day.pairs:
            if pair.lessons:
                pairs_with_lessons += 1
                if first_pair_with_lesson is None:
                    first_pair_with_lesson = pair.number
                last_pair_with_lesson = pair.number

        if pairs_with_lessons == 0:
            pair_info = "(немає пар)"
        else:
            pair_info = (
                f"({pairs_with_lessons} пар: {first_pair_with_lesson}-{last_pair_with_lesson})"
            )

        return f"{day_info} {pair_info}"

    for day_schedule in week_schedule.days:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=get_button_name(day_schedule),
                    callback_data=Patterns.GET_SCHEDULE.with_args(
                        day_schedule.date,
                        day_schedule.for_entity,
                    ),
                ),
            ]
        )

    await edit_or_reply(
        update=update,
        text=f"Оберіть день тижня, щоб побачити розклад.\nДля {week_schedule.for_entity}",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
