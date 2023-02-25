"""Contains some handy decorators for bot"""
from telegram import Update


def reply_with_exception(func):
    """
    If while processing a call ValueError occurs - tries to reply with text to a message
    """
    async def inner(update: Update, *args, **kwargs):
        try:
            value = await func(update, *args, **kwargs)
            return value
        except ValueError as exception:
            query = update.callback_query
            message = None
            if update.message:
                message = update.message
            if query and query.message:
                message = query.message

            if not message:
                print(
                    f"Виникла помилка:\n{exception.args}"
                )

            await message.reply_text(
                f"Виникла помилка:\n{exception.args}"
            )
    return inner
