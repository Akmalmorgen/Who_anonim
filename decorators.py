"""
utils/decorators.py — полезные декораторы
"""

from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

from config.settings import ADMINS
from db.users import is_banned


def admin_only(func):
    """ Декоратор — доступ только для админов """

    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id

        if user_id not in ADMINS:
            await update.message.reply_text("❌ У вас нет доступа.")
            return

        return await func(update, context, *args, **kwargs)

    return wrapper


def not_banned(func):
    """ Запрещает выполнение функции забаненному человеку """

    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id

        if is_banned(user_id):
            await update.message.reply_text("🚫 Вы заблокированы.")
            return

        return await func(update, context, *args, **kwargs)

    return wrapper