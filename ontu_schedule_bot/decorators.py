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


def reply_with_exception(func: Callable):
    """
    If while processing a call ValueError occurs - tries to reply with text to a message
    """
    async def inner(*args, **kwargs):
        logging.info(
            "Running `%s` with `reply_with_exception` decorator.\n"
            "Args: %s\nKwargs: %s",
            func.__name__,
            args,
            kwargs,
        )

        try:
            value = await func(*args, **kwargs)
            return value
        except (ValueError, RequestException) as exception:
            logging.exception(
                msg=f"Exception in {func}\n{exception}"
            )
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

            text_full = "Виникла помилка:\n"
            text_full += str(exception.args) + "\n"
            text_full += str(
                f"Arguments of `{func.__name__}`:\n"
                f"{(args, kwargs)}"
            )
            texts = split_string(
                string=text_full
            )

            for text in texts:
                send_message_to_telegram(
                    bot_token=update.get_bot().token,
                    chat_id=DEBUG_CHAT_ID,
                    text=text,
                    parse_mode=""
                )
                await asyncio.sleep(0.2)

            short_text = "Виникла помилка.\nПовідомте про це @man_with_a_name."

            if not message:
                return

            await message.reply_text(
                text=short_text,
            )
    return inner
