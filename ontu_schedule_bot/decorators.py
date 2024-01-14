"""Contains some handy decorators for bot"""
import logging
import traceback
from typing import Callable

from requests.exceptions import RequestException
from secret_config import DEBUG_CHAT_ID
from telegram import Bot, Update
from telegram.ext import ContextTypes
from utils import split_string


def _print(exception: Exception) -> str:
    """
    Print exception for methods.
    Also - returns str
    """
    text = f"Виникла помилка:\n{exception.args}"
    print(text)
    return text


async def send_exception(
    bot: Bot | None,
    exception: Exception,
    *args,
    func: Callable | None = None,
    **kwargs,
):
    """
    Sends exception to DEBUG_CHAT_ID, can be used in any function.
    """
    text_full = "Виникла помилка:\nArgs:"
    text_full += str(exception.args) + "\nTraceback:\n"
    text_full += str(traceback.format_exc())
    if func:
        text_full += str(f"Arguments of `{func.__name__}`:")

    pretty_args = [
        {"original": arg, "dict": getattr(arg, "__dict__", None)} for arg in args
    ]
    pretty_kwargs = [
        {"key": key, "value": item, "dict": getattr(item, "__dict__", None)}
        for key, item in kwargs.items()
    ]
    text_full += str(f"\n{pretty_args=};{pretty_kwargs=}")

    texts = split_string(string=text_full)

    for text in texts:
        await bot.send_message(
            chat_id=DEBUG_CHAT_ID,
            text=text,
            parse_mode="",
        )


def reply_with_exception(func: Callable):
    """
    If while processing a call ValueError occurs - tries to reply with text to a message
    """

    async def inner(*args, **kwargs):
        pretty_args = [
            {"original": arg, "str": str(arg), "dict": getattr(arg, "__dict__", None)}
            for arg in args
        ]
        pretty_kwargs = [
            {
                "key": key,
                "value": item,
                "str": str(item),
                "dict": getattr(item, "__dict__", None),
            }
            for key, item in kwargs.items()
        ]
        logging.info(
            "Running `%s` with `reply_with_exception` decorator.\n"
            "Args: %s\nKwargs: %s",
            func.__name__,
            pretty_args,
            pretty_kwargs,
        )

        try:
            value = await func(*args, **kwargs)
            return value
        except (ValueError, RequestException) as exception:
            logging.exception(msg=f"Exception in {func}\n{exception}")
            context = kwargs.pop("context", None)
            update = kwargs.pop("update", None)
            for arg in args:
                if isinstance(arg, Update):
                    update = arg
                if isinstance(arg, ContextTypes):
                    context = arg

            if not isinstance(update, Update) and not isinstance(context, ContextTypes):
                return _print(exception)

            query = update.callback_query
            message = None

            if update.message:
                message = update.message
            if query and query.message:
                message = query.message

            bot = None
            if update:
                bot = update.get_bot()
            if context:
                bot = context.bot  # type: ignore

            await send_exception(
                bot,
                exception,
                func,
                *args,
                **kwargs,
            )

            short_text = "Виникла помилка.\nПовідомте про це @man_with_a_name."

            if not message:
                return

            await message.reply_text(
                text=short_text,
            )

    return inner
