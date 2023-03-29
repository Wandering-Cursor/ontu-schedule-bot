"""Contains some handy decorators for bot"""
import asyncio
import logging

from telegram import Update

from requests.exceptions import RequestException

from utils import split_string
from secret_config import DEBUG_CHAT_ID


def _print(exception: Exception):
    """Print exception for methods"""
    print(f"Виникла помилка:\n{exception.args}")


def reply_with_exception(func):
    """
    If while processing a call ValueError occurs - tries to reply with text to a message
    """
    async def inner(*args, **kwargs):
        try:
            value = await func(*args, **kwargs)
            return value
        except (ValueError, RequestException) as exception:
            logging.error(
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

            if not message:
                return _print(exception)

            short_text = "Виникла помилка.\nПовідомте про це @man_with_a_name."

            bot_msg = await message.reply_text(
                text=short_text,
            )

            text_full = "Виникла помилка:\n"
            text_full += str(exception.args)
            texts = split_string(
                string=text_full
            )

            for text in texts:
                await bot_msg.get_bot().send_message(
                    chat_id=DEBUG_CHAT_ID,
                    text=text,
                )
                await asyncio.sleep(0.2)
    return inner
