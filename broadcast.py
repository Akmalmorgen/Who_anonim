"""
handlers/broadcast.py — рассылка сообщений администратора.

✓ Работает с любыми медиа
✓ copy_message сохраняет формат
✓ Несколько админов
"""

from telegram import Update
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    filters,
)

from config.settings import ADMINS
from states import UserStates
from db.users import (
    set_user_state,
    get_all_users,
    is_banned
)
from keyboards.keyboards import kb


# ---------------------------------------------------------
# Вход в режим рассылки
# ---------------------------------------------------------
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ADMINS:
        return await update.message.reply_text("❌ У вас нет доступа.")

    set_user_state(user_id, UserStates.ADMIN_BROADCAST)

    await update.message.reply_text(
        "📢 <b>Режим рассылки</b>\n\n"
        "Отправьте сообщение, фото, видео, документ или любой файл.\n"
        "Все, что вы отправите — уйдёт всем пользователям.",
        parse_mode="HTML",
        reply_markup=kb.reply.back_only()
    )


# ---------------------------------------------------------
# Выполнение рассылки (принимает ЛЮБОЙ контент)
# ---------------------------------------------------------
async def broadcast_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id

    if admin_id not in ADMINS:
        return

    # Получаем объект сообщения
    msg = update.message

    # Список всех пользователей
    users = get_all_users()

    sent = 0

    for uid in users:
        if is_banned(uid):
            continue

        try:
            # copy_message сохраняет весь формат, качество, caption и т.д.
            await context.bot.copy_message(
                chat_id=uid,
                from_chat_id=msg.chat_id,
                message_id=msg.message_id
            )
            sent += 1
        except:
            pass

    await msg.reply_text(
        f"📢 Рассылка завершена!\n"
        f"✔ Успешно: <b>{sent}</b> пользователям.",
        parse_mode="HTML",
        reply_markup=kb.reply.admin_menu()
    )

    set_user_state(admin_id, UserStates.ADMIN_PANEL)


# ---------------------------------------------------------
# РЕГИСТРАЦИЯ
# ---------------------------------------------------------
def register_broadcast_handlers(app):

    # вход в рассылку
    app.add_handler(MessageHandler(filters.Regex("^📢 Рассылка$"), broadcast_start))

    # контент (ТЕКСТ И ЛЮБОЕ МЕДИА)
    app.add_handler(MessageHandler(
        filters.ChatType.PRIVATE &
        (
            filters.TEXT |
            filters.PHOTO |
            filters.VIDEO |
            filters.DOCUMENT |
            filters.AUDIO |
            filters.VOICE |
            filters.ANIMATION |
            filters.STICKER
        ),
        broadcast_execute
    ))