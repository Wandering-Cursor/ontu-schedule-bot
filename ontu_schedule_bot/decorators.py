"""Contains some handy decorators for bot"""
import asyncio
import logging
from typing import Callable

from requests.exceptions import RequestException
from secret_config import DEBUG_CHAT_ID
from telegram import Update
from utils import send_message_to_telegram, split_string


def _print(exception: Exception) -> str:
    """
    Print exception for methods.
    Also - returns str
    """
    text = f"Виникла помилка:\n{exception.args}"
    print(text)
    return text


async def send_exception(
    update: Update | None,
    exception: Exception,
    *args,
    func: Callable | None = None,
    bot_token: str | None = None,
    **kwargs,
):
    """
    Sends exception to DEBUG_CHAT_ID, can be used in any function.
    """
    text_full = "Виникла помилка:\n"
    text_full += str(exception.args) + "\n"
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

    if update:
        bot_token = update.get_bot().token

    for text in texts:
        send_message_to_telegram(
            bot_token=bot_token,
            chat_id=DEBUG_CHAT_ID,
            text=text,
            parse_mode="",
        )
        await asyncio.sleep(0.2)


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
            update = kwargs.pop("update", None)
            for arg in args:
                if isinstance(arg, Update):
                    update = arg

            if not update or not isinstance(update, Update):
                return _print(exception)

            query = update.callback_query
            message = None

            if update.message:
                message = update.message
            if query and query.message:
                message = query.message

            await send_exception(
                update,
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
