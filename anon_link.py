"""
handlers/anon_link.py — логика работы с анонимной ссылкой:
• показать мою ссылку
• создать новую
• сменить ссылку (с кнопкой «Отмена»!)
• вывод управления ссылкой
"""

from telegram import Update
from telegram.ext import ContextTypes

from states import UserStates
from keyboards.keyboards import kb

from db.links import (
    get_or_create_user_link,
    regenerate_link,
    count_active_anon_sessions
)

from db.users import set_user_state


# -----------------------------------------------------------
# ПОКАЗАТЬ МОЮ АНОНИМНУЮ ССЫЛКУ
# -----------------------------------------------------------
async def send_my_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    # получить или создать ссылку
    link_id = get_or_create_user_link(user_id)
    url = f"https://t.me/{context.bot.username}?start={link_id}"

    # количество людей, кто пишет владельцу
    active_count = count_active_anon_sessions(user_id)

    text = (
        "🔗 <b>Ваша анонимная ссылка</b>\n\n"
        f"🌐 <code>{url}</code>\n"
        f"🆔 ID: <code>{link_id}</code>\n\n"
        f"👥 Активных диалогов: <b>{active_count}</b>\n\n"
        "Вы можете изменить ссылку ниже:"
    )

    set_user_state(user_id, UserStates.MY_LINK)

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=kb.reply.my_link_menu()
    )


# -----------------------------------------------------------
# НАЧАТЬ СМЕНУ ССЫЛКИ
# -----------------------------------------------------------
async def start_change_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    set_user_state(user_id, UserStates.CHANGING_LINK)

    await update.message.reply_text(
        "🔄 <b>Вы уверены, что хотите сменить ссылку?</b>\n\n"
        "Старая перестанет работать!\n\n"
        "Нажмите «Сменить ссылку» или «Отмена».",
        parse_mode="HTML",
        reply_markup=kb.reply.change_link_confirm()
    )


# -----------------------------------------------------------
# ПОДТВЕРДИТЬ СМЕНУ ССЫЛКИ
# -----------------------------------------------------------
async def confirm_change_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    new_link = regenerate_link(user_id)
    url = f"https://t.me/{context.bot.username}?start={new_link}"

    text = (
        "✅ <b>Ссылка успешно изменена!</b>\n\n"
        f"Новая ссылка:\n<code>{url}</code>\n\n"
        "Старая теперь недействительна."
    )

    set_user_state(user_id, UserStates.MY_LINK)

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=kb.reply.my_link_menu()
    )


# -----------------------------------------------------------
# ОТМЕНА СМЕНЫ ССЫЛКИ
# -----------------------------------------------------------
async def cancel_change_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат обратно в меню моей ссылки."""
    await send_my_link(update, context)


# -----------------------------------------------------------
# РЕГИСТРАЦИЯ ХЕНДЛЕРОВ
# -----------------------------------------------------------
def register_anon_link_handlers(app):

    from telegram.ext import MessageHandler, filters

    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^🔗 Моя анон-ссылка$"),
        send_my_link
    ))

    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^🔄 Сменить ссылку$"),
        start_change_link
    ))

    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^Сменить ссылку$"),
        confirm_change_link
    ))

    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^Отмена$"),
        cancel_change_link
    ))