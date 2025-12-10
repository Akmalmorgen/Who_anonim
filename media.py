"""
utils/media.py — безопасная отправка медиа через copy_message
"""

from telegram import Update
from telegram.ext import ContextTypes


async def send_media_copy(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    """
    Отправляет ТЕКСТ ИЛИ МЕДИА как копию сообщения.
    Используется для рассылки и пересылки анонимов.
    """
    msg = update.message

    try:
        # copy_message автоматически копирует ЛЮБОЙ тип контента
        await context.bot.copy_message(
            chat_id=target_id,
            from_chat_id=msg.chat_id,
            message_id=msg.message_id
        )
        return True
    except Exception as e:
        print(f"[MEDIA ERROR] {e}")
        return False