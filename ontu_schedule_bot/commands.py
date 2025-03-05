"""This module contains all the commands bot may execute"""

import logging
import time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.constants import ChatType, ParseMode
from telegram.error import Forbidden
from telegram.ext import ContextTypes

import classes
import decorators
import enums
import utils
from secret_config import DEBUG_CHAT_ID


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

    await telegram_chat.send_chat_action(action="typing")

    chat_entity = None
    try:
        chat_entity = utils.Getter().get_chat(message)
    except ValueError as error:
        logging.warning(error)

    if not chat_entity:
        chat_entity = utils.Setter().new_chat(message)
        if not isinstance(chat_entity, classes.Chat):
            raise ValueError("Could not create chat for whatever reason!")

    subscription = chat_entity.subscription

    show_teacher = all(
        [
            subscription,
            getattr(subscription, "teacher", False),
            "force" not in str(getattr(update.callback_query, "data", "")),
        ]
    )
    if show_teacher:
        await start_for_teachers(update=update, _=context)
        return

    subscription_text = "Ви не підписані на розклад"
    keyboard = []
    if subscription and (subscription.group or subscription.teacher):
        keyboard.append(
            [
                InlineKeyboardButton("Оновити підписку",
                                     callback_data=("set_group",)),
            ]
        )
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=(
                        "Отримувати повідомлення перед парою? "
                        f"{'✅' if subscription.is_active else '❌'}"
                    ),
                    callback_data=("toggle_subscription", chat_entity),
                )
            ]
        )
        if subscription.group:
            subscription_text = (
                "Ви підписані на розклад для групи: "
                f"{subscription.group.name} "
                f"({subscription.group.faculty.name})"
            )
        elif subscription.teacher:
            subscription_text = (
                "Поки що Ви підписані на розклад для "
                f"викладача: {subscription.teacher.short_name}"
            )
    elif not subscription:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "Отримувати розклад студента", callback_data=("set_group",)
                ),
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "Розклад викладачів 🌚", callback_data=("start_for_teachers",)
            ),
        ]
    )

    kwargs = {
        "text": f"Чим можу допомогти?\n\n{subscription_text}",
        "reply_markup": InlineKeyboardMarkup(inline_keyboard=keyboard),
    }

    if base_text is not None:
        kwargs["text"] = base_text + "\n\n" + kwargs["text"]

    if update.callback_query and update.callback_query.message:
        await update.callback_query.message.edit_text(**kwargs)
    elif update.message:
        await update.message.reply_html(**kwargs)


@decorators.reply_with_exception
async def start_for_teachers(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Executed when user initiates conversation, or returns to main menu"""
    telegram_chat = update.effective_chat
    message = update.effective_message
    if not telegram_chat:
        return
    if not message:
        return

    await telegram_chat.send_chat_action(action="typing")

    chat_entity = None
    try:
        chat_entity = utils.Getter().get_chat(message)
    except ValueError as error:
        logging.error(error)
    if not chat_entity:
        chat_entity = utils.Setter().new_chat(message=telegram_chat)
        if not isinstance(chat_entity, classes.Chat):
            raise ValueError("Could not create chat for whatever reason!")

    subscription = chat_entity.subscription

    keyboard = []
    set_teacher_button_text = "Отримувати розклад викладача"
    if subscription and subscription.teacher:
        set_teacher_button_text = "Оновити підписку на розклад викладача"
    keyboard.append(
        [
            InlineKeyboardButton(
                set_teacher_button_text, callback_data=("set_teacher",)
            ),
        ]
    )
    if subscription and (subscription.teacher or subscription.group):
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=(
                        "Отримувати повідомлення перед парою? "
                        f"{'✅' if subscription.is_active else '❌'}"
                    ),
                    callback_data=("toggle_subscription", chat_entity),
                )
            ]
        )
    keyboard.append(
        [
            InlineKeyboardButton(
                "Перейти до розкладу студента 🌝", callback_data=("start", "force")
            ),
        ]
    )

    main_text = "Чим можу допомогти?\n\n"
    if subscription and subscription.teacher:
        main_text += (
            "Ви підписані на розклад для викладача: "
            f"{subscription.teacher.short_name}"
        )
    elif subscription and subscription.group:
        main_text += (
            "Ви підписані на розклад для групи: "
            f"{subscription.group.name} ({subscription.group.faculty.name})\n"
            "Бажаєте отримувати розклад викладача?"
        )
    else:
        main_text += "Ви не підписані на розклад. Бажаєте це змінити?"

    kwargs = {
        "text": main_text,
        "reply_markup": InlineKeyboardMarkup(inline_keyboard=keyboard),
    }

    if update.callback_query and update.callback_query.message:
        await update.callback_query.message.edit_text(**kwargs)
    elif update.message:
        await update.message.reply_html(**kwargs)


@decorators.reply_with_exception
async def department_select(update: Update, _) -> None:
    """This command sends a list of departments you can choose"""
    telegram_chat = update.effective_chat
    if not telegram_chat:
        return

    query = update.callback_query
    if not query or not query.message:
        return

    await query.answer("Будь-ласка, зачекайте")

    departments = utils.Getter().get_list_of_departments()

    keyboard = []
    for index, department in enumerate(departments):
        if index % 4 == 0:
            keyboard.append([])
        keyboard[-1].append(
            InlineKeyboardButton(
                text=department.name,
                callback_data=("pick_department", department),
            )
        )
    keyboard.append(
        [
            InlineKeyboardButton(
                "Назад ⤴️",
                callback_data=("start_for_teachers",),
            )
        ]
    )

    kwargs = {
        "text": "Оберіть кафедру:",
        "reply_markup": InlineKeyboardMarkup(inline_keyboard=keyboard),
    }

    await query.message.edit_text(**kwargs)


@decorators.reply_with_exception
async def teacher_set(update: Update, _) -> None:
    """
    This command activates a subscription (by selecting a teacher of some department)
    """
    telegram_chat = update.effective_chat
    if not telegram_chat:
        return

    query = update.callback_query
    if not query or not query.message:
        return

    await query.answer("Будь-ласка, зачекайте")

    if not query.data:
        return

    data: tuple[str, classes.Department] = tuple(query.data)  # type: ignore

    department_index = 1
    department: classes.Department = data[department_index]

    teachers = utils.Getter().get_teachers_by_department(department=department)

    keyboard = []
    for index, teacher in enumerate(teachers):
        if index % 2 == 0:
            keyboard.append([])
        keyboard[-1].append(
            InlineKeyboardButton(
                text=teacher.short_name,
                callback_data=("pick_teacher", teacher),
            )
        )
    keyboard.append(
        [
            InlineKeyboardButton(
                "Назад ⤴️",
                callback_data=("set_teacher", department),
            )
        ]
    )

    kwargs = {
        "text": "Оберіть викладача:",
        "reply_markup": InlineKeyboardMarkup(inline_keyboard=keyboard),
    }

    await query.message.edit_text(**kwargs)


@decorators.reply_with_exception
async def teacher_select(update: Update, _) -> None:
    """Finalize selection of teacher schedule"""
    telegram_chat = update.effective_chat
    telegram_message = update.effective_message
    query = update.callback_query

    if not telegram_chat or not (telegram_message or query):
        return

    if query:
        await query.answer("Будь-ласка, зачекайте")
        telegram_message = query.message

    if not query.data:
        return

    data: tuple[str, classes.TeacherForSchedule] = tuple(
        query.data)  # type: ignore

    teacher_index = 1
    teacher: classes.TeacherForSchedule = data[teacher_index]

    subscription = utils.Setter().set_chat_teacher(
        message=telegram_message,
        teacher=teacher,
        is_active=True,
    )
    if isinstance(subscription, dict):
        raise ValueError(
            "Instead of subscription - got response from server",
            subscription,
        )
    await start_command(
        update=update,
        context=_,
    )


@decorators.reply_with_exception
async def faculty_select(update: Update, _):
    """This command sends a list of faculties to choose for subscription"""
    query = update.callback_query
    if not query or not query.message:
        return
    await query.answer()

    keyboard = []

    faculties = utils.Getter().get_faculties()
    for faculty in faculties:
        keyboard.append(
            [
                InlineKeyboardButton(
                    faculty.name,
                    callback_data=("pick_faculty", faculty.name),
                )
            ]
        )
    keyboard.append([InlineKeyboardButton(
        "Назад ⤴️", callback_data=("start",))])

    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await query.message.edit_text(
        text="Будь-ласка - оберіть факультет:",
        reply_markup=reply_markup,
    )


def _back_forward_buttons_get(page: int, query_data: list) -> tuple[tuple, tuple]:
    """This method encapsulates logics to get forward and backwards buttons"""
    back_list: list[str | int] = query_data.copy()
    forward_list: list[str | int] = query_data.copy()

    if len(query_data) > enums.PAGE_INDEX:
        back_list[2] = page - 1 if page - 1 >= 0 else 0
        forward_list[2] = page + 1
    else:
        back_list.append(page)
        forward_list.append(page + 1)
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
        faculty_name=data[enums.FACULTY_NAME_INDEX])
    number_of_pages = utils.get_number_of_pages(groups)  # type: ignore
    current_page: list[classes.Group] = utils.get_current_page(
        list_of_elements=groups,  # type: ignore
        page=page,
    )  # type: ignore
    for group in current_page:
        keyboard.append(
            [
                InlineKeyboardButton(
                    group.name,
                    callback_data=("pick_group", group),
                )
            ]
        )

    back_tuple, forward_tuple = _back_forward_buttons_get(
        page=page,
        query_data=list(data),
    )

    keyboard.append(
        [
            InlineKeyboardButton("◀️", callback_data=back_tuple),
            InlineKeyboardButton("Назад ⤴️", callback_data=("set_group",)),
            InlineKeyboardButton("▶️", callback_data=forward_tuple),
        ]
    )

    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await query.message.edit_text(
        text=f"Тепер - оберіть групу\nСторінка {page+1}/{number_of_pages}",
        reply_markup=reply_markup,
    )


@decorators.reply_with_exception
async def group_set(update: Update, _) -> None:
    """This command activates a subscription"""
    telegram_chat = update.effective_chat
    telegram_message = update.effective_message
    query = update.callback_query

    if not telegram_chat or not (telegram_message or query):
        return

    if query:
        await query.answer()
        telegram_message = query.message

    if not query.data:
        return

    data: tuple[str, classes.Group] = tuple(query.data)  # type: ignore
    group_index = 1
    group: classes.Group = data[group_index]
    subscription = utils.Setter().set_chat_group(
        message=telegram_message,
        group=group,
        is_active=update.effective_chat.type != ChatType.PRIVATE,
    )
    if isinstance(subscription, dict):
        raise ValueError(
            "Instead of subscription - got response from server", subscription
        )

    if not subscription.group:
        raise ValueError("Subscription has no group!")

    await start_command(
        update=update,
        context=_,
        base_text=(
            "Відтепер ви будете отримувати розклад для групи: "
            f"{subscription.group.name} факультету {subscription.group.faculty.name}"
        ),
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
async def update_cache(update: Update, _):
    """This method updates cache for current chat"""
    query = update.callback_query
    if not query or not query.message:
        return
    message = query.message
    await query.answer(text="Будь-ласка, зачекайте")

    if not query.data:
        return

    data: tuple[str, classes.Group, Message] = tuple(
        query.data)  # type: ignore
    group_index = 1

    group: classes.Group = data[group_index]

    cache_reset = utils.Getter().reset_cache(group=group)
    if not cache_reset:
        await message.edit_text(
            text="Розклад, кеш не вдалося оновити. Спробуйте пізніше (чи /schedule)",
        )
        return

    schedule = utils.Getter().get_students_schedule(group=group)

    week_schedule = schedule.get_week_representation()

    await send_week_schedule(
        message=message,
        week_schedule=week_schedule,
        group=group,
        is_updated=True,
    )


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

    callback_data: tuple[str, classes.Pair, classes.Day] = tuple(
        query.data)  # type: ignore

    pair = callback_data[1]
    day = callback_data[2]

    keyboard = [
        [InlineKeyboardButton(
            text="Назад ⤴️", callback_data=("day_details", day))]
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
    if update.effective_chat.id != DEBUG_CHAT_ID:
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
                    chat_id=DEBUG_CHAT_ID,
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
        chat_id=DEBUG_CHAT_ID,
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
        raise ValueError(
            "В вас ще немає підписки! Здається ви мені бота зламали...")

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
async def update_notbot(update: Update, _) -> None:
    """
    A method to update notbot with hope to reduce waiting time on average
    Args:
        _ (ContextTypes.DEFAULT_TYPE): Context, that's passed when calling for task
    """
    if not update.effective_chat:
        return
    if update.effective_chat.id != DEBUG_CHAT_ID:
        return

    logging.info("Updating notbot")
    utils.Getter().update_notbot()
    logging.info("Finished updating notbot")
    if update.message:
        await update.message.reply_text("Notbot was reset")


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

    if message.chat.id != DEBUG_CHAT_ID:
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
        f"Повідомлення надіслано всім отримувачам за {round(end-start, 2)} секунд"
    )
